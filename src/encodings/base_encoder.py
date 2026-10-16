"""Bố trí biến bàn cờ và số đếm chính xác của CNF đầy đủ theo từng encoder."""
from functools import lru_cache
from math import isqrt


def validate_n(n: int) -> None:
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("N must be a positive integer")


def get_var_id(n: int, row: int, col: int) -> int:
    return row * n + col + 1


def yield_alo(n: int, column_alo: bool = True):
    validate_n(n)
    for row in range(n):
        yield list(range(row * n + 1, (row + 1) * n + 1))
    if column_alo:
        for col in range(n):
            yield list(range(col + 1, n * n + 1, n))


def yield_all_lines(n: int):
    """Original line/variable order, using compact ranges."""
    validate_n(n)
    for row in range(n):
        yield range(row * n + 1, (row + 1) * n + 1)
    for col in range(n):
        yield range(col + 1, n * n + 1, n)
    for p in range(2 * n - 1):
        lo, hi = max(0, p - n + 1), min(n, p + 1)
        if hi - lo > 1:
            yield range((n - 1) * lo + p + 1, (n - 1) * hi + p + 1, n - 1)
            yield range((n + 1) * lo + n - p, (n + 1) * hi + n - p, n + 1)


@lru_cache(maxsize=None)
def _recursive_amo_counts(k: int, encoding: str):
    """Trả (biến phụ, clause, literal) của một nhóm AMO, gồm mọi tầng."""
    pair = lambda size: size * (size - 1) // 2

    if encoding == "Commander":
        if k <= 3:
            return 0, pair(k), 2 * pair(k)
        groups = (k + 2) // 3
        full, rem = divmod(k, 3)
        inside = 3 * full + pair(rem)
        aux, clauses, literals = _recursive_amo_counts(groups, encoding)
        # Tầng này: groups biến mới; inside clause cấm cặp; k liên kết
        # x=>commander; groups liên kết commander=>OR(nhóm).
        # Tổng literal: 2*inside + 2*k + (k+groups).
        return (groups + aux,
                inside + k + groups + clauses,
                2 * inside + 3 * k + groups + literals)

    if encoding == "Product":
        if k <= 4:
            return 0, pair(k), 2 * pair(k)
        p = isqrt(k - 1) + 1
        q = (k + p - 1) // p
        ar, cr, lr = _recursive_amo_counts(p, encoding)
        ac, cc, lc = _recursive_amo_counts(q, encoding)
        # Tầng này cấp p+q tọa độ; mỗi biến có 2 clause, mỗi clause 2 literal.
        return p + q + ar + ac, 2 * k + cr + cc, 4 * k + lr + lc

    raise ValueError(f"Unknown recursive encoding: {encoding}")


def estimate_cnf(n: int, encoding: str, column_alo: bool = True) -> dict:
    """Đếm CNF ĐẦY ĐỦ theo công thức, không tạo hoặc lưu danh sách clause.

    Commander/Product ở đây là bản đệ quy; Sequential có nhánh nhỏ k<=3.
    Khi TIMEOUT giữa chừng, số này vẫn mô tả toàn bộ mô hình dự kiến.
    clauses_generated/clauses_loaded trong kết quả mô tả tiến độ đã nhận.
    Kiểm thử đối chiếu công thức với CNF sinh thật, không chỉ ID lớn nhất.
    """
    validate_n(n)
    if encoding not in {"Binomial", "Binary", "Commander", "Product", "Sequential"}:
        raise ValueError(f"Unknown encoding: {encoding}")
    aux = 0
    # ALO: n clause hàng, thêm n clause cột khi column_alo=True.
    clauses = n * (1 + bool(column_alo))
    literals = n * n * (1 + bool(column_alo))
    pair = lambda k: k * (k - 1) // 2
    for k in range(2, n + 1):
        # 2n hàng/cột + 2 chéo dài n; mỗi độ dài 2..n-1 có 4 đường chéo.
        multiplicity = 2 * n + 2 if k == n else 4
        if encoding == "Binomial":
            a, c = 0, pair(k)
            lit = 2 * c
        elif encoding == "Binary":
            a = (k - 1).bit_length()
            c = k * a
            lit = 2 * c
        elif encoding == "Sequential":
            a, c = (0, pair(k)) if k <= 3 else (k - 1, 3 * k - 4)
            lit = 2 * c
        else:
            a, c, lit = _recursive_amo_counts(k, encoding)
        aux += multiplicity * a
        clauses += multiplicity * c
        literals += multiplicity * lit
    return {"primary_vars": n * n, "aux_vars": aux,
            "cnf_clauses": clauses, "cnf_literals": literals,
            "count_source": "exact_formula"}
