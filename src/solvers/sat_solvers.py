# import time
# from pysat.solvers import Solver

# def run_sat(clauses_generator, solver_name: str, timeout: int = 100) -> dict:
#     """
#     Tiêu thụ luồng mệnh đề lười (lazy clauses) và đẩy vào SAT Solver.
#     Hỗ trợ: 'glucose3', 'cadical', 'kissat', 'cryptominisat'.
#     """
#     start_time = time.perf_counter()
#     try:
#         # Ép Generator thành List trước khi nạp để tối ưu tốc độ I/O của PySAT
#         clauses = list(clauses_generator) 
        
#         with Solver(name=solver_name, bootstrap_with=clauses) as solver:
#             is_sat = solver.solve()
#             return {
#                 "status": "Optimal" if is_sat else "Infeasible", 
#                 "time": time.perf_counter() - start_time,
#                 "vars": solver.nof_vars(),
#                 "clauses": solver.nof_clauses()
#             }
#     except Exception as e:
#         return {"status": f"Error: {str(e)}", "time": time.perf_counter() - start_time}



import time
from pysat.solvers import Solver

def run_sat(clauses_generator, solver_name: str, timeout: int = 100) -> dict:
    start_time = time.perf_counter()
    try:
        clauses = list(clauses_generator) 
        
        with Solver(name=solver_name, bootstrap_with=clauses) as solver:
            is_sat = solver.solve()
            # Lấy mảng nghiệm nếu trạng thái là SAT
            model = solver.get_model() if is_sat else None
            
            return {
                "status": "Optimal" if is_sat else "Infeasible", 
                "time": time.perf_counter() - start_time,
                "vars": solver.nof_vars(),
                "clauses": solver.nof_clauses(),
                "model": model  # Dữ liệu mới được thêm vào
            }
    except Exception as e:
        return {"status": f"Error: {str(e)}", "time": time.perf_counter() - start_time, "model": None}