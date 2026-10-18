"""Điểm vào: python -m analysis --input results/experiment_02 --output report."""
import argparse
import json
from pathlib import Path
from .data_processing import load_experiment, export_data, work_time, require


def main(argv=None):
    parser = argparse.ArgumentParser(description="Tái tạo bảng và hình từ kết quả N-Queens đã chạy.")
    parser.add_argument("--input", type=Path, default=Path("results/experiment_02"), help="Thư mục có CSV, JSONL, manifest và summary.")
    parser.add_argument("--output", type=Path, default=Path("report"), help="Thư mục nhận data dẫn xuất, tables và figures.")
    parser.add_argument("--figure", choices=["formula_sizes", "sat_runtime", "native_runtime", "memory", "status_matrix", "cactus", "sat_iqr", "phase_breakdown"], help="Chỉ vẽ một hình; bỏ tùy chọn này để tạo toàn bộ bảng và hình.")
    parser.add_argument("--inspect", nargs=2, metavar=("N", "METHOD"), help="In các lượt và trung vị của một nhóm; không ghi tệp.")
    args = parser.parse_args(argv)
    try:
        report = load_experiment(args.input)
        audit = report["audit"]
        print(f"Đã kiểm tra {audit['rows']} lượt, {audit['groups']} nhóm: {audit['statuses']}")
        if args.inspect:
            n, method = int(args.inspect[0]), args.inspect[1]
            require((n, method) in report["groups"], f"Không có nhóm N={n}, phương pháp={method}.")
            rows = []
            for row in sorted(report["groups"][n, method], key=lambda r: r["repetition"]):
                rows.append({**{k: row.get(k) for k in ["run_id", "repetition", "status", "build_s", "load_s", "solve_s", "total_s", "peak_rss_mib"]},
                             "completed_work_s": work_time(row) if row["status"] == "SAT" else None})
            print(json.dumps({"runs": rows, "summary": report["summary"][n, method]}, ensure_ascii=False, indent=2))
            return 0
        export_data(report, args.output)
        if not args.figure:
            from .tables import create_tables
            create_tables(report, args.output)
            print("Đã tạo các bảng thực nghiệm trong tables/.")
        from .plots import create_figures
        create_figures(report, args.output, args.figure)
        print(f"Kết quả ở: {args.output.resolve()}")
        return 0
    except (ValueError, KeyError, OSError) as error:
        parser.exit(2, f"Dừng để kiểm tra đầu vào: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
