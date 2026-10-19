"""Tách trạng thái lượt chạy khỏi bằng chứng về từng phép đo.

Không suy ra thời gian giải bằng total - build - load. Không dùng nhãn
phase làm bằng chứng pha hoàn tất: nhãn trong thông báo cuối có thể cũ.
"""
from math import isfinite
from statistics import median

PHASE_FIELDS = ("build_s", "load_s", "solve_s", "startup_s", "setup_s")
OBSERVED_FIELDS = PHASE_FIELDS + ("total_s",)


def observation(row, field):
    """Trả (số giây sử dụng được, loại bằng chứng); giữ nguyên số gốc ở nơi khác.

    final: bản ghi xác nhận phase_timings_complete.
    last_update: số dương có thật, nhưng chưa xác nhận phép đo cuối cùng.
    elapsed: thời gian toàn lượt đến khi kết thúc/dừng, không phải thời gian
             cần để tìm nghiệm khi lượt đó chưa giải thành công.
    unavailable: thiếu số đo hoặc 0 chưa được xác nhận, không có nghĩa 0 giây.
    not_measured: native không đo riêng load.
    """
    if field == "load_s" and row["solver"] != "sat":
        return None, "not_measured"
    value = row.get(field)
    if value is None:
        return None, "unavailable"
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
        raise ValueError(f"Số đo không hợp lệ: {row.get('run_id')}, {field}={value!r}")
    if field == "total_s":
        return value, "elapsed"
    if row.get("phase_timings_complete") is True:
        return value, "final"
    # Runner cũ khởi tạo các đồng hồ chưa cập nhật bằng 0. Không thể phân biệt
    # một số 0 thực với giá trị khởi tạo nếu chưa có xác nhận hoàn tất phép đo.
    if value == 0:
        return None, "unavailable"
    return value, "last_update"


def summarize_measurement(rows, field):
    """Trung vị những số đo có thật; luôn trả cả mẫu số và chất lượng mẫu.

    Nếu chỉ có 1/3 lượt có số đo, trung vị này mô tả đúng 1 lượt đó,
    không phải trung vị của cả ba lượt hay thời gian để giải thành công.
    """
    observations = [observation(row, field) for row in rows]
    values = [value for value, kind in observations if value is not None]
    kinds = {kind for value, kind in observations if value is not None}
    if len(kinds) == 1:
        quality = next(iter(kinds))
    elif kinds:
        quality = "mixed"
    elif all(kind == "not_measured" for _, kind in observations):
        quality = "not_measured"
    else:
        quality = "unavailable"
    return dict(
        median_s=median(values) if values else None,
        runs_used=len(values), total_runs=len(rows),
        final_runs=sum(kind == "final" for _, kind in observations),
        last_update_runs=sum(kind == "last_update" for _, kind in observations),
        missing_runs=sum(kind == "unavailable" for _, kind in observations),
        not_measured_runs=sum(kind == "not_measured" for _, kind in observations),
        quality=quality,
    )


def measurement_rows(report):
    """Dữ liệu dài: truy ngược mỗi số tổng hợp về run_id và số gốc."""
    result = []
    for row in sorted(report["raw"], key=lambda r: (r["n"], r["solver"], r.get("encoding") or "", r["repetition"])):
        for field in OBSERVED_FIELDS:
            value, quality = observation(row, field)
            result.append(dict(
                n=row["n"], method=row["encoding"] if row["solver"] == "sat" else row["solver"],
                repetition=row["repetition"], run_id=row["run_id"],
                run_status=row["status"], termination_reason=row.get("termination_reason"),
                field=field, raw_seconds=row.get(field), usable_seconds=value,
                quality=quality, phase_timings_complete=row.get("phase_timings_complete"),
                last_reported_phase=row.get("phase"),
                cnf_clauses=row.get("cnf_clauses"),
                clauses_generated=row.get("clauses_generated"), clauses_loaded=row.get("clauses_loaded"),
                all_clauses_generated=(row.get("clauses_generated") == row.get("cnf_clauses")) if row["solver"] == "sat" else None,
                all_clauses_loaded=(row.get("clauses_loaded") == row.get("cnf_clauses")) if row["solver"] == "sat" else None,
            ))
    return result


def phase_summary_rows(report):
    return [dict(n=n, method=method, group_status=report["summary"][n, method]["status"],
                 field=field, **summarize_measurement(rows, field))
            for (n, method), rows in sorted(report["groups"].items())
            for field in OBSERVED_FIELDS]
