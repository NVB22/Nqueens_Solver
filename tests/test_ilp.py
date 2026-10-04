import sys
import os

# Thêm thư mục gốc vào sys.path để nhận diện package src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.solvers.ilp_solvers import run_gurobi, run_cplex_mip

TEST_SIZES = [2, 4, 8]

def helper_run_ilp(solver_func):
    """Hàm helper kiểm tra logic cho các trình giải ILP"""
    for n in TEST_SIZES:
        res = solver_func(n)
        
        # N=2 và N=3 không có nghiệm, kỳ vọng Timeout/Infeasible
        expected_status = "Timeout/Infeasible" if n < 4 else "Optimal"
        
        # Chấp nhận cả License/Error trong trường hợp máy chưa cài bản quyền Gurobi/CPLEX
        assert res["status"] in [expected_status, "License/Error"], \
            f"Lỗi ở {solver_func.__name__} tại N={n}. Trạng thái nhận được: {res['status']}"
            
        # Đảm bảo thời gian chạy hợp lệ
        assert res["time"] >= 0, f"Thời gian chạy phải >= 0 tại N={n}"

def test_gurobi():
    helper_run_ilp(run_gurobi)

def test_cplex_mip():
    helper_run_ilp(run_cplex_mip)

if __name__ == '__main__':
    print("Đang chạy kiểm thử trình giải ILP (Gurobi & CPLEX MIP)...")
    test_gurobi()
    test_cplex_mip()