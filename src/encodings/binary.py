from .base_encoder import yield_all_lines, yield_alo


def generate_binary_clauses(n: int, column_alo: bool = True):
    yield from yield_alo(n, column_alo)
    next_aux = n * n + 1
    for line in yield_all_lines(n):
        if len(line) < 2:
            continue
        bits = (len(line) - 1).bit_length()
        signed_bits = [(1 << j, next_aux + j, -next_aux - j) for j in range(bits)]
        next_aux += bits
        for index, var in enumerate(line):
            neg_var = -var
            for mask, pos, neg in signed_bits:
                yield [neg_var, pos if index & mask else neg]
    