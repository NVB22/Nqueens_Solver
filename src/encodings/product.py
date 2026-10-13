from itertools import combinations, product
from math import isqrt
from .base_encoder import yield_all_lines, yield_alo


def generate_product_clauses(n: int, column_alo: bool = True):
    yield from yield_alo(n, column_alo)
    next_aux = n * n + 1
    for line in yield_all_lines(n):
        k = len(line)
        if k < 2:
            continue
        p = isqrt(k - 1) + 1
        q = (k + p - 1) // p
        rows = range(next_aux, next_aux + p)
        next_aux += p
        cols = range(next_aux, next_aux + q)
        next_aux += q
        for a, b in combinations(rows, 2):
            yield [-a, -b]
        for a, b in combinations(cols, 2):
            yield [-a, -b]
        for var, (row_aux, col_aux) in zip(line, product(rows, cols)):
            neg_var = -var
            yield [neg_var, row_aux]
            yield [neg_var, col_aux]
