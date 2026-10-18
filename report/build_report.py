"""Lệnh tiện dụng cho gói LaTeX độc lập: python build_report.py.

Trong repository, analysis/ ở cạnh report/.
Trong gói LaTeX, analysis/ được đóng kèm cạnh tệp này từ cùng bộ mã nguồn.
"""
from pathlib import Path
import sys

here = Path(__file__).resolve().parent
if not (here / "analysis").is_dir():
    sys.path.insert(0, str(here.parent))
from analysis.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main(["--input", str(here / "data"), "--output", str(here)]))
