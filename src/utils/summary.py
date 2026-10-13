"""Summaries keep censored/failed runs visible; never rank errors as fast solves."""
import csv
from collections import Counter, defaultdict
from statistics import median, quantiles


def summarize(records):
    groups = defaultdict(list)
    # Keep only the latest completed record for a run_id if recovering old interrupted records.
    unique = {}
    for index, record in enumerate(records):
        unique[record.get("run_id", index)] = record
    for record in unique.values():
        key = tuple(record.get(k) for k in ("n", "solver", "encoding", "sat_solver", "column_alo"))
        groups[key].append(record)
    rows = []
    for key, records in sorted(groups.items(), key=lambda item: str(item[0])):
        counts = Counter(r["status"] for r in records)
        complete = [r for r in records if r["status"] in ("SAT", "UNSAT")]
        times = [r["total_s"] for r in complete]
        q1 = q3 = None
        if len(times) >= 2:
            q1, _, q3 = quantiles(times, n=4, method="inclusive")
        row = dict(zip(("n", "solver", "encoding", "sat_solver", "column_alo"), key))
        row.update(num_runs=len(records), completed=len(complete),
                   completion_rate=len(complete) / len(records),
                   sat=counts["SAT"], unsat=counts["UNSAT"], timeout=counts["TIMEOUT"],
                   mem_limit=counts["MEM_LIMIT"], errors=counts["ERROR"],
                   unknown=counts["UNKNOWN"], skipped=counts["SKIPPED"],
                   median_total_s=median(times) if len(times) == len(records) else None,
                   median_completed_total_s=median(times) if times else None,
                   q1_completed_total_s=q1, q3_completed_total_s=q3,
                   median_completed_solve_s=median([r["solve_s"] for r in complete
                                                   if r.get("solve_s") is not None])
                       if any(r.get("solve_s") is not None for r in complete) else None,
                   median_peak_rss_mib=median([r["peak_rss_mib"] for r in records
                                              if r.get("peak_rss_mib") is not None])
                       if any(r.get("peak_rss_mib") is not None for r in records) else None)
        rows.append(row)
    return rows


def write_summary(records, path):
    rows = summarize(records)
    if not rows:
        return
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
