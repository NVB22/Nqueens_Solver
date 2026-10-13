"""Validate solutions independently of their SAT/CP/ILP models."""


def validate_solution(cols, n: int) -> bool:
    return (len(cols) == n and all(isinstance(c, int) and 0 <= c < n for c in cols)
            and len(set(cols)) == n
            and len({r + c for r, c in enumerate(cols)}) == n
            and len({r - c for r, c in enumerate(cols)}) == n)


def cells_to_columns(cells, n: int) -> list:
    cols = [-1] * n
    for row, col in cells:
        if not (0 <= row < n and 0 <= col < n) or cols[row] != -1:
            raise ValueError("Invalid cell or more than one queen in a row")
        cols[row] = col
    if not validate_solution(cols, n):
        raise ValueError("Solver returned an invalid N-Queens solution")
    return cols


def sat_to_columns(model, n: int) -> list:
    return cells_to_columns((divmod(lit - 1, n) for lit in model if 0 < lit <= n * n), n)
