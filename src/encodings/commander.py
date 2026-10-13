from itertools import combinations
from math import isqrt
from .base_encoder import yield_all_lines, yield_alo


def generate_commander_clauses(n: int, column_alo: bool = True):
    yield from yield_alo(n, column_alo)
    next_aux = n * n + 1
    for line in yield_all_lines(n):
        k = len(line)
        if k < 2:
            continue
        group_size = isqrt(k)
        groups = [line[i:i + group_size] for i in range(0, k, group_size)]
        commanders = range(next_aux, next_aux + len(groups))
        next_aux += len(groups)
        for a, b in combinations(commanders, 2):
            yield [-a, -b]
        for commander, group in zip(commanders, groups):
            yield [-commander, *group]
            for a, b in combinations(group, 2):
                yield [-commander, -a, -b]
            for var in group:
                yield [commander, -var]
