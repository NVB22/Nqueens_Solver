"""Vẽ từng hình và lưu chính các điểm đã vẽ vào CSV để kiểm tra.

Mỗi hàm plot_* trả lời một câu hỏi, không gọi solver hoặc tạo số đo mới.
Đọc plot_runtime() trước để hiểu mẫu: chọn dữ liệu -> vẽ -> lưu PDF/PNG/CSV.
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # Chạy được trên Windows/server không có cửa sổ đồ họa.
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
from .data_processing import SAT, NATIVE, METHODS, LABEL, COLORS, counts, write_csv, require

TICKS = [4, 16, 64, 216, 512, 1331]


def style_axes(ax, log_y=False):
    """Trục N log giúp nhìn cả bàn cờ nhỏ và lớn; nhãn vẫn là N thật."""
    ax.set_xscale("log")
    ax.set_xticks(TICKS, labels=TICKS)
    if log_y:
        ax.set_yscale("log")
    ax.set_xlabel("N")
    ax.grid(alpha=0.22)


def save_figure(fig, name, points, output_dir):
    """PDF để chèn LaTeX, PNG để xem/GitHub, CSV để đối chiếu từng điểm."""
    output_dir = Path(output_dir)
    figure_dir = output_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    for extension in ["pdf", "png"]:
        fig.savefig(figure_dir / f"{name}.{extension}", dpi=180, bbox_inches="tight")
    plt.close(fig)
    write_csv(output_dir / "data" / "figure_points" / f"{name}.csv", points)


def draw_metric(ax, report, methods, metric, points, include_incomplete=False):
    """Nối các điểm trung vị. None -> NaN để không vẽ thời gian chưa biết."""
    for method in methods:
        selected = []
        for n in report["sizes"]:
            group = report["summary"][n, method]
            visible = include_incomplete or group["status"] == "SAT"
            value = group[metric] if visible else None
            point = dict(n=n, method=method, metric=metric, status=group["status"],
                         value=value, plotted=visible)
            selected.append(point)
            points.append(point)
        xs = [p["n"] for p in selected]
        ys = [p["value"] if p["value"] is not None else np.nan for p in selected]
        ax.plot(xs, ys, "o-", ms=3, lw=1.3, label=LABEL[method], color=COLORS[method])
    style_axes(ax)


def plot_formula_sizes(report, output_dir):
    """Câu hỏi: kích thước CNF của các mã hóa tăng như thế nào theo N?"""
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
    points = []
    for ax, metric, title in zip(axes, ["total_vars", "cnf_clauses"],
                                 ["(a) Variables", "(b) Input clauses"]):
        for method in SAT:
            values = [counts(n, method)[metric] for n in report["sizes"]]
            ax.plot(report["sizes"], values, lw=1.4, label=method, color=COLORS[method])
            for n, value in zip(report["sizes"], values):
                points.append(dict(n=n, method=method, metric=metric, value=value,
                                   count_source="exact_formula"))
        style_axes(ax, log_y=True)
        ax.set_title(title)
    fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center",
               bbox_to_anchor=(0.5, 1.07), ncol=5, frameon=False)
    save_figure(fig, "formula_sizes", points, output_dir)


def plot_runtime(report, output_dir, native=False):
    """Câu hỏi: cấu hình nào nhanh hơn theo work và theo total?"""
    name = "native_runtime" if native else "sat_runtime"
    methods = ["Binary", "Commander"] + NATIVE if native else SAT
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    points = []
    for ax, metric, title in zip(axes, ["median_work_s", "median_total_s"],
                                 ["(a) Model work", "(b) Whole-job elapsed time"]):
        draw_metric(ax, report, methods, metric, points)
        ax.set_yscale("log")
        ax.set_title(title)
        ax.set_ylabel("Seconds (median of 3 completed runs)")
    fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center",
               bbox_to_anchor=(0.5, 1.12), ncol=3 if native else 5, frameon=False)
    save_figure(fig, name, points, output_dir)


def plot_memory(report, output_dir):
    """Câu hỏi: đỉnh RAM quan sát tăng ra sao? x = nhóm chưa hoàn tất 3/3."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    points = []
    for ax, methods, title in zip(axes, [SAT, NATIVE], ["(a) SAT", "(b) CP and ILP"]):
        draw_metric(ax, report, methods, "median_peak_rss_mib", points, include_incomplete=True)
        for method in methods:
            ns = [n for n in report["sizes"] if report["summary"][n, method]["status"] != "SAT"]
            values = [report["summary"][n, method]["median_peak_rss_mib"] for n in ns]
            ax.scatter(ns, values, marker="x", s=45, color=COLORS[method], zorder=5)
        ax.set_yscale("log")
        ax.set_ylabel("Observed peak RSS (MiB; median of 3)")
        ax.set_title(title)
        ax.legend(fontsize=7.5, frameon=False)
    save_figure(fig, "memory", points, output_dir)


def plot_status_matrix(report, output_dir):
    """Câu hỏi: phương pháp nào hoàn tất ở N nào, và có thành công một phần không?"""
    codes = {"SAT": 0, "TO": 1, "2TO+1U": 2, "1S+2TO": 3}
    symbols = {"SAT": "S", "TO": "TO", "2TO+1U": "T/U", "1S+2TO": "1S/2T"}
    sizes = report["sizes"]
    matrix = [[codes[report["summary"][n, m]["status"]] for n in sizes] for m in METHODS]
    fig, ax = plt.subplots(figsize=(10, 3.7))
    ax.imshow(matrix, aspect="auto", cmap=ListedColormap(["#d8ead7", "#f3c4bf", "#ffe4a3", "#c7d7f1"]), vmin=0, vmax=3)
    points = []
    for i, method in enumerate(METHODS):
        for j, n in enumerate(sizes):
            status = report["summary"][n, method]["status"]
            ax.text(j, i, symbols[status], ha="center", va="center", fontsize=6.8)
            points.append(dict(n=n, method=method, status=status, color_code=codes[status]))
    ax.set_xticks(range(len(sizes)), labels=sizes, rotation=45)
    ax.set_yticks(range(len(METHODS)), labels=[LABEL[m] for m in METHODS])
    ax.set_xlabel("N")
    ax.set_title("S: 3 SAT   TO: 3 timeouts   T/U: 2 timeouts + 1 unknown   1S/2T: 1 SAT + 2 timeouts")
    save_figure(fig, "status_matrix", points, output_dir)


def plot_cactus(report, output_dir):
    """Trục x là thời gian, KHÔNG phải N; trục y là số kích thước đã giải đủ 3/3."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.7))
    points = []
    for panel, ax, methods, title in zip(["SAT", "native"], axes,
            [SAT, ["Binary"] + NATIVE], ["(a) SAT encodings", "(b) SAT versus CP/ILP"]):
        for method in methods:
            completed = [(report["summary"][n, method]["median_total_s"], n)
                         for n in report["sizes"] if report["summary"][n, method]["status"] == "SAT"]
            completed.sort()
            times = [t for t, n in completed]
            # Điểm đầu chỉ neo đường bậc thang ở số đã giải = 0; không phải số đo.
            ax.step([0.1] + times, [0] + list(range(1, len(times)+1)), where="post",
                    label=LABEL[method], color=COLORS[method], lw=1.5)
            points.append(dict(panel=panel, method=method, n=None, threshold_total_s=0.1,
                               solved_sizes=0, point_type="axis_anchor"))
            for rank, (time_s, n) in enumerate(completed, start=1):
                points.append(dict(panel=panel, method=method, n=n, threshold_total_s=time_s,
                                   solved_sizes=rank, point_type="completed_group"))
        ax.set_xscale("log")
        ax.set_xlim(0.4, 110)
        ax.set_ylim(0, 19)
        ax.set_yticks([0, 6, 12, 18])
        ax.set_xlabel("Whole-job median time (s)")
        ax.set_ylabel("Sizes completed in all 3 runs")
        ax.set_title(title)
        ax.grid(alpha=0.2)
        ax.legend(fontsize=7.5, frameon=False)
    save_figure(fig, "cactus", points, output_dir)


def plot_sat_iqr(report, output_dir):
    """Câu hỏi: ba lượt hoàn tất dao động thế nào? Q1-Q3 không là khoảng tin cậy."""
    fig, ax = plt.subplots(figsize=(9.8, 3.7))
    points = []
    for method in SAT:
        ns = [n for n in report["sizes"] if report["summary"][n, method]["status"] == "SAT"]
        groups = [report["summary"][n, method] for n in ns]
        ys = [g["median_work_s"] for g in groups]
        lower = [g["median_work_s"] - g["q1_work_s"] for g in groups]
        upper = [g["q3_work_s"] - g["median_work_s"] for g in groups]
        ax.errorbar(ns, ys, yerr=[lower, upper], fmt="o-", ms=3, lw=1.1,
                    capsize=2, label=method, color=COLORS[method])
        for n, group in zip(ns, groups):
            points.append(dict(n=n, method=method, median_work_s=group["median_work_s"],
                               q1_work_s=group["q1_work_s"], q3_work_s=group["q3_work_s"]))
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("N")
    ax.set_ylabel("Build + load + solve (s)")
    ax.grid(alpha=0.2)
    ax.legend(ncol=5, loc="upper left", fontsize=8, frameon=False)
    save_figure(fig, "sat_iqr", points, output_dir)


def plot_phase_breakdown(report, output_dir):
    """Chọn đúng một lượt có total trung vị; không chồng trung vị từng pha."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    fields = ["startup_s", "setup_s", "build_s", "load_s", "solve_s", "decode_validate_s"]
    colors = ["#bdbdbd", "#8c8c8c", "#56B4E9", "#0072B2", "#E69F00", "#009E73", "#eeeeee"]
    points = []
    for ax, n in zip(axes, [4, 216]):
        methods = [m for m in METHODS if report["summary"][n, m]["status"] == "SAT"]
        chosen = [sorted(report["groups"][n, m], key=lambda row: row["total_s"])[1] for m in methods]
        bottom = np.zeros(len(methods))
        for field, color in zip(fields, colors):
            values = np.array([row.get(field) or 0 for row in chosen])
            ax.bar(range(len(methods)), values, bottom=bottom, label=field.removesuffix("_s"), color=color)
            bottom += values
            for method, row, value in zip(methods, chosen, values):
                points.append(dict(n=n, method=method, repetition=row["repetition"],
                                   run_id=row["run_id"], component=field, seconds=float(value),
                                   measured=row.get(field) is not None))
        remaining = np.array([row["total_s"] for row in chosen]) - bottom
        require(min(remaining) >= -1e-5, "Các pha cộng lớn hơn total.")
        remaining = np.maximum(remaining, 0)
        ax.bar(range(len(methods)), remaining, bottom=bottom, label="coordination", color=colors[-1])
        for method, row, value in zip(methods, chosen, remaining):
            points.append(dict(n=n, method=method, repetition=row["repetition"],
                               run_id=row["run_id"], component="coordination", seconds=float(value), measured=False))
        ax.set_xticks(range(len(methods)), labels=[LABEL[m] for m in methods], rotation=55, ha="right")
        ax.set_ylabel("Seconds")
        ax.set_title(f"N={n}")
        ax.grid(axis="y", alpha=0.2)
    fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center",
               bbox_to_anchor=(0.5, 1.08), ncol=4, fontsize=8, frameon=False)
    save_figure(fig, "phase_breakdown", points, output_dir)


FIGURES = {
    "formula_sizes": plot_formula_sizes,
    "sat_runtime": plot_runtime,
    "native_runtime": lambda report, out: plot_runtime(report, out, native=True),
    "memory": plot_memory,
    "status_matrix": plot_status_matrix,
    "cactus": plot_cactus,
    "sat_iqr": plot_sat_iqr,
    "phase_breakdown": plot_phase_breakdown,
}


def create_figures(report, output_dir, selected=None):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10,
                         "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42})
    names = [selected] if selected else list(FIGURES)
    for name in names:
        FIGURES[name](report, output_dir)
        print(f"Đã tạo hình: {name}.pdf / .png và CSV điểm dữ liệu")
