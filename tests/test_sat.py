import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.solvers.sat_solvers import run_sat
from src.encodings.binomial import generate_binomial_clauses
from src.encodings.binary import generate_binary_clauses
from src.encodings.sequential_counter import generate_sequential_clauses
from src.encodings.commander import generate_commander_clauses
from src.encodings.product import generate_product_clauses


SOLVER = "glucose3"
TEST_SIZES = [4, 8]

def helper_run_encoding(encoding_func):
    """Hàm helper thuần túy kiểm tra logic cho một thuật toán bất kỳ"""
    for n in TEST_SIZES:
        clauses = encoding_func(n)
        res = run_sat(clauses, SOLVER)
        
        assert res["status"] == "Optimal", f"Lỗi ở thuật toán {encoding_func.__name__} tại N={n}"
        assert res["vars"] > 0, "Số biến phải lớn hơn 0"
        assert res["clauses"] > 0, "Số mệnh đề phải lớn hơn 0"

def test_binomial():
    helper_run_encoding(generate_binomial_clauses)

def test_binary():
    helper_run_encoding(generate_binary_clauses)

def test_sequential():
    helper_run_encoding(generate_sequential_clauses)

def test_commander():
    helper_run_encoding(generate_commander_clauses)
    
def test_product():
    helper_run_encoding(generate_product_clauses)


if __name__ == '__main__':
    # Chạy manual nếu không dùng công cụ test runner
    print("Đang chạy kiểm thử thuật toán")
    test_binomial()
    test_binary()
    test_sequential()
    test_commander()
    test_product()