import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from src.utils.resource_monitor import get_current_ram_mb
from src.utils.wandb_logger import init_wandb, log_result, finish_wandb

from src.encodings.binomial import generate_binomial_clauses
from src.encodings.binary import generate_binary_clauses
from src.encodings.commander import generate_commander_clauses
from src.encodings.product import generate_product_clauses
from src.encodings.sequential_counter import generate_sequential_clauses

from src.solvers.sat_solvers import run_sat
from src.solvers.cp_solvers import run_cp_sat, run_cp_cplex
from src.solvers.ilp_solvers import run_gurobi, run_cplex_mip

N_SIZES = [2,4, 8, 12, 16, 25, 36] 
SAT_SOLVERS = ['glucose3'] 

ENCODINGS = {
    "Binomial": generate_binomial_clauses,
    "Binary": generate_binary_clauses,
    "Commander": generate_commander_clauses,
    "Product": generate_product_clauses,
    "Sequential": generate_sequential_clauses
}

def draw_board(model, n):
    """Hàm vẽ bàn cờ từ mảng nghiệm của SAT Solver"""
    if not model:
        return
    print(f"\n--- Bàn cờ minh họa (N={n}) ---")
    board = [['.' for _ in range(n)] for _ in range(n)]
    
    for val in model:
        # Chỉ quét các biến mang giá trị dương (đặt Hậu) và là biến trên bàn cờ (<= n*n)
        if val > 0 and val <= n * n:
            idx = val - 1
            r, c = idx // n, idx % n
            board[r][c] = 'Q'
            
    for row in board:
        print(" " + "  ".join(row))
    print("-" * 30)

def main():
    init_wandb()
    print("=== BẮT ĐẦU CHẠY THỰC NGHIỆM ĐÁNH GIÁ N-QUEENS ===")
    
    for enc_name, enc_func in ENCODINGS.items():
        for solver_name in SAT_SOLVERS:
            print(f"\n>> Đang chạy SAT | Mã hóa: {enc_name} | Bộ giải: {solver_name.upper()}")
            
            for n in N_SIZES:
                ram_before = get_current_ram_mb()
                clauses_gen = enc_func(n)
                res = run_sat(clauses_gen, solver_name)
                
                ram_after = get_current_ram_mb()
                ram_used = max(0, ram_after - ram_before)
                
                vars_count = res.get('vars', 0)
                clauses_count = res.get('clauses', 0)
                
                print(f"N={n:<3} | {res['status']:<10} | Time: {res['time']:.4f}s | Vars: {vars_count:<7} | Clauses: {clauses_count:<8} | RAM: {ram_used:.2f}MB")
                
                # Chỉ in bàn cờ trực quan cho N=4 hoặc N=8 để tránh làm rối màn hình
                if res['status'] == "Optimal" and n in [4, 8]:
                    draw_board(res['model'], n)
                
                log_result({
                    "Category": "SAT",
                    "Algorithm": enc_name,
                    "Solver": solver_name,
                    "N": n,
                    "Time": res['time'],
                    "Variables": vars_count,
                    "Clauses": clauses_count,
                    "RAM_MB": ram_used,
                    "Status": res['status']
                })

    print("\n=== CHẠY NHÓM CP VÀ ILP ĐỐI SÁNH ===")
    advanced_solvers = {
        "CP-SAT": run_cp_sat,
        "Cplex CP": run_cp_cplex,
        # "Gurobi ILP": run_gurobi,
        # "Cplex MIP": run_cplex_mip
    }
    
    for adv_name, adv_func in advanced_solvers.items():
        print(f"\n>> Đang chạy: {adv_name}")
        for n in N_SIZES:
            res = adv_func(n)
            print(f"N={n:<3} | {res['status']:<18} | Time: {res['time']:.4f}s")
            log_result({
                "Category": "Advanced",
                "Algorithm": "Native_Model",
                "Solver": adv_name,
                "N": n,
                "Time": res['time'],
                "Variables": 0, 
                "Clauses": 0,
                "RAM_MB": 0,
                "Status": res['status']
            })
            
    finish_wandb()

if __name__ == "__main__":
    main()