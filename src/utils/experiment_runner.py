import math
import multiprocessing as mp
import os
import platform
import time
import traceback
from src.encodings.base_encoder import validate_n, estimate_cnf
from src.solvers.common import Measurements, BudgetExpired

SOLVERS = ("sat", "cp_sat", "cplex_cp", "gurobi", "cplex_mip")


def _worker(job, sender, deadline, parent_start):
    if os.name == "posix":
        os.setsid()
    m = Measurements(deadline, sender.send)
    m.data["startup_s"] = time.perf_counter() - parent_start
    try:
        if job["solver"] == "sat":
            from src.solvers.sat_solvers import _solve_sat
            answer = _solve_sat(job, m)
        elif job["solver"] in ("cp_sat", "cplex_cp"):
            from src.solvers.cp_solvers import _solve_cp_sat, _solve_cp_cplex
            answer = (_solve_cp_sat if job["solver"] == "cp_sat" else _solve_cp_cplex)(job, m)
        else:
            from src.solvers.ilp_solvers import _solve_gurobi, _solve_cplex_mip
            answer = (_solve_gurobi if job["solver"] == "gurobi" else _solve_cplex_mip)(job, m)
        m.data["phase_timings_complete"] = True
    except BudgetExpired as exc:
        answer = {"status": "TIMEOUT", "termination_reason": "WALL_TIME_LIMIT",
                  "error_type": type(exc).__name__, "error_message": str(exc)}
    except MemoryError as exc:
        answer = {"status": "MEM_LIMIT", "termination_reason": "ALLOCATION_FAILED",
                  "error_type": type(exc).__name__, "error_message": str(exc)}
    except Exception as exc:
        answer = {"status": "ERROR", "termination_reason": "EXCEPTION",
                  "error_type": type(exc).__name__, "error_message": str(exc),
                  "traceback": traceback.format_exc()}
    try:
        sender.send({"type": "result", "data": {**m.data, **answer},
                     "finished_at": time.perf_counter()})
    finally:
        sender.close()


def run_job(n, solver="sat", encoding="Binary", sat_solver="glucose3",
            timeout=100.0, memory_limit_mib=6144.0, threads=1, seed=0,
            column_alo=True, batch_size=8192, sample_interval_ms=20.0,
            max_clauses=0, cpoptimizer=None):
    validate_n(n)
    if solver not in SOLVERS:
        raise ValueError(f"Unknown solver: {solver}")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be finite and positive")
    if not math.isfinite(memory_limit_mib) or memory_limit_mib <= 0:
        raise ValueError("memory_limit_mib must be finite and positive")
    if threads < 1 or batch_size < 1 or max_clauses < 0:
        raise ValueError("Invalid thread count, batch size or clause limit")
    if not math.isfinite(sample_interval_ms) or sample_interval_ms <= 0:
        raise ValueError("Sampling interval must be finite and positive")
    if not 0 <= seed <= 2_147_483_647:
        raise ValueError("seed must be in [0, 2147483647]")
    job = dict(n=n, solver=solver, encoding=encoding if solver == "sat" else None,
               sat_solver=sat_solver, timeout=float(timeout), memory_limit_mib=float(memory_limit_mib),
               threads=1 if solver == "sat" else threads, seed=seed, column_alo=bool(column_alo),
               batch_size=batch_size, sample_interval_ms=sample_interval_ms,
               max_clauses=max_clauses, cpoptimizer=cpoptimizer)
    result = dict(n=n, solver=solver, encoding=job["encoding"],
                  sat_solver=sat_solver if solver == "sat" else None,
                  column_alo=bool(column_alo) if solver == "sat" else None,
                  threads=job["threads"], seed=seed if solver != "sat" else None,
                  seed_applied=None, time_limit_s=timeout, memory_limit_mib=memory_limit_mib,
                  max_clauses=max_clauses, batch_size=batch_size if solver == "sat" else None,
                  sample_interval_ms=sample_interval_ms, timeout_scope="spawn_to_validated_result",
                  memory_scope="sampled_sum_worker_and_descendants_rss",
                  status="ERROR", termination_reason="WORKER_DIED", phase="startup",
                  solution_valid=None, solution_cols=None, python_version=platform.python_version(),
                  peak_rss_mib=None, phase_timings_complete=False)
    if solver == "sat":
        result.update(estimate_cnf(n, encoding, column_alo))
        if max_clauses and result["cnf_clauses"] > max_clauses:
            result.update(status="SKIPPED", termination_reason="CLAUSE_LIMIT",
                          error_message=f"CNF has {result['cnf_clauses']} clauses; limit={max_clauses}",
                          total_s=None, phase="preflight")
            return result
    from src.utils.resource_monitor import ProcessTreeMonitor
    ctx = mp.get_context("spawn")
    receiver, sender = ctx.Pipe(duplex=False)
    start = time.perf_counter()
    deadline = start + timeout
    process = ctx.Process(target=_worker, args=(job, sender, deadline, start))
    monitor = None
    got_result = False
    try:
        process.start()
        sender.close()
        try:
            monitor = ProcessTreeMonitor(process.pid)
        except Exception as exc:
            # Do not silently claim RAM=0 when the OS denies process inspection.
            result.update(status="ERROR", termination_reason="MONITOR_UNAVAILABLE",
                          error_type=type(exc).__name__, error_message=str(exc),
                          total_s=time.perf_counter() - start)
            return result
        while True:
            monitor.sample()
            if monitor.peak_mib > memory_limit_mib:
                result.update(status="MEM_LIMIT", termination_reason="RSS_LIMIT",
                              phase_timings_complete=False)
                break
            pipe_closed = False
            while receiver.poll():
                try:
                    event = receiver.recv()
                except EOFError:
                    pipe_closed = True
                    break
                result.update(event["data"])
                if event["type"] == "result":
                    got_result = True
                    if event["finished_at"] > deadline:
                        result.update(status="TIMEOUT", termination_reason="WALL_TIME_LIMIT",
                                      solution_valid=None, solution_cols=None,
                                      phase_timings_complete=False)
                    break
            if got_result:
                break
            if time.perf_counter() >= deadline:
                result.update(status="TIMEOUT", termination_reason="WALL_TIME_LIMIT",
                              phase_timings_complete=False)
                break
            if pipe_closed:
                break
            if not process.is_alive() and not receiver.poll():
                break
            receiver.poll(min(sample_interval_ms / 1000, max(0, deadline - time.perf_counter())))
        result["total_s"] = time.perf_counter() - start
    finally:
        cleanup_start = time.perf_counter()
        if got_result:
            process.join(timeout=0.2)
        if monitor is not None:
            result.update(peak_rss_mib=monitor.peak_mib, memory_samples=monitor.samples,
                          memory_access_errors=monitor.access_errors)
            survivors = monitor.stop()
            if survivors:
                result["cleanup_warning"] = f"Processes still alive after cleanup: {survivors}"
        if process.pid is not None:
            if monitor is None and process.is_alive():
                process.terminate()
            process.join(timeout=1)
            if process.is_alive():
                process.kill()
                process.join(timeout=1)
            result["worker_exitcode"] = process.exitcode
            if not process.is_alive():
                process.close()
            else:
                result["cleanup_warning"] = "Worker still alive after kill; inspect it before continuing"
        receiver.close()
        sender.close()
        result["cleanup_s"] = time.perf_counter() - cleanup_start
    if not got_result and result["termination_reason"] == "WORKER_DIED":
        result.update(error_type="WorkerExited",
                      error_message=f"Worker exited without a result: {result.get('worker_exitcode')}")
    return result
