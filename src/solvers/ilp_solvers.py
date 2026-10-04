import time
import gurobipy as gp
from gurobipy import GRB
from docplex.mp.model import Model as MipModel

def run_gurobi(n: int, timeout: int = 100) -> dict:
    """Giải N-Queens bằng Gurobi ILP"""
    start = time.perf_counter()
    try:
        # Tắt output console mặc định của Gurobi để terminal không bị loạn
        env = gp.Env(empty=True)
        env.setParam("OutputFlag", 0)
        env.start()
        
        model = gp.Model("NQueens_Gurobi", env=env)
        model.setParam('TimeLimit', timeout)
        
        # Ma trận nhị phân N x N
        x = model.addVars(n, n, vtype=GRB.BINARY, name="x")
        
        # Ràng buộc: Mỗi hàng/cột có đúng 1 hậu (Tổng = 1)
        model.addConstrs((x.sum(i, '*') == 1 for i in range(n)), "row")
        model.addConstrs((x.sum('*', j) == 1 for j in range(n)), "col")
        
        # Ràng buộc: Đường chéo chính và phụ có không quá 1 hậu (Tổng <= 1)
        for p in range(2 * n - 1):
            model.addConstr(gp.quicksum(x[i, p - i] for i in range(max(0, p - n + 1), min(n, p + 1))) <= 1)
            model.addConstr(gp.quicksum(x[i, n - 1 - p + i] for i in range(max(0, p - n + 1), min(n, p + 1))) <= 1)
        
        model.optimize()
        
        if model.Status == GRB.OPTIMAL:
            return {"status": "Optimal", "time": time.perf_counter() - start}
        return {"status": "Timeout/Infeasible", "time": time.perf_counter() - start}
    except Exception as e:
        return {"status": "License/Error", "time": time.perf_counter() - start}

def run_cplex_mip(n: int, timeout: int = 100) -> dict:
    """Giải N-Queens bằng IBM Cplex MIP"""
    start = time.perf_counter()
    try:
        mdl = MipModel(name="NQueens_Cplex_MIP")
        mdl.parameters.timelimit = timeout
        mdl.context.solver.log_output = False
        
        x = mdl.binary_var_matrix(n, n, name="x")
        
        for i in range(n):
            mdl.add_constraint(mdl.sum(x[i, j] for j in range(n)) == 1)
            mdl.add_constraint(mdl.sum(x[j, i] for j in range(n)) == 1)
            
        for p in range(2 * n - 1):
            mdl.add_constraint(mdl.sum(x[i, p - i] for i in range(max(0, p - n + 1), min(n, p + 1))) <= 1)
            mdl.add_constraint(mdl.sum(x[i, n - 1 - p + i] for i in range(max(0, p - n + 1), min(n, p + 1))) <= 1)
            
        sol = mdl.solve()
        if sol:
            return {"status": "Optimal", "time": time.perf_counter() - start}
        return {"status": "Timeout/Infeasible", "time": time.perf_counter() - start}
    except Exception as e:
        return {"status": "License/Error", "time": time.perf_counter() - start}