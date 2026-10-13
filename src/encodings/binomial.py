from itertools import combinations
from .base_encoder import yield_all_lines, yield_alo


def generate_binomial_clauses(n: int, column_alo: bool = True):
    yield from yield_alo(n, column_alo)
    for line in yield_all_lines(n):
        for a, b in combinations(line, 2):
            yield [-a, -b]
