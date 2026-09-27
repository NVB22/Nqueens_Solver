from itertools import combinations
from .base_encoder import yield_all_lines, get_var_id

def generate_binomial_clauses(n: int):
    # Ràng buộc ALO (Ít nhất 1 hậu mỗi hàng)
    for i in range(n):
        yield [get_var_id(n, i, j) for j in range(n)]
        
    # Ràng buộc AMO (Không quá 1 hậu) cho tất cả các đường
    for line in yield_all_lines(n):
        for v1, v2 in combinations(line, 2):
            yield [-v1, -v2]