"""Xuất bảng CSV để người viết tự trình bày trên Overleaf; không sinh LaTeX.

Số đo là số thực chưa làm tròn. Cột *_info đi ngay cạnh số đo để không đánh
đồng một trung vị 1/3 hoặc bản cập nhật cuối với phép đo hoàn tất 3/3.
"""
from pathlib import Path
from .data_processing import SAT, NATIVE, METHODS, LABEL, counts, require, write_csv
from .measurements import summarize_measurement, observation


def timing_cell(report, n, method, field):
    """Một ô thời gian và bằng chứng của ô, độc lập với trạng thái cả lượt."""
    rows = report["groups"][n, method]
    group = report["summary"][n, method]
    if field == "work_s":
        full = group["status"] == "SAT"
        # Đây là bảng so sánh thời gian hoàn tất, không cộng thời gian dở dang.
        measurement = dict(median_s=group["median_work_s"],
                           runs_used=len(rows) if full else 0, total_runs=len(rows),
                           final_runs=len(rows) if full else 0, last_update_runs=0,
                           missing_runs=0, not_measured_runs=0,
                           quality="final" if full else "needs_3_SAT")
    else:
        measurement = summarize_measurement(rows, field)
    detail = dict(n=n, method=method, field=field, group_status=group["status"],
                  sat_runs=group["sat_runs"], timeout_runs=group["timeout_runs"],
                  unknown_runs=group["unknown_runs"], **measurement)
    status_label = "3SAT" if group["status"] == "SAT" else "3TO" if group["status"] == "TO" else group["status"]
    info = f"{measurement['runs_used']}/{len(rows)};{measurement['quality']};{status_label}"
    return measurement["median_s"], info, detail


def create_tables(report, output_dir):
    """Ghi CSV bảng, danh mục và dữ liệu chứng minh từng ô thời gian."""
    destination = Path(output_dir) / "data" / "tables"
    catalog, details = [], []
    sizes, summary, groups = report["sizes"], report["summary"], report["groups"]

    def export(name, rows, title, unit="", old_table="", policy=""):
        write_csv(destination / (name + ".csv"), rows)
        catalog.append(dict(file="tables/" + name + ".csv", table_in_previous_pdf=old_table,
                            title=title, unit=unit, policy=policy))

    def time_columns(row, table, n, method, field, name, scale=1):
        value, info, detail = timing_cell(report, n, method, field)
        row[name] = value * scale if value is not None else None
        row[name + "_info"] = info
        details.append(dict(table=table, **detail))

    export("coverage", [dict(method=d["method"], label=LABEL[d["method"]],
           solved_all=d["solved_all"], solved_any=d["solved_any"], total_sizes=len(sizes),
           sat_runs=d["SAT"], timeout_runs=d["TIMEOUT"], unknown_runs=d["UNKNOWN"])
           for d in report["coverage"]], "Mức độ hoàn tất", old_table="7",
           policy="solved_all/solved_any đếm kích thước; *_runs đếm lượt.")

    definitions = [
        ("sat_work", SAT, "work_s", "Thời gian sinh + nạp + giải, nhóm đủ 3 SAT", "10"),
        ("sat_total", SAT, "total_s", "Thời gian toàn lượt đến khi kết thúc hoặc bị dừng", "11"),
        ("sat_build", SAT, "build_s", "Thời gian sinh CNF đã ghi nhận", "25"),
        ("sat_load", SAT, "load_s", "Thời gian nạp CNF đã ghi nhận", "26"),
        ("sat_solve", SAT, "solve_s", "Thời gian quanh lời gọi giải SAT đã ghi nhận", "27"),
        ("native_work", NATIVE, "work_s", "Thời gian xây mô hình + gọi giải, nhóm đủ 3 SAT", "16"),
        ("native_total", NATIVE, "total_s", "Thời gian toàn lượt CP/ILP đến khi kết thúc hoặc bị dừng", "17"),
        ("native_build", NATIVE, "build_s", "Thời gian xây mô hình CP/ILP đã ghi nhận", "28"),
        ("native_solve", NATIVE, "solve_s", "Thời gian quanh lời gọi giải CP/ILP đã ghi nhận", "29"),
    ]
    for name, methods, field, title, number in definitions:
        rows = []
        for n in sizes:
            row = dict(n=n)
            for method in methods:
                time_columns(row, name, n, method, field, method)
            rows.append(row)
        export(name, rows, title, "s", number,
               "Đọc cột *_info: số lượt có số đo/tổng lượt; chất lượng phép đo; trạng thái nhóm. "
               "Ô rỗng không phải 0 hay TIMEOUT của pha. Total bao gồm thời gian đến khi dừng. "
               "Work chỉ công bố trung vị khi đủ 3/3 SAT.")

    for name, key, number in [("variables", "total_vars", "8"), ("clauses", "cnf_clauses", "9")]:
        export(name, [dict(n=n, **{m: counts(n, m)[key] for m in SAT}) for n in sizes],
               "Kích thước CNF đầy đủ: " + key, "count", number,
               "Đếm theo công thức trước tiền xử lý, không gồm clause học; TIMEOUT không đổi số đếm.")

    for name, methods, number in [("sat_ram", SAT, "20"), ("native_ram", NATIVE, "21")]:
        rows = []
        for n in sizes:
            row = dict(n=n)
            for method in methods:
                row[method] = summary[n, method]["median_peak_rss_mib"]
                row[method + "_status"] = summary[n, method]["status"]
            rows.append(row)
        export(name, rows, "Trung vị đỉnh RSS quan sát của cả ba lượt", "MiB", number,
               "Bao gồm lượt bị ngắt; không phải RAM cần để mọi phương pháp giải thành công.")

    export("statuses", [dict(n=n, **{m: summary[n, m]["status"] for m in METHODS}) for n in sizes],
           "Trạng thái nhóm ba lượt", policy="SAT: 3 SAT; TO: 3 TIMEOUT; 2TO+1U; 1S+2TO.")
    small = []
    for method in SAT:
        row = dict(n=4, method=method)
        for field in ["startup_s", "setup_s", "work_s", "solve_s", "total_s"]:
            time_columns(row, "small_n", 4, method, field, field.replace("_s", "_ms"), scale=1000)
        small.append(row)
    export("small_n", small, "Thời gian thành phần tại N=4", "ms", "14",
           "Solve đã nằm trong Work. Các cột là trung vị riêng, không cộng chúng thành Total.")

    phase_rows = []
    for method in METHODS:
        row = dict(n=216, method=method, label=LABEL[method], group_status=summary[216, method]["status"])
        for field in ["build_s", "load_s", "solve_s", "work_s", "total_s"]:
            time_columns(row, "phase_216", 216, method, field, field)
        phase_rows.append(row)
    export("phase_216", phase_rows, "Các số đo tại N=216", "s", "15",
           "Build/Load/Solve giữ số đo có thật, kể cả khi cả lượt TIMEOUT. Work yêu cầu 3 SAT. "
           "last_update chưa xác nhận số đo cuối, kể cả khi đã nạp đủ CNF.")

    counter = []
    for method in SAT:
        group = groups[64, method]
        stats = [r["solver_stats"] for r in group]
        require(all(s == stats[0] for s in stats), "Các bộ đếm N=64 không giống nhau; cần rà lại bảng.")
        counter.append(dict(n=64, method=method, cnf_clauses=group[0]["cnf_clauses"],
                            median_solve_s=summary[64, method]["median_solve_s"],
                            conflicts=stats[0]["conflicts"], propagations=stats[0]["propagations"]))
    export("counterexample", counter, "Kích thước và công việc tìm kiếm tại N=64", old_table="13",
           policy="Bộ đếm giống nhau giữa 3 lượt; thời gian là trung vị 3 lượt.")
    export("pairwise_binomial", report["pairs"], "So sánh Work với Binomial trên tập chung đủ 3 SAT", old_table="12",
           policy="geometric_speedup > 1 nghĩa là nhanh hơn Binomial; tập so sánh khác nhau giữa các hàng.")
    export("matched_winners", [dict(method=m, label=LABEL[m], common_sizes=len(report["common"]),
           work_wins=sum(v == m for v in report["winners"]["work"].values()),
           total_wins=sum(v == m for v in report["winners"]["total"].values())) for m in METHODS],
           "Số kích thước có trung vị nhanh nhất trên tập mọi phương pháp đủ 3 SAT", old_table="18",
           policy="Tập chung: " + ", ".join(map(str, report["common"])))
    export("native_size", [dict(n=n, cp_vars=n, all_different=3, mip_vars=n*n, mip_constraints=6*n-2)
           for n in [4, 216, 1331]], "Kích thước mô hình native tại giao diện", "count", "19",
           "Không phải kích thước bên trong solver sau presolve; không quy AllDifferent thành một clause.")

    partial = []
    for source in sorted(groups[125, "Product"], key=lambda r: r["repetition"]):
        row = dict(n=125, method="Product", repetition=source["repetition"], run_id=source["run_id"],
                   status=source["status"], peak_rss_mib=source["peak_rss_mib"])
        for field in ["build_s", "load_s", "solve_s", "total_s"]:
            row[field], row[field + "_quality"] = observation(source, field)
        partial.append(row)
    export("partial_product", partial, "Từng lượt Product tại N=125", "s;MiB", "22",
           "Không dùng một lượt SAT làm đại diện cho trung vị hoàn tất của ba lượt.")

    timeouts = [r for r in report["raw"] if r["solver"] == "sat" and r["status"] == "TIMEOUT"]
    progress = []
    for method in SAT:
        group = [r for r in timeouts if r["encoding"] == method]
        loaded = sum(r["clauses_loaded"] == r["cnf_clauses"] for r in group)
        progress.append(dict(method=method, timeout_runs=len(group), reported_fully_loaded=loaded,
                             not_reported_fully_loaded=len(group)-loaded))
    export("timeout_progress", progress, "Tiến độ nạp của lượt SAT bị TIMEOUT", "runs", "23",
           "Tiến độ là bản cập nhật cuối; nạp đủ không chứng minh phép đo thời gian đã hoàn tất.")
    export("progress_1331", [dict(method=m, n=1331, cnf_clauses=counts(1331,m)["cnf_clauses"],
           loaded_min=min(r["clauses_loaded"] for r in groups[1331,m]),
           loaded_max=max(r["clauses_loaded"] for r in groups[1331,m]),
           group_status=summary[1331,m]["status"]) for m in SAT],
           "CNF đầy đủ và tiến độ nạp tại N=1331", "clauses", "24")

    dispersion = []
    for n in [4,64,81,216,512]:
        for method in SAT:
            group = summary[n,method]
            if group["status"] == "SAT":
                iqr = group["q3_work_s"] - group["q1_work_s"]
                dispersion.append(dict(n=n, method=method, median_work_s=group["median_work_s"],
                                       q1_s=group["q1_work_s"], q3_s=group["q3_work_s"],
                                       iqr_s=iqr, relative_iqr_percent=100*iqr/group["median_work_s"]))
    export("dispersion", dispersion, "Độ phân tán Work trên nhóm đủ 3 SAT", "s;%", "30",
           "Q1/Q3 nội suy inclusive; IQR không phải khoảng tin cậy.")
    export("encoding_n4", [dict(n=4,method=m,**counts(4,m)) for m in SAT],
           "Đối chiếu kích thước CNF tại N=4", "count", "3")
    write_csv(Path(output_dir)/"data"/"table_measurements.csv", details)
    write_csv(Path(output_dir)/"data"/"table_catalog.csv", catalog)
    return len(catalog)
