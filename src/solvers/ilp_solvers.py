def run_gurobi(n: int, timeout=100, **options):
    from src.utils.experiment_runner import run_job
    return run_job(n=n, solver="gurobi", timeout=timeout, **options)


def run_cplex_mip(n: int, timeout=100, **options):
    from src.utils.experiment_runner import run_job
    return run_job(n=n, solver="cplex_mip", timeout=timeout, **options)


def _solve_gurobi(job, m):
    from src.utils.validation import cells_to_columns
    with m.phase("setup_s"):
        import gurobipy as gp
        from gurobipy import GRB
        env = gp.Env(empty=True)
        try:
            env.setParam("OutputFlag", 0)
            env.start()
        except BaseException:
            env.dispose()
            raise
        m.data.update(solver_version=".".join(map(str, gp.gurobi.version())),
                      seed_applied=job["seed"])
    n = job["n"]
    try:
        with gp.Model("NQueens", env=env) as model:
            with m.phase("build_s"):
                model.Params.Threads, model.Params.Seed = job["threads"], job["seed"]
                x = model.addVars(n, n, vtype=GRB.BINARY, name="x")
                model.addConstrs((x.sum(i, "*") == 1 for i in range(n)))
                model.addConstrs((x.sum("*", j) == 1 for j in range(n)))
                for p in range(2 * n - 1):
                    rows = range(max(0, p - n + 1), min(n, p + 1))
                    model.addConstr(gp.quicksum(x[i, p - i] for i in rows) <= 1)
                    model.addConstr(gp.quicksum(x[i, n - 1 - p + i] for i in rows) <= 1)
                model.update()
                m.data.update(native_vars=model.NumVars, native_constraints=model.NumConstrs)
            m.progress(force=True)
            with m.phase("solve_s"):
                model.Params.TimeLimit = m.remaining()
                model.optimize()
            m.data.update(native_status=str(model.Status), native_solve_s=model.Runtime,
                          solver_stats={"nodes": model.NodeCount, "solutions": model.SolCount})
            if model.SolCount:
                with m.phase("decode_validate_s"):
                    values = model.getAttr("X", x)
                    cols = cells_to_columns((cell for cell, v in values.items() if v > 0.5), n)
                    answer = m.solution(cols, n)
                if model.Status == GRB.TIME_LIMIT:
                    answer["termination_reason"] = "NATIVE_TIME_LIMIT_WITH_SOLUTION"
                return answer
            if model.Status == GRB.INFEASIBLE:
                return {"status": "UNSAT", "termination_reason": "COMPLETED"}
            if model.Status == GRB.TIME_LIMIT:
                return {"status": "TIMEOUT", "termination_reason": "NATIVE_TIME_LIMIT"}
            return {"status": "UNKNOWN", "termination_reason": "NATIVE_STOP"}
    finally:
        env.dispose()


def _solve_cplex_mip(job, m):
    from src.solvers.common import cplex_mip_status, package_version
    from src.utils.validation import cells_to_columns
    with m.phase("setup_s"):
        from docplex.mp.model import Model
        m.data.update(solver_version="cplex " + str(package_version("cplex")),
                      seed_applied=job["seed"])
    n = job["n"]
    with Model(name="NQueens") as model:
        with m.phase("build_s"):
            model.parameters.threads = job["threads"]
            model.parameters.randomseed = job["seed"]
            x = model.binary_var_matrix(n, n, name="x")
            for i in range(n):
                model.add_constraint(model.sum(x[i, j] for j in range(n)) == 1)
                model.add_constraint(model.sum(x[j, i] for j in range(n)) == 1)
            for p in range(2 * n - 1):
                rows = range(max(0, p - n + 1), min(n, p + 1))
                model.add_constraint(model.sum(x[i, p - i] for i in rows) <= 1)
                model.add_constraint(model.sum(x[i, n - 1 - p + i] for i in rows) <= 1)
            m.data.update(native_vars=model.number_of_variables,
                          native_constraints=model.number_of_constraints)
        m.progress(force=True)
        with m.phase("solve_s"):
            model.parameters.timelimit = m.remaining()
            solution = model.solve(log_output=False)
        details = model.solve_details
        native = str(details.status)
        m.data.update(native_status=native, native_solve_s=details.time)
        status, reason = cplex_mip_status(native, solution is not None)
        if solution is not None:
            with m.phase("decode_validate_s"):
                values = solution.get_values(list(x.values()))
                cols = cells_to_columns((cell for cell, v in zip(x, values) if v > 0.5), n)
                answer = m.solution(cols, n)
                answer["termination_reason"] = reason
                return answer
        return {"status": status, "termination_reason": reason}
