from .base_encoder import yield_all_lines, yield_alo


def generate_sequential_clauses(n: int, column_alo: bool = True):
    yield from yield_alo(n, column_alo)
    next_aux = n * n + 1
    for line in yield_all_lines(n):
        k = len(line)
        if k < 2:
            continue
        chain = range(next_aux, next_aux + k - 1)
        next_aux += k - 1
        yield [-line[0], chain[0]]
        yield [-line[-1], -chain[-1]]
        for i in range(1, k - 1):
            yield [-line[i], chain[i]]
            yield [-chain[i - 1], chain[i]]
            yield [-line[i], -chain[i - 1]]
