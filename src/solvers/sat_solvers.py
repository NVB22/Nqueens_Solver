from itertools import islice
from src.solvers.common import package_version
from src.utils.validation import sat_to_columns


def run_sat(n: int, solver_name="glucose3", timeout=100, *, encoding="Binary",
            column_alo=True, **options):
    from src.utils.experiment_runner import run_job
    return run_job(n=n, solver="sat", encoding=encoding, sat_solver=solver_name,
                   timeout=timeout, column_alo=column_alo, **options)


def _solve_sat(job, m):
    with m.phase("setup_s"):
        from pysat.solvers import Solver
        from src.encodings import ENCODINGS
        solver = Solver(name=job["sat_solver"])
        m.data.update(solver_version="python-sat " + str(package_version("python-sat")),
                      seed_applied=None, clauses_generated=0, clauses_loaded=0, load_s=0.0)
        generator = ENCODINGS[job["encoding"]](job["n"], job["column_alo"])
    try:
        while True:
            with m.phase("build_s"):
                chunk = list(islice(generator, job["batch_size"]))
                m.data["clauses_generated"] += len(chunk)
            if not chunk:
                break
            with m.phase("load_s"):
                solver.append_formula(chunk)
                m.data["clauses_loaded"] += len(chunk)
            del chunk
        m.progress(force=True)
        with m.phase("solve_s"):
            answer = solver.solve()  # External supervisor enforces the hard deadline.
        m.data["native_status"] = "SAT" if answer is True else "UNSAT" if answer is False else "UNKNOWN"
        try:
            m.data["solver_stats"] = solver.accum_stats()
        except (AttributeError, NotImplementedError):
            m.data["solver_stats"] = {}
        if answer is True:
            with m.phase("decode_validate_s"):
                model = solver.get_model()
                cols = sat_to_columns(model, job["n"])
                del model
                return m.solution(cols, job["n"])
        if answer is False:
            return {"status": "UNSAT", "termination_reason": "COMPLETED"}
        return {"status": "UNKNOWN", "termination_reason": "NATIVE_STOP"}
    finally:
        solver.delete()
