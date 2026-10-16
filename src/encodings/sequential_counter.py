from itertools import combinations, count

from .base_encoder import yield_all_lines, yield_alo


def _amo(inputs, auxiliary_ids):
    k = len(inputs)

    # Bước 1: nhóm nhỏ không cần chuỗi phụ.
    # k=2: 1 clause, 0 biến phụ (chuỗi gốc: 2 clause, 1 biến phụ).
    # k=3: 3 clause, 0 biến phụ (chuỗi gốc: 5 clause, 2 biến phụ).
    # Đây là tối ưu bổ sung; slide mô tả chuỗi tổng quát k-1 / 3k-4.
    if k <= 3:
        for left, right in combinations(inputs, 2):
            yield [-left, -right]
        return

    # Bước 2: x1 => s1. Nếu đã có biến đúng trong tiền tố thì cờ phải bật.
    # Các clause chỉ buộc các chiều cần cho AMO, không mã hóa đầy đủ iff.
    previous = next(auxiliary_ids)
    yield [-inputs[0], previous]

    # Bước 3: với mỗi xi ở giữa, cấp si mới và sinh đúng 3 clause.
    # Ghi nhớ ID trước đó, không cần dựng cả danh sách biến của chuỗi.
    for variable in inputs[1:-1]:
        current = next(auxiliary_ids)
        negative = -variable
        yield [negative, current]       # xi => si: ghi nhận biến vừa đúng.
        yield [-previous, current]      # s(i-1) => si: truyền cờ về sau.
        yield [negative, -previous]     # Cấm xi đúng nếu tiền tố đã có biến đúng.
        previous = current

    # Bước 4: s(k-1) => NOT xk. Biến cuối không cần tạo thêm cờ sk.
    yield [-inputs[-1], -previous]
    # k>=4: tổng cộng k-1 biến phụ và 1 + 3*(k-2) + 1 = 3k-4 clause.


def generate_sequential_clauses(n: int, column_alo: bool = True):
    yield from yield_alo(n, column_alo)
    auxiliary_ids = count(n * n + 1)
    for line in yield_all_lines(n):
        yield from _amo(line, auxiliary_ids)
