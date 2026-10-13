import csv
import json
import os
import warnings
from pathlib import Path

FIELDS = """experiment_id run_id repetition timestamp config_hash code_hash n solver encoding sat_solver column_alo threads seed seed_applied solver_version python_version status native_status native_stop_cause termination_reason solution_valid time_limit_s memory_limit_mib max_clauses batch_size timeout_scope sample_interval_ms memory_scope total_s startup_s setup_s build_s load_s solve_s native_solve_s decode_validate_s cleanup_s phase phase_timings_complete peak_rss_mib memory_samples memory_access_errors primary_vars aux_vars cnf_clauses cnf_literals count_source clauses_generated clauses_loaded native_vars native_constraints error_type error_message worker_exitcode cleanup_warning solver_stats solution_cols""".split()
_WANDB = None


def read_results(path, repair=False):
    path = Path(path)
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    records = []
    for i, line in enumerate(lines):
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            if not repair or i != len(lines) - 1:
                raise ValueError(f"Invalid JSONL record at line {i + 1}: {path}")
            # Only an incomplete last line is recoverable. Preserve its bytes.
            import shutil
            shutil.copy2(path, path.with_suffix(".jsonl.incomplete-backup"))
            path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
                            encoding="utf-8")
            warnings.warn("Recovered an incomplete final JSONL record; backup retained.")
    return records


def csv_row(record):
    return {key: json.dumps(record[key], ensure_ascii=False) if isinstance(record.get(key), (dict, list))
            else record.get(key) for key in FIELDS}


class ResultLogger:
    def __init__(self, output_dir, resume=False):
        self.directory = Path(output_dir)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.jsonl = self.directory / "results.jsonl"
        self.csv = self.directory / "experiment_results.csv"
        existing = read_results(self.jsonl, repair=resume)
        if existing and not resume:
            raise FileExistsError("Results already exist; use --resume or choose a new output directory")
        # JSONL is authoritative. Rebuild CSV to recover a crash between the two writes.
        with self.csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(csv_row(row) for row in existing)
        self.records = existing

    def log(self, data):
        with self.jsonl.open("a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False, allow_nan=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        with self.csv.open("a", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writerow(csv_row(data))
            f.flush()
            os.fsync(f.fileno())
        self.records.append(data)
        if _WANDB is not None:
            try:
                _WANDB.log({k: v for k, v in data.items() if isinstance(v, (int, float, str, bool))})
            except Exception as exc:
                warnings.warn(f"W&B log failed; local data is saved: {exc}")


def init_wandb(project_name="NQueens-Optimization", run_name=None, *, enabled=False, output_dir="."):
    global _WANDB
    if enabled:
        try:
            import wandb
            _WANDB = wandb.init(project=project_name, name=run_name, mode="offline", dir=str(output_dir))
        except Exception as exc:
            warnings.warn(f"W&B disabled: {exc}")
    return _WANDB


def finish_wandb():
    global _WANDB
    if _WANDB is not None:
        try:
            _WANDB.finish()
        except Exception as exc:
            warnings.warn(f"W&B finish failed: {exc}")
        finally:
            _WANDB = None


def log_result(data, logger):
    """Use one ResultLogger per experiment; no implicit append to an old-schema CSV."""
    logger.log(data)
