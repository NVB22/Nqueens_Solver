import os


def run_cp_sat(n: int, timeout=100, **options):
    from src.utils.experiment_runner import run_job
    return run_job(n=n, solver="cp_sat", timeout=timeout, **options)


def run_cp_cplex(n: int, timeout=100, **options):
    from src.utils.experiment_runner import run_job
    return run_job(n=n, solver="cplex_cp", timeout=timeout, **options)


def _solve_cp_sat(job, m):
    from src.solvers.common import package_version
    with m.phase("setup_s"):
        from ortools.sat.python import cp_model
        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = job["threads"]
        solver.parameters.random_seed = job["seed"]
        m.data.update(solver_version=package_version("ortools"), seed_applied=job["seed"])
    n = job["n"]
    with m.phase("build_s"):
        model = cp_model.CpModel()
        q = [model.NewIntVar(0, n - 1, f"q_{i}") for i in range(n)]
        model.AddAllDifferent(q)
        model.AddAllDifferent([q[i] + i for i in range(n)])
        model.AddAllDifferent([q[i] - i for i in range(n)])
        m.data.update(native_vars=n, native_constraints=3)
    m.progress(force=True)
    with m.phase("solve_s"):
        solver.parameters.max_time_in_seconds = m.remaining()
        status = solver.Solve(model)
    m.data.update(native_status=solver.StatusName(status), native_solve_s=solver.WallTime(),
                  solver_stats={"conflicts": solver.NumConflicts(), "branches": solver.NumBranches()})
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        with m.phase("decode_validate_s"):
            return m.solution([int(solver.Value(v)) for v in q], n)
    if status == cp_model.INFEASIBLE:
        return {"status": "UNSAT", "termination_reason": "COMPLETED"}
    if status == cp_model.MODEL_INVALID:
        return {"status": "ERROR", "termination_reason": "MODEL_INVALID",
                "error_type": "ModelInvalid", "error_message": solver.ResponseStats()}
    return {"status": "UNKNOWN", "termination_reason": "NATIVE_STOP"}


def _solve_cp_cplex(job, m):
    from src.solvers.common import package_version
    with m.phase("setup_s"):
        import docplex.cp.model as cp
        m.data.update(solver_version="docplex " + str(package_version("docplex")),
                      seed_applied=job["seed"])
    n = job["n"]
    with m.phase("build_s"):
        model = cp.CpoModel(name="NQueens")
        q = cp.integer_var_list(n, 0, n - 1, "q")
        model.add(cp.all_diff(q))
        model.add(cp.all_diff([q[i] + i for i in range(n)]))
        model.add(cp.all_diff([q[i] - i for i in range(n)]))
        m.data.update(native_vars=n, native_constraints=3)
    m.progress(force=True)
    kwargs = {"Workers": job["threads"], "RandomSeed": job["seed"], "LogVerbosity": "Quiet"}
    executable = job.get("cpoptimizer") or os.environ.get("CPO_EXECUTABLE")
    if executable:
        kwargs["execfile"] = executable
    with m.phase("solve_s"):
        kwargs["TimeLimit"] = m.remaining()
        result = model.solve(**kwargs)
    if result is None:
        return {"status": "UNKNOWN", "termination_reason": "NO_RESULT"}
    native, cause = str(result.get_solve_status()), str(result.get_stop_cause())
    m.data.update(native_status=native, native_stop_cause=cause,
                  native_solve_s=result.get_solve_time())
    infos = result.get_solver_infos()
    if infos.get("SolverVersion"):
        m.data["solver_version"] += "; CP Optimizer " + str(infos.get("SolverVersion"))
    if result.is_solution():
        with m.phase("decode_validate_s"):
            answer = m.solution([int(result.get_value(v)) for v in q], n)
        if cause == "SearchStoppedByLimit":
            answer["termination_reason"] = "NATIVE_LIMIT_WITH_SOLUTION"
        return answer
    if native == "Infeasible":
        return {"status": "UNSAT", "termination_reason": "COMPLETED"}
    if native == "JobFailed":
        return {"status": "ERROR", "termination_reason": "NATIVE_FAILURE",
                "error_type": "CpoJobFailed", "error_message": str(result)}
    return {"status": "UNKNOWN", "termination_reason": cause or "NATIVE_STOP"}
