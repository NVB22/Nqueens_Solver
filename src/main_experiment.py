import argparse
import hashlib
import json
import math
import multiprocessing
import platform
import random
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from src.encodings import ENCODINGS
from src.encodings.base_encoder import estimate_cnf
from src.solvers.common import package_version
from src.utils.experiment_runner import SOLVERS, run_job
from src.utils.wandb_logger import ResultLogger, init_wandb, finish_wandb
from src.utils.summary import write_summary

# main_experiment.py nằm trong src; thư mục dự án là cấp cha của src.
ROOT = Path(__file__).resolve().parents[1]
LARGE_SIZES = [4, 8, 9, 16, 25, 27, 36, 49, 64, 81, 100, 125, 216, 343, 512, 729, 1000, 1331]


def positive_int(value):
    result = int(value)
    if result < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return result


def positive_float(value): 
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise argparse.ArgumentTypeError("must be finite and positive")
    return result


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sizes", nargs="+", type=positive_int)
    p.add_argument("--large", action="store_true", help="Use the reference sizes up to 1331")
    p.add_argument("--solvers", nargs="+", choices=SOLVERS, default=list(SOLVERS))
    p.add_argument("--encodings", nargs="+", choices=ENCODINGS, default=list(ENCODINGS))
    p.add_argument("--sat-solver", default="glucose3")
    p.add_argument("--num-runs", type=positive_int, default=3)
    p.add_argument("--timeout", type=positive_float, default=100.0)
    p.add_argument("--memory-mib", type=positive_float, default=6144.0)
    p.add_argument("--threads", type=positive_int, default=1)
    p.add_argument("--seed", type=int, default=0, help="Native solver seed; Glucose seed is not overridden")
    p.add_argument("--order-seed", type=int, default=2026)
    p.add_argument("--column-alo", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--batch-size", type=positive_int, default=8192)
    p.add_argument("--sample-ms", type=positive_float, default=20.0)
    # Mặc định không chặn theo kích thước CNF. Timeout/RAM vẫn được giám sát.
    p.add_argument("--max-clauses", type=int, default=0,
                   help="Optional preflight cap; default 0 means no clause limit")
    p.add_argument("--cpoptimizer", help="Full path to cpoptimizer.exe, or set CPO_EXECUTABLE")
    p.add_argument("--output", type=Path)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="Print the plan/counts without running solvers")
    p.add_argument("--wandb-offline", action="store_true")
    a = p.parse_args(argv)
    if not 0 <= a.seed <= 2_147_483_647 or a.max_clauses < 0:
        p.error("seed must be in [0,2147483647]; max-clauses must be nonnegative")
    if a.resume and not a.output:
        p.error("--resume requires --output")
    if a.sizes and a.large:
        p.error("Choose --sizes or --large")
    a.sizes = sorted(set(a.sizes or (LARGE_SIZES if a.large else [2, 4, 8, 16, 32, 64])))
    a.solvers = list(dict.fromkeys(a.solvers))
    a.encodings = list(dict.fromkeys(a.encodings))
    return a


def source_hash():
    digest = hashlib.sha256()
    # File chạy chính đã nằm trong src nên được băm đúng một lần.
    for path in sorted((ROOT / "src").rglob("*.py")):
        digest.update(str(path.relative_to(ROOT)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def environment():
    import psutil
    packages = {name: package_version(name) for name in
                ["python-sat", "psutil", "ortools", "docplex", "cplex", "gurobipy"]}
    return {"python": platform.python_version(), "executable": sys.executable,
            "os": platform.platform(), "processor": platform.processor(),
            "logical_cpus": psutil.cpu_count(), "physical_cpus": psutil.cpu_count(logical=False),
            "ram_mib": psutil.virtual_memory().total / 1024 ** 2, "packages": packages}


def main(argv=None):
    args = parse_args(argv)
    config = {k: v for k, v in vars(args).items()
              if k not in {"output", "resume", "dry_run", "wandb_offline"}}
    code_hash = source_hash()
    jobs = []
    for solver in args.solvers:
        for encoding in (args.encodings if solver == "sat" else [None]):
            for n in args.sizes:
                for repetition in range(1, args.num_runs + 1):
                    jobs.append((solver, encoding, n, repetition))
    random.Random(args.order_seed).shuffle(jobs)
    if args.dry_run:
        print(f"{len(jobs)} jobs; timeout={args.timeout}s; RAM={args.memory_mib} MiB; column_alo={args.column_alo}")
        for n in args.sizes:
            for encoding in args.encodings if "sat" in args.solvers else []:
                counts = estimate_cnf(n, encoding, args.column_alo)
                skip = args.max_clauses and counts["cnf_clauses"] > args.max_clauses
                print(f"N={n:<5} {encoding:<11} vars={counts['primary_vars'] + counts['aux_vars']:,} "
                      f"clauses={counts['cnf_clauses']:,} {'SKIP: clause cap' if skip else ''}")
        return 0
    env = environment()
    fingerprint = {"config": config, "code_hash": code_hash, "python": env["python"],
                   "packages": env["packages"], "os": env["os"]}
    config_hash = hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest()
    new_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    output = (args.output or ROOT / "results" / new_id).resolve()
    manifest_path = output / "manifest.json"
    if args.resume:
        if not manifest_path.exists():
            raise ValueError("Cannot resume: manifest.json does not exist")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["config_hash"] != config_hash:
            raise ValueError("Resume refused: code, options, OS or package versions changed. Use a new output directory.")
    else:
        if output.exists() and any(output.iterdir()):
            raise FileExistsError("Output directory is not empty; use --resume or a new directory")
        output.mkdir(parents=True, exist_ok=True)
        manifest = {"schema_version": 1, "experiment_id": new_id, "config_hash": config_hash,
                    "code_hash": code_hash, "config": config, "environment": env,
                    "encoding_definitions": {
                        "Binomial": "pairwise_original",
                        "Binary": "binary_original",
                        "Commander": "recursive_groups_3_pairwise_base_3_reverse_links",
                        "Product": "recursive_coordinates_pairwise_base_4",
                        "Sequential": "sinz_pairwise_base_3"},
                    "created_utc": datetime.now(timezone.utc).isoformat(),
                    "time_definition": "spawn to validated worker result; excludes logging and cleanup",
                    "memory_definition": "sampled sum of RSS of worker and descendants; shared pages may be counted twice",
                    "native_solve_definition": "adapter solve call, may include model export/presolve"}
        with manifest_path.open("x", encoding="utf-8") as handle:
            json.dump(manifest, handle, ensure_ascii=False, indent=2)
    # File lock is released by the OS after a crash, on both Windows and POSIX.
    from src.utils.run_lock import run_lock
    with run_lock(output / "run.lock"):
        logger = ResultLogger(output, resume=args.resume)
        finished = {r["run_id"] for r in logger.records if r["status"] != "INTERRUPTED"}
        init_wandb(run_name=manifest["experiment_id"], enabled=args.wandb_offline, output_dir=output)
        try:
            for index, (solver, encoding, n, repetition) in enumerate(jobs, 1):
                key = f"{config_hash}|{solver}|{encoding}|{n}|{repetition}"
                run_id = hashlib.sha256(key.encode()).hexdigest()[:24]
                if run_id in finished:
                    continue
                print(f"[{index}/{len(jobs)}] {solver} {encoding or 'Native_Model'} N={n} run={repetition}", flush=True)
                row = run_job(n=n, solver=solver, encoding=encoding, sat_solver=args.sat_solver,
                              timeout=args.timeout, memory_limit_mib=args.memory_mib,
                              threads=args.threads, seed=args.seed, column_alo=args.column_alo,
                              batch_size=args.batch_size, sample_interval_ms=args.sample_ms,
                              max_clauses=args.max_clauses, cpoptimizer=args.cpoptimizer)
                row.update(experiment_id=manifest["experiment_id"], run_id=run_id,
                           repetition=repetition, timestamp=datetime.now(timezone.utc).isoformat(),
                           config_hash=config_hash, code_hash=code_hash)
                logger.log(row)
                total = row.get("total_s")
                print(f"  {row['status']} total={total:.4f}s peak={row.get('peak_rss_mib')} MiB" if total is not None
                      else f"  {row['status']}: {row.get('error_message', '')}", flush=True)
                if row["status"] == "ERROR":
                    print("  " + row.get("error_message", "Unknown error"), flush=True)
        except KeyboardInterrupt:
            print("\nInterrupted. Completed jobs are saved; repeat the command with --resume.")
            return 130
        finally:
            finish_wandb()
            write_summary(logger.records, output / "summary.csv")
    print(f"Saved results to: {output}")
    return 0


if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
