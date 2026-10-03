import time
from ortools.sat.python import cp_model
import docplex.cp.model as cp_docplex

def run_cp_sat(n: int, timeout: int = 100) -> dict:
    """Giải N-Queens bằng (CP-SAT)"""
    start = time.perf_counter()
    
    model = cp_model.CpModel()
    queens = [model.NewIntVar(0, n - 1, f'q_{i}') for i in range(n)]
    
    model.AddAllDifferent(queens)
    model.AddAllDifferent([queens[i] + i for i in range(n)])
    model.AddAllDifferent([queens[i] - i for i in range(n)])
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout
    status = solver.Solve(model)
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {"status": "Optimal", "time": time.perf_counter() - start}
    return {"status": "Timeout/Infeasible", "time": time.perf_counter() - start}

def run_cp_cplex(n: int, timeout: int = 100) -> dict:
    """Giải N-Queens bằng IBM ILOG Cplex CP Optimizer"""
    start = time.perf_counter()
    try:
        mdl = cp_docplex.CpoModel(name="NQueens_Cplex_CP")
        queens = cp_docplex.integer_var_list(n, 0, n - 1, "Q")
        
        mdl.add(cp_docplex.all_diff(queens))
        mdl.add(cp_docplex.all_diff([queens[i] + i for i in range(n)]))
        mdl.add(cp_docplex.all_diff([queens[i] - i for i in range(n)]))
        
        sol = mdl.solve(TimeLimit=timeout, LogVerbosity="Quiet")
        if sol and sol.is_solution():
            return {"status": "Optimal", "time": time.perf_counter() - start}
        return {"status": "Timeout/Infeasible", "time": time.perf_counter() - start}
    except Exception as e:
        return {"status": "License/Error", "time": time.perf_counter() - start}