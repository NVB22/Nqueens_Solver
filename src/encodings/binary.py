import math
from .base_encoder import yield_all_lines, get_var_id

def generate_binary_clauses(n: int):
    aux_state = [n * n + 1]
    
    for i in range(n):
        yield [get_var_id(n, i, j) for j in range(n)]
        
    for line in yield_all_lines(n):
        k = len(line)
        if k <= 1:
            continue
            
        num_bits = math.ceil(math.log2(k))
        aux_vars = [aux_state[0] + i for i in range(num_bits)]
        aux_state[0] += num_bits
        
        for i, var in enumerate(line):
            for j in range(num_bits):
                # Kiểm tra bit thứ j của số i
                if (i & (1 << j)) != 0:
                    yield [-var, aux_vars[j]]
                else:
                    yield [-var, -aux_vars[j]]