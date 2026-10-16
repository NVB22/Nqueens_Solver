from itertools import combinations, count, product
from math import isqrt
from .base_encoder import yield_all_lines, yield_alo


def _amo(inputs, auxiliary_ids):
    """Sinh AMO(inputs) bằng lưới tọa độ phụ và hai lời gọi đệ quy."""
    k = len(inputs)

    # Bước 1: nhóm tối đa 4 biến dùng cấm từng cặp, không cấp biến phụ.
    # Đây cũng là điểm dừng, để đệ quy không tiếp tục ở nhóm quá nhỏ.
    if k <= 4:
        for left, right in combinations(inputs, 2):
            yield [-left, -right]
        return

    # Bước 2: tạo lưới phụ p*q có đủ k ô, p = ceil(sqrt(k)).
    # Dùng số nguyên để tránh sai số khi lấy căn bậc hai.
    p = isqrt(k - 1) + 1
    q = (k + p - 1) // p
    rows = tuple(next(auxiliary_ids) for _ in range(p))
    cols = tuple(next(auxiliary_ids) for _ in range(q))

    # Bước 3: tối đa một tọa độ hàng và một tọa độ cột được đúng.
    # Thay pairwise một tầng bằng Product đệ quy trên hai tập này.
    yield from _amo(rows, auxiliary_ids)
    yield from _amo(cols, auxiliary_ids)

    # Bước 4: gán mỗi biến đầu vào một cặp tọa độ riêng biệt.
    # x đúng => hàng phụ đúng VÀ cột phụ đúng, tức hai clause nhị phân.
    # Hai biến khác nhau cùng đúng sẽ vi phạm AMO hàng phụ hoặc cột phụ.
    # zip dừng sau k biến; các ô trống của lưới phụ không có biến đầu vào.
    for variable, (row_aux, col_aux) in zip(inputs, product(rows, cols)):
        negative = -variable
        yield [negative, row_aux]
        yield [negative, col_aux]


def generate_product_clauses(n: int, column_alo: bool = True):
    # ALO của bàn cờ vẫn là một clause trực tiếp cho mỗi hàng/cột.
    yield from yield_alo(n, column_alo)
    auxiliary_ids = count(n * n + 1)
    for line in yield_all_lines(n):
        # rows/cols trong _amo là tọa độ PHỤ của riêng nhóm này,
        # không phải hàng/cột thật của bàn cờ N-Queens.
        yield from _amo(line, auxiliary_ids)
