import math
from itertools import combinations
from .base_encoder import yield_all_lines, get_var_id

def generate_product_clauses(n: int):
    aux_state = [n * n + 1]
    
    for i in range(n):
        yield [get_var_id(n, i, j) for j in range(n)]
        
    for line in yield_all_lines(n):
        k = len(line)
        if k <= 1:
            continue
            
        p = math.ceil(math.sqrt(k))
        q = math.ceil(k / p)
        
        # Trục tọa độ ảo r và c
        rows = [aux_state[0] + i for i in range(p)]
        aux_state[0] += p
        cols = [aux_state[0] + i for i in range(q)]
        aux_state[0] += q
        
        # AMO cho r và c
        for r1, r2 in combinations(rows, 2):
            yield [-r1, -r2]
        for c1, c2 in combinations(cols, 2):
            yield [-c1, -c2]
            
        for idx, var in enumerate(line):
            r_idx = idx // q
            c_idx = idx % q
            
            # Nếu biến chính True -> Biến tọa độ r và c phải True
            yield [-var, rows[r_idx]]
            yield [-var, cols[c_idx]]