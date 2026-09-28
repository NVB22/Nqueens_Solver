from .base_encoder import yield_all_lines, get_var_id

def generate_sequential_clauses(n: int):
    aux_state = [n * n + 1] # Dùng list để truyền tham chiếu (mutable) qua các vòng lặp
    
    # Ràng buộc ALO
    for i in range(n):
        yield [get_var_id(n, i, j) for j in range(n)]
        
    for line in yield_all_lines(n):
        k = len(line)
        if k <= 1:
            continue
            
        # Khởi tạo k-1 biến phụ trợ (s_1 đến s_k-1)
        s = [aux_state[0] + i for i in range(k - 1)]
        aux_state[0] += k - 1
        
        # Logic Sequential Encoding
        yield [-line[0], s[0]]
        yield [-line[-1], -s[-1]]
        
        for i in range(1, k - 1):
            yield [-line[i], s[i]]
            yield [-s[i-1], s[i]]
            yield [-line[i], -s[i-1]]