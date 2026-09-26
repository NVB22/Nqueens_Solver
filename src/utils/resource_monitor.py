import os
import psutil

def get_current_ram_mb() -> float:
    """Trả về dung lượng RAM đang sử dụng (MB) của tiến trình hiện tại."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)