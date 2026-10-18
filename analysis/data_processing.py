"""Đọc dữ liệu, kiểm tra và tính thống kê; chưa vẽ hoặc gọi solver.

Thứ tự đọc gợi ý: load_experiment -> summarize_group -> export_data.
JSONL giữ đúng kiểu số/list/bool; từng trường CSV được đối chiếu với JSONL.
"""
from collections import Counter, defaultdict
from functools import lru_cache
from math import isqrt, isfinite
from pathlib import Path
from statistics import median, quantiles, geometric_mean
import csv
import hashlib
import json

SAT = ["Binomial", "Binary", "Sequential", "Commander", "Product"]
NATIVE = ["cp_sat", "cplex_cp", "cplex_mip", "gurobi"]
METHODS = SAT + NATIVE
LABEL = {**{m: m for m in SAT}, "cp_sat": "CP-SAT", "cplex_cp": "CPLEX CP",
         "cplex_mip": "CPLEX MIP", "gurobi": "Gurobi"}
COLORS = dict(zip(METHODS, ["#0072B2", "#E69F00", "#009E73", "#D55E00",
                           "#CC79A7", "#56B4E9", "#222222", "#8B6914", "#6A51A3"]))
REPORT_EXPERIMENT = "20261015T101136Z_afe2720f"
REPORT_SIZES = [4, 8, 9, 16, 25, 27, 36, 49, 64, 81, 100, 125,
                216, 343, 512, 729, 1000, 1331]


def require(condition, message):
    """Lỗi dữ liệu phải dừng rõ ràng, kể cả khi Python chạy với -O."""
    if not condition:
        raise ValueError(message)


def pair(k):
    return k * (k - 1) // 2


@lru_cache(maxsize=None)
def amo_counts(k, encoding):
    """Số (biến phụ, clause, literal) của một nhóm AMO, đúng biến thể mới."""
    if k <= 1:
        return 0, 0, 0
    if encoding == "Binomial":
        return 0, pair(k), 2 * pair(k)
    if encoding == "Binary":
        bits = (k - 1).bit_length()
        return bits, k * bits, 2 * k * bits
    if encoding == "Sequential":
        aux, clauses = (0, pair(k)) if k <= 3 else (k - 1, 3 * k - 4)
        return aux, clauses, 2 * clauses
    if encoding == "Commander":
        if k <= 3:
            return 0, pair(k), 2 * pair(k)
        groups = (k + 2) // 3
        inside = 3 * (k // 3) + pair(k % 3)
        aux, clauses, literals = amo_counts(groups, encoding)
        return (groups + aux, inside + k + groups + clauses,
                2 * inside + 3 * k + groups + literals)
    if encoding == "Product":
        if k <= 4:
            return 0, pair(k), 2 * pair(k)
        p = isqrt(k - 1) + 1
        q = (k + p - 1) // p
        ar, cr, lr = amo_counts(p, encoding)
        ac, cc, lc = amo_counts(q, encoding)
        return p + q + ar + ac, 2 * k + cr + cc, 4 * k + lr + lc
    raise ValueError(f"Encoding chưa được hỗ trợ: {encoding}")


def counts(n, encoding, column_alo=True):
    """Ghép chi phí các nhóm thành CNF đầy đủ; không phải số đã sinh trước timeout."""
    aux = 0
    clauses = n * (1 + bool(column_alo))
    literals = n * n * (1 + bool(column_alo))
    for k in range(2, n + 1):
        multiplicity = 2 * n + 2 if k == n else 4
        a, c, lit = amo_counts(k, encoding)
        aux += multiplicity * a
        clauses += multiplicity * c
        literals += multiplicity * lit
    return dict(primary_vars=n*n, aux_vars=aux, total_vars=n*n+aux,
                cnf_clauses=clauses, cnf_literals=literals)


def find_input(folder, names):
    """Chấp nhận tên tệp trên máy người dùng hoặc tên trong gói LaTeX."""
    matches = [folder / name for name in names if (folder / name).is_file()]
    require(len(matches) == 1,
            f"Cần đúng một tệp trong {names} tại {folder}; thấy {len(matches)} tệp.")
    return matches[0]


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows):
    """CSV đầu ra dùng UTF-8 BOM để Excel trên Windows đọc tiếng Việt."""
    path.parent.mkdir(parents=True, exist_ok=True)
    require(bool(rows), f"Không có dữ liệu để ghi {path.name}")
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def verify_csv_jsonl(csv_rows, raw):
    """Đối chiếu theo run_id, không phụ thuộc thứ tự các dòng trong hai tệp."""
    by_id = {r["run_id"]: r for r in raw}
    csv_ids = [r["run_id"] for r in csv_rows]
    require(len(by_id) == len(raw), "JSONL có run_id trùng.")
    require(len(set(csv_ids)) == len(csv_ids), "CSV có run_id trùng.")
    require(set(csv_ids) == set(by_id), "CSV và JSONL không có cùng tập run_id.")
    for row in csv_rows:
        original = by_id[row["run_id"]]
        for key, text in row.items():
            expected = original.get(key)
            if expected is None:
                equal = text == ""
            elif isinstance(expected, (dict, list)):
                equal = json.loads(text) == expected
            elif isinstance(expected, bool):
                equal = text == str(expected)
            elif isinstance(expected, (int, float)):
                equal = float(text) == expected
            else:
                equal = text == str(expected)
            require(equal, f"CSV/JSONL khác nhau ở {row['run_id']}, cột {key}.")


def group_status(rows):
    """Nhóm ba lượt phải giữ riêng kết quả chưa hoàn tất và thành công một phần."""
    require(len(rows) == 3, "Báo cáo này yêu cầu đúng ba lần lặp mỗi nhóm.")
    status = Counter(r["status"] for r in rows)
    if status == Counter(SAT=3):
        return "SAT"
    if status == Counter(TIMEOUT=3):
        return "TO"
    if status == Counter(TIMEOUT=2, UNKNOWN=1):
        return "2TO+1U"
    if status == Counter(SAT=1, TIMEOUT=2):
        return "1S+2TO"
    raise ValueError(f"Nhóm có trạng thái ngoài phạm vi báo cáo hiện tại: {status}")


def work_time(row):
    """Cộng TRONG một lượt. Native không có pha load riêng."""
    return row["build_s"] + (row.get("load_s") or 0) + row["solve_s"]


def summarize_group(n, method, rows):
    """Tính một dòng tổng hợp từ ba lần lặp của cùng N và phương pháp."""
    status = group_status(rows)
    completed = [r for r in rows if r["status"] == "SAT"]
    full = status == "SAT"
    result = dict(n=n, method=method, status=status, sat_runs=len(completed),
                  timeout_runs=sum(r["status"] == "TIMEOUT" for r in rows),
                  unknown_runs=sum(r["status"] == "UNKNOWN" for r in rows))
    for field in ["build_s", "load_s", "solve_s", "startup_s", "setup_s", "total_s"]:
        values = [r.get(field) for r in rows]
        result["median_" + field] = median(values) if full and all(v is not None for v in values) else None

    # Chỉ có thời gian hoàn tất của cả nhóm khi đủ 3/3 lượt SAT.
    work = [work_time(r) for r in completed]
    result["median_work_s"] = median(work) if full else None
    quartiles = quantiles(work, n=4, method="inclusive") if full else None
    result["q1_work_s"] = quartiles[0] if full else None
    result["q3_work_s"] = quartiles[2] if full else None
    # Hai cột dưới để kiểm tra riêng lượt thành công; KHÔNG dùng cho bảng thời gian chính.
    result["median_completed_work_s"] = median(work) if work else None
    result["median_completed_total_s"] = median(r["total_s"] for r in completed) if completed else None
    # RAM vẫn là số đo quan sát hợp lệ khi timeout, nhưng phải đánh dấu trên hình.
    result["median_peak_rss_mib"] = median(r["peak_rss_mib"] for r in rows)
    for field in ["primary_vars", "aux_vars", "cnf_clauses", "cnf_literals", "native_vars", "native_constraints"]:
        result[field] = rows[0].get(field)
    result["total_sat_vars"] = result["primary_vars"] + result["aux_vars"] if method in SAT else None
    return result


def load_experiment(input_dir):
    """Kiểm tra bốn đầu vào và tổng hợp đúng đợt được phân tích trong báo cáo."""
    folder = Path(input_dir).resolve()
    files = {
        "experiment_results.csv": find_input(folder, ["experiment_results.csv", "experiment_results(2).csv"]),
        "results.jsonl": find_input(folder, ["results.jsonl"]),
        "manifest.json": find_input(folder, ["manifest.json"]),
        "summary_runner.csv": find_input(folder, ["summary.csv", "summary_runner.csv", "summary(1).csv"]),
    }
    manifest = json.loads(files["manifest.json"].read_text(encoding="utf-8-sig"))
    config = manifest["config"]
    require(manifest["experiment_id"] == REPORT_EXPERIMENT,
            "Đây là mã tái tạo báo cáo đợt 20261015. Đợt khác cần rà lại các phân tích chuyên biệt.")
    require(config["sizes"] == REPORT_SIZES and config["num_runs"] == 3, "Kích thước/số lần lặp không khớp báo cáo.")
    require(set(config["encodings"]) == set(SAT), "Không đủ năm mã hóa SAT.")
    require(set(config["solvers"]) == {"sat", *NATIVE}, "Không đủ năm nhóm bộ giải.")
    require(config["max_clauses"] == 0 and config["column_alo"] is True, "Cấu hình clause/ALO không khớp.")
    for method, description in {
        "Commander": "recursive_groups_3_pairwise_base_3_reverse_links",
        "Product": "recursive_coordinates_pairwise_base_4",
        "Sequential": "sinz_pairwise_base_3",
    }.items():
        require(manifest["encoding_definitions"][method] == description, f"Biến thể {method} không khớp.")
    raw = [json.loads(line) for line in files["results.jsonl"].read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    verify_csv_jsonl(read_csv(files["experiment_results.csv"]), raw)
    expected = {(n, s, e, repetition) for n in config["sizes"] for s in config["solvers"]
                for e in (config["encodings"] if s == "sat" else [None]) for repetition in range(1, 4)}
    actual = {(r["n"], r["solver"], r["encoding"], r["repetition"]) for r in raw}
    require(actual == expected and len(raw) == len(expected), "Thiếu hoặc trùng lượt trong lưới thực nghiệm.")

    groups = defaultdict(list)
    valid = clause_matches = formula_rows = 0
    for row in raw:
        for key in ["experiment_id", "code_hash", "config_hash"]:
            require(row[key] == manifest[key], f"Trộn dữ liệu khác {key}.")
        require(row["max_clauses"] == 0 and row["time_limit_s"] == 100 and row["memory_limit_mib"] == 6144, "Giới hạn tài nguyên không khớp.")
        require(row.get("memory_access_errors") == 0 and not row.get("cleanup_warning"), "Có lỗi đo RAM hoặc dọn worker cần kiểm tra.")
        require(row["status"] in {"SAT", "TIMEOUT", "UNKNOWN"}, "Xuất hiện trạng thái ngoài đợt đã phân tích.")
        require(isfinite(row["total_s"]) and isfinite(row["peak_rss_mib"]) and row["peak_rss_mib"] >= 0, "Thời gian/RAM không hợp lệ.")
        method = row["encoding"] if row["solver"] == "sat" else row["solver"]
        groups[row["n"], method].append(row)
        if row["status"] == "SAT":
            n, q = row["n"], row["solution_cols"]
            require(len(q) == n and all(type(x) is int and 0 <= x < n for x in q), "Vector nghiệm sai miền.")
            require(len(set(q)) == len({i+x for i, x in enumerate(q)}) == len({i-x for i, x in enumerate(q)}) == n, "Nghiệm có hai hậu tấn công.")
            require(row["solution_valid"] is True and row["phase_timings_complete"] is True, "Nghiệm/pha thời gian chưa được xác nhận.")
            require(work_time(row) <= row["total_s"] + 1e-6, "Work lớn hơn total.")
            valid += 1
        if method in SAT:
            formula_rows += 1
            formula = counts(row["n"], method)
            for field in ["primary_vars", "aux_vars", "cnf_clauses", "cnf_literals"]:
                require(row[field] == formula[field], f"Số đếm không khớp: N={row['n']}, {method}, {field}.")
            require(row["count_source"] == "exact_formula", "Nguồn số đếm không khớp.")
            if row["status"] == "SAT":
                require(row["clauses_generated"] == row["clauses_loaded"] == row["cnf_clauses"], "Lượt SAT chưa nạp đủ CNF.")
                clause_matches += 1
        elif row["status"] == "SAT":
            n = row["n"]
            require(row["native_vars"] == (n if method in ["cp_sat", "cplex_cp"] else n*n), "Số biến native không khớp.")
            require(row["native_constraints"] == (3 if method in ["cp_sat", "cplex_cp"] else 6*n-2), "Số ràng buộc native không khớp.")

    summary = {key: summarize_group(*key, rows) for key, rows in sorted(groups.items())}
    supplied = read_csv(files["summary_runner.csv"])
    require(len(supplied) == len(summary), "Summary của runner thiếu nhóm.")
    seen = set()
    for row in supplied:
        method = row["encoding"] if row["solver"] == "sat" else row["solver"]
        key = int(row["n"]), method
        require(key not in seen, "Summary của runner trùng nhóm.")
        seen.add(key)
        result = summary[key]
        require(int(row["completed"]) == result["sat_runs"] and int(row["timeout"]) == result["timeout_runs"] and int(row["unknown"]) == result["unknown_runs"], "Summary trạng thái không khớp dữ liệu thô.")
        require(int(row["skipped"]) == int(row["errors"]) == int(row["mem_limit"]) == 0, "Summary có trạng thái không khớp đợt này.")
        require((float(row["median_total_s"]) if row["median_total_s"] else None) == result["median_total_s"], "Trung vị runner không khớp.")

    sizes = config["sizes"]
    coverage = []
    for method in METHODS:
        status = Counter(r["status"] for (n, m), g in groups.items() if m == method for r in g)
        coverage.append(dict(method=method,
            solved_all=sum(summary[n, method]["status"] == "SAT" for n in sizes),
            solved_any=sum(summary[n, method]["sat_runs"] > 0 for n in sizes),
            SAT=status["SAT"], TIMEOUT=status["TIMEOUT"], UNKNOWN=status["UNKNOWN"]))
    pairs = []
    for method in SAT[1:]:
        common = [n for n in sizes if summary[n, method]["status"] == summary[n, "Binomial"]["status"] == "SAT"]
        ratios = [summary[n, "Binomial"]["median_work_s"] / summary[n, method]["median_work_s"] for n in common]
        pairs.append(dict(method=method, matched=len(common), wins=sum(x > 1 for x in ratios),
                          losses=sum(x < 1 for x in ratios), geometric_speedup=geometric_mean(ratios)))
    common = [n for n in sizes if all(summary[n, m]["status"] == "SAT" for m in METHODS)]
    winners = {metric: {n: min(METHODS, key=lambda m: summary[n, m]["median_"+metric+"_s"]) for n in common}
               for metric in ["work", "total"]}
    timeouts = [r for r in raw if r["solver"] == "sat" and r["status"] == "TIMEOUT"]
    audit = dict(experiment_id=manifest["experiment_id"], code_hash=manifest["code_hash"], config_hash=manifest["config_hash"],
        raw_sha256={name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items()},
        rows=len(raw), groups=len(groups), csv_jsonl_equal=True, summary_runner_matches=True, expected_jobs_match=True,
        statuses=dict(Counter(r["status"] for r in raw)), valid_solutions=valid, sat_formula_rows=formula_rows,
        completed_sat_clause_matches=clause_matches,
        timeout_sat_fully_loaded=sum(r["clauses_loaded"] == r["cnf_clauses"] for r in timeouts),
        timeout_sat_not_fully_loaded=sum(r["clauses_loaded"] != r["cnf_clauses"] for r in timeouts),
        full_groups=sum(r["status"] == "SAT" for r in summary.values()),
        partial_groups=sum(0 < r["sat_runs"] < 3 for r in summary.values()),
        no_success_groups=sum(r["sat_runs"] == 0 for r in summary.values()),
        common_all_n=common, pairwise_binomial=pairs, winners=winners,
        max_rss_mib=max(r["peak_rss_mib"] for r in raw), memory_access_errors=0, cleanup_warnings=0,
        unknown_rows=[{k: r.get(k) for k in ["n", "solver", "repetition", "total_s", "native_status", "termination_reason"]} for r in raw if r["status"] == "UNKNOWN"])
    return dict(manifest=manifest, files=files, raw=raw, sizes=sizes, groups=groups,
                summary=summary, coverage=coverage, pairs=pairs, common=common, winners=winners, audit=audit)


def export_data(report, output_dir):
    """Ghi số liệu dẫn xuất; bốn tệp đầu vào không bị thay đổi."""
    target = Path(output_dir) / "data"
    write_csv(target / "summary_report.csv", list(report["summary"].values()))
    formulas = [dict(n=n, encoding=m, **counts(n, m)) for n in report["sizes"] for m in SAT]
    write_csv(target / "cnf_formula_counts.csv", formulas)
    write_csv(target / "coverage.csv", report["coverage"])
    write_csv(target / "pairwise_binomial.csv", report["pairs"])
    target.mkdir(parents=True, exist_ok=True)
    (target / "data_audit.json").write_text(json.dumps(report["audit"], ensure_ascii=False, indent=2), encoding="utf-8")
