def get_var_id(n: int, row: int, col: int) -> int:
    """Tính ID biến tuyến tính từ tọa độ (row, col)"""
    return row * n + col + 1

def yield_all_lines(n: int):
    """
    Generator trả về danh sách các biến trên từng hàng, cột và đường chéo.
    Giúp tái sử dụng mã nguồn cho mọi thuật toán AMO.
    """
    # 1. Hàng (Rows)
    for i in range(n):
        yield [get_var_id(n, i, j) for j in range(n)]
        
    # 2. Cột (Columns)
    for j in range(n):
        yield [get_var_id(n, i, j) for i in range(n)]
        
    # 3. Đường chéo (Diagonals) - Chỉ lấy các đường có nhiều hơn 1 ô
    for p in range(2 * n - 1):
        diag1 = [get_var_id(n, i, p - i) for i in range(max(0, p - n + 1), min(n, p + 1))]
        if len(diag1) > 1:
            yield diag1
            
        diag2 = [get_var_id(n, i, n - 1 - p + i) for i in range(max(0, p - n + 1), min(n, p + 1))]
        if len(diag2) > 1:
            yield diag2