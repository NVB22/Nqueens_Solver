from itertools import combinations, count

from .base_encoder import yield_all_lines, yield_alo


def _amo(inputs, auxiliary_ids):
    """Sinh AMO(inputs); auxiliary_ids cấp ID mới dùng chung cho toàn CNF."""
    k = len(inputs)

    # Bước 1: nhóm nhỏ dùng cấm từng cặp, không cần biến phụ.
    # Nhóm 0 hoặc 1 biến tự thỏa AMO, nên không sinh clause nào.
    if k <= 3:
        for left, right in combinations(inputs, 2):
            yield [-left, -right]
        return

    # Bước 2: chia thành các nhóm tối đa 3 biến; mỗi nhóm có một commander.
    # ceil(k / 3) = (k + 2) // 3; nhóm cuối có thể thiếu 1 hoặc 2 biến.
    commanders = tuple(next(auxiliary_ids) for _ in range((k + 2) // 3))

    # Bước 3: áp dụng chính Commander đệ quy cho tập commander.
    # Nhờ vậy, ở mọi tầng đều chỉ có tối đa một nhóm được hoạt động.
    yield from _amo(commanders, auxiliary_ids)

    for start, commander in zip(range(0, k, 3), commanders):
        group = inputs[start:start + 3]

        # Bước 4: bên trong một nhóm, cấm hai biến cùng đúng.
        # Không cần thêm -commander vào các clause cấm cặp:
        # các liên kết bên dưới đã buộc biến đúng => commander đúng.
        for left, right in combinations(group, 2):
            yield [-left, -right]

        # Bước 5: commander đúng => ít nhất một biến trong nhóm đúng.
        # Đây là ALO CÓ ĐIỀU KIỆN, không bắt buộc nhóm phải có biến đúng.
        yield [-commander, *group]

        # Bước 6: biến trong nhóm đúng => commander của nhóm đúng.
        for variable in group:
            yield [-variable, commander]


def generate_commander_clauses(n: int, column_alo: bool = True):
    # ALO: mỗi hàng có ít nhất một hậu; thêm ALO cột khi được bật.
    # Không thêm ALO cho đường chéo hoặc cho tập commander toàn cục.
    yield from yield_alo(n, column_alo)

    # ID 1..n*n dành cho các ô bàn cờ. Mọi tầng đệ quy và mọi đường
    # dùng CHUNG một bộ cấp ID, tránh hai nhóm dùng trùng biến phụ.
    auxiliary_ids = count(n * n + 1)

    # AMO: tối đa một hậu trên mỗi hàng, cột và đường chéo.
    for line in yield_all_lines(n):
        yield from _amo(line, auxiliary_ids)
