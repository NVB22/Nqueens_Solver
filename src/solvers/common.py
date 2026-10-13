import time
from contextlib import contextmanager
from importlib.metadata import PackageNotFoundError, version
from src.utils.validation import validate_solution


def package_version(name):
    try:
        return version(name)
    except PackageNotFoundError:
        return None


class BudgetExpired(TimeoutError):
    pass


class Measurements:
    """Accumulate phase times and emit bounded progress messages."""
    def __init__(self, deadline, emit):
        self.deadline, self.emit = deadline, emit
        self.last_emit = 0.0
        self.data = {"setup_s": 0.0, "build_s": 0.0, "load_s": None,
                     "solve_s": 0.0, "decode_validate_s": 0.0,
                     "phase": "setup", "phase_timings_complete": False}

    def remaining(self):
        left = self.deadline - time.perf_counter()
        if left <= 0:
            raise BudgetExpired("End-to-end time budget exhausted")
        return left

    def progress(self, force=False):
        now = time.perf_counter()
        if force or now - self.last_emit >= 0.25:
            self.emit({"type": "progress", "data": dict(self.data)})
            self.last_emit = now

    @contextmanager
    def phase(self, key):
        self.remaining()
        self.data["phase"] = key.removesuffix("_s")
        self.progress()
        start = time.perf_counter()
        try:
            yield
        finally:
            self.data[key] = (self.data.get(key) or 0.0) + time.perf_counter() - start

    def solution(self, cols, n):
        if not validate_solution(cols, n):
            raise ValueError("Solver returned an invalid N-Queens solution")
        return {"status": "SAT", "termination_reason": "COMPLETED",
                "solution_valid": True, "solution_cols": cols}


def cplex_mip_status(status_text, has_solution):
    text = (status_text or "").lower()
    if has_solution:
        return "SAT", "NATIVE_TIME_LIMIT" if "time limit" in text else "COMPLETED"
    if "infeasible" in text and "unbounded" not in text:
        return "UNSAT", "COMPLETED"
    if "time limit" in text:
        return "TIMEOUT", "NATIVE_TIME_LIMIT"
    return "UNKNOWN", "NATIVE_STOP"
