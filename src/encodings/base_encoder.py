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


def estimate_cnf(n: int, encoding: str, column_alo: bool = True) -> dict:
    validate_n(n)
    if encoding not in {"Binomial", "Binary", "Commander", "Product", "Sequential"}:
        raise ValueError(f"Unknown encoding: {encoding}")
    aux = 0
    clauses = n * (1 + bool(column_alo))
    literals = n * n * (1 + bool(column_alo))
    pair = lambda k: k * (k - 1) // 2
    for k in range(2, n + 1):
        multiplicity = 2 * n + 2 if k == n else 4
        if encoding == "Binomial":
            a, c = 0, pair(k)
            lit = 2 * c
        elif encoding == "Binary":
            a = (k - 1).bit_length()
            c = k * a
            lit = 2 * c
        elif encoding == "Sequential":
            a, c = k - 1, 3 * k - 4
            lit = 2 * c
        elif encoding == "Product":
            p = isqrt(k - 1) + 1
            q = (k + p - 1) // p
            a, c = p + q, 2 * k + pair(p) + pair(q)
            lit = 2 * c
        else:
            group_size = isqrt(k)
            full, rem = divmod(k, group_size)
            a = full + bool(rem)
            inside = full * pair(group_size) + pair(rem)
            c = pair(a) + a + k + inside
            lit = 2 * pair(a) + a + 3 * k + 3 * inside
        aux += multiplicity * a
        clauses += multiplicity * c
        literals += multiplicity * lit
    return {"primary_vars": n * n, "aux_vars": aux,
            "cnf_clauses": clauses, "cnf_literals": literals,
            "count_source": "exact_formula"}
