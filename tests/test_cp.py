import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.solvers.cp_solvers import run_cp_sat, run_cp_cplex

TEST_SIZES = [2, 4, 8]

def helper_run_cp_solver(solver_func):
    """Hàm helper kiểm tra logic cho các trình giải Constraint Programming"""
    is_cplex = (solver_func.__name__ == 'run_cp_cplex')

    for n in TEST_SIZES:
        result = solver_func(n)
        
        # N=2 và N=3 bài toán N-Queens không có nghiệm
        expected_status = "Timeout/Infeasible" if n < 4 else "Optimal"

        # Khớp điều kiện dựa trên loại solver
        if is_cplex:
            # Chấp nhận thêm License/Error nếu test trên máy không cài CPLEX Studio
            assert result["status"] in [expected_status, "License/Error"], \
                f"Lỗi ở {solver_func.__name__} tại N={n}. Trạng thái nhận được: {result['status']}"
        else:
            # OR-Tools miễn phí nên bắt buộc phải ra đúng trạng thái kỳ vọng
            assert result["status"] == expected_status, \
                f"Lỗi ở {solver_func.__name__} tại N={n}. Trạng thái nhận được: {result['status']}"

        # Chỉ kiểm tra thời gian nếu hàm chạy bình thường (không văng lỗi bản quyền)
        if result["status"] != "License/Error":
            assert result["time"] > 0, f"Thời gian chạy phải > 0 tại N={n}"

def test_cp_sat():
    helper_run_cp_solver(run_cp_sat)

def test_cp_cplex():
    helper_run_cp_solver(run_cp_cplex)

if __name__ == '__main__':
    print("Đang chạy kiểm thử CP-SAT:")
    test_cp_sat()
    print("Đang chạy kiểm thử CPLEX Optimizer:")
    test_cp_cplex()
    print("Hoàn tất kiểm thử (Các assert đều pass)!")