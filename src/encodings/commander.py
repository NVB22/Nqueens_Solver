import math
from itertools import combinations
from .base_encoder import yield_all_lines, get_var_id

def generate_commander_clauses(n: int):
    aux_state = [n * n + 1]
    
    for i in range(n):
        yield [get_var_id(n, i, j) for j in range(n)]
        
    for line in yield_all_lines(n):
        k = len(line)
        if k <= 1:
            continue
            
        g = math.floor(math.sqrt(k))
        if g == 0: g = 1
        
        # Chia nhóm
        groups = [line[i:i+g] for i in range(0, k, g)]
        commanders = [aux_state[0] + i for i in range(len(groups))]
        aux_state[0] += len(groups)
        
        # AMO cho các chỉ huy
        for c1, c2 in combinations(commanders, 2):
            yield [-c1, -c2]
            
        for idx, group in enumerate(groups):
            c = commanders[idx]
            
            # Nếu chỉ huy True -> Ít nhất 1 lính True
            yield [-c] + group
            
            # Nếu chỉ huy True -> Không quá 1 lính True
            for v1, v2 in combinations(group, 2):
                yield [-c, -v1, -v2]
                
            # Nếu chỉ huy False -> Mọi lính đều False
            for v in group:
                yield [c, -v]