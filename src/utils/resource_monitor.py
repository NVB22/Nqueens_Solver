import os
import signal
import psutil


def get_current_ram_mb():
    return psutil.Process().memory_info().rss / (1024 ** 2)


class ProcessTreeMonitor:
    def __init__(self, pid):
        self.root = psutil.Process(pid)
        self.known = {pid: self.root}
        self.peak_mib = 0.0
        self.samples = 0
        self.access_errors = 0

    def sample(self):
        try:
            for p in self.root.children(recursive=True):
                self.known[p.pid] = p
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            self.access_errors += 1
        total = 0
        for p in list(self.known.values()):
            try:
                if p.is_running():
                    total += p.memory_info().rss
            except psutil.NoSuchProcess:
                pass
            except psutil.AccessDenied:
                self.access_errors += 1
        self.samples += 1
        self.peak_mib = max(self.peak_mib, total / (1024 ** 2))
        return total / (1024 ** 2)

    def stop(self):
        try:
            self.root.suspend()
        except psutil.Error:
            pass
        try:
            for p in self.root.children(recursive=True):
                self.known[p.pid] = p
        except psutil.Error:
            pass
        if os.name == "posix":
            try:
                if os.getpgid(self.root.pid) == self.root.pid:
                    os.killpg(self.root.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        for p in reversed(list(self.known.values())):
            try:
                p.kill()
            except psutil.Error:
                pass
        # multiprocessing owns waitpid() for the root; psutil must not reap it.
        descendants = [p for p in self.known.values() if p.pid != self.root.pid]
        _, alive = psutil.wait_procs(descendants, timeout=0.5)
        survivors = []
        for p in alive:
            try:
                if p.is_running() and p.status() != psutil.STATUS_ZOMBIE:
                    survivors.append(p.pid)
            except psutil.Error:
                pass
        return survivors
