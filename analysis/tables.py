"""Tạo các bảng thực nghiệm .tex từ dữ liệu đã được kiểm tra.

Số đo đầy đủ ở data/summary_report.csv; chỉ ở đây mới làm tròn để trình bày.
Các bảng lý thuyết/định nghĩa trong báo cáo được viết trực tiếp trong LaTeX.
"""
from pathlib import Path
from .data_processing import SAT, NATIVE, METHODS, LABEL, counts, require

NOTE = (r"Giá trị số: trung vị của ba lượt SAT có nghiệm hợp lệ. TO: ba TIMEOUT; "
        r"2TO+1U: hai TIMEOUT và một UNKNOWN; 1S+2TO: một SAT và hai TIMEOUT. "
        r"Không thay lượt chưa hoàn tất bằng 0 hoặc 100 giây.")

def timing(x):
    if x is None:
        return '--'
    return f'{x:.6f}' if x < 0.01 else f'{x:.4f}' if x < 1 else f'{x:.3f}'

def count_fmt(x):
    return f'{int(x):,}'.replace(',', '\\,')

def write_table(output_dir, name, caption, headers, rows, note='', size='small', align=None):
    """Ghi bảng LaTeX từ các hàng đã tính; chỉ định dạng ở bước cuối."""
    align = align or 'l' + 'r' * (len(headers) - 1)
    text = ['\\begin{table}[pos=H]', '\\centering', '\\' + size, '\\caption{' + caption + '}', '\\label{tab:' + name + '}', '\\setlength{\\tabcolsep}{4pt}', '\\begin{tabular}{@{}' + align + '@{}}', '\\toprule', ' & '.join(headers) + ' \\\\', '\\midrule']
    text += [' & '.join(map(str, row)) + ' \\\\' for row in rows]
    text += ['\\bottomrule', '\\end{tabular}']
    if note:
        text += ['\\par\\smallskip\\begin{minipage}{\\linewidth}\\footnotesize ' + note + '\\end{minipage}']
    text += ['\\end{table}', '']
    (output_dir / 'tables' / (name + '.tex')).write_text('\n'.join(text), encoding='utf-8')

def create_tables(report, output_dir):
    """Mỗi lời gọi write_table tương ứng một tệp trong report/tables/."""
    output_dir = Path(output_dir)
    (output_dir / 'tables').mkdir(parents=True, exist_ok=True)
    sizes = report['sizes']
    summary = report['summary']
    groups = report['groups']
    raw = report['raw']
    coverage = report['coverage']
    pairs = report['pairs']
    common = report['common']
    winners = report['winners']
    # 1. Bao phủ: đếm nhóm kích thước và đếm lượt là hai đơn vị khác nhau.
    write_table(
        output_dir,
        'coverage',
        'Mức độ hoàn tất của đợt thực nghiệm không giới hạn clause.',
        ['Phương pháp', 'Đủ 3/3', 'Có SAT', 'SAT', 'TO', 'UNK'],
        [
            [
                LABEL[d['method']],
                f"{d['solved_all']}/18",
                f"{d['solved_any']}/18",
                d['SAT'],
                d['TIMEOUT'],
                d['UNKNOWN'],
            ]
            for d in coverage
        ],
        (
            'Hai cột tỷ lệ đếm kích thước; ba cột cuối đếm lượt. Mỗi phương pháp được thử đủ 54'
            ' lượt; không có SKIPPED, MEM\\_LIMIT hoặc ERROR.'
        ),
    )
    # 2. Các bảng thời gian có chung mẫu: N ở hàng, phương pháp ở cột.
    for name, methods, key, caption in [
        (
            'sat_work',
            SAT,
            'median_work_s',
            'Thời gian sinh, nạp và giải SAT: $T_{\\mathrm{work}}$ (giây).',
        ),
        (
            'sat_total',
            SAT,
            'median_total_s',
            'Thời gian toàn lượt SAT: $T_{\\mathrm{total}}$ (giây).',
        ),
        ('sat_build', SAT, 'median_build_s', 'Thời gian sinh CNF SAT (giây).'),
        ('sat_load', SAT, 'median_load_s', 'Thời gian nạp CNF SAT (giây).'),
        ('sat_solve', SAT, 'median_solve_s', 'Thời gian quanh lời gọi giải SAT (giây).'),
        (
            'native_work',
            NATIVE,
            'median_work_s',
            'Thời gian xây mô hình và gọi giải CP/ILP: $T_{\\mathrm{work}}$ (giây).',
        ),
        ('native_total', NATIVE, 'median_total_s', 'Thời gian toàn lượt CP/ILP (giây).'),
        ('native_build', NATIVE, 'median_build_s', 'Thời gian xây mô hình CP/ILP (giây).'),
        ('native_solve', NATIVE, 'median_solve_s', 'Thời gian quanh lời gọi giải CP/ILP (giây).'),
    ]:
        write_table(
            output_dir,
            name,
            caption,
            ['$N$'] + [LABEL[m] for m in methods],
            [
                (
                    [n]
                    + [
                        (
                            timing(summary[n, m][key])
                            if summary[n, m]['status'] == 'SAT'
                            else summary[n, m]['status']
                        )
                        for m in methods
                    ]
                )
                for n in sizes
            ],
            note=NOTE,
        )
    # 3. Kích thước CNF đầy đủ, không giảm theo tiến độ của lượt timeout.
    for name, key, caption in [
        ('variables', 'total_vars', 'Số biến CNF đầy đủ của năm mã hóa.'),
        ('clauses', 'cnf_clauses', 'Số clause đầu vào của năm mã hóa.'),
    ]:
        write_table(
            output_dir,
            name,
            caption,
            ['$N$'] + SAT,
            [[n] + [count_fmt(counts(n, m)[key]) for m in SAT] for n in sizes],
            size='footnotesize',
            note=(
                'Commander và Product đều là bản đệ quy. Số đếm theo công thức trước tiền xử '
                'lý; TIMEOUT không làm giảm kích thước mô hình đầy đủ. Không bao gồm clause '
                'học.'
            ),
        )
    for name, methods in [('sat_ram', SAT), ('native_ram', NATIVE)]:
        write_table(
            output_dir,
            name,
            'Trung vị đỉnh RSS quan sát (' + ('SAT' if name == 'sat_ram' else 'CP/ILP') + ', MiB).',
            ['$N$'] + [LABEL[m] for m in methods],
            [
                (
                    [n]
                    + [
                        (
                            f"{summary[n, m]['median_peak_rss_mib']:.1f}"
                            + ('$^{\\dagger}$' if summary[n, m]['status'] != 'SAT' else '')
                        )
                        for m in methods
                    ]
                )
                for n in sizes
            ],
            note=(
                '$\\dagger$: không hoàn tất đủ ba lượt; đây là bộ nhớ đã quan sát trong các lượt'
                ' chạy, không phải mức RAM cần để giải thành công.'
            ),
        )
    write_table(
        output_dir,
        'small_n',
        'Thành phần thời gian SAT tại N=4 (mili giây).',
        ['Mã hóa', 'Khởi động', 'Thiết lập', '$T_{work}$', 'Solve', '$T_{total}$'],
        [
            (
                [m]
                + [
                    f'{1000 * summary[4, m][key]:.3f}'
                    for key in ['median_startup_s', 'median_setup_s', 'median_work_s', 'median_solve_s', 'median_total_s']
                ]
            )
            for m in SAT
        ],
        (
            'Mỗi cột là một trung vị riêng. Trung vị tổng không nhất thiết bằng tổng các trung '
            'vị thành phần.'
        ),
    )
    write_table(
        output_dir,
        'phase_216',
        'Phân rã thời gian tại N=216 (giây).',
        ['Phương pháp', 'Build', 'Load', 'Solve', '$T_{work}$', '$T_{total}$'],
        [
            (
                [LABEL[m]]
                + (
                    [
                        timing(summary[216, m][key])
                        for key in ['median_build_s', 'median_load_s', 'median_solve_s', 'median_work_s', 'median_total_s']
                    ]
                    if summary[216, m]['status'] == 'SAT'
                    else [summary[216, m]['status']] * 5
                )
            )
            for m in METHODS
        ],
        (
            'Mỗi cột là một trung vị riêng; tổng các trung vị pha có thể khác trung vị work. '
            'Load chỉ áp dụng cho SAT; dấu -- của native không phải một pha nạp được đo bằng 0.'
        ),
    )
    # 4. Ví dụ N=64 liên hệ kích thước với công việc tìm kiếm thực tế.
    counter = []
    for m in SAT:
        g = groups[64, m]
        stats = [r['solver_stats'] for r in g]
        require(all((s == stats[0] for s in stats)), 'Bộ đếm N=64 thay đổi; cần cập nhật cách trình bày bảng counterexample.')
        counter.append([m, count_fmt(g[0]['cnf_clauses']), timing(summary[64, m]['median_solve_s']), count_fmt(stats[0]['conflicts']), count_fmt(stats[0]['propagations'])])
    write_table(
        output_dir,
        'counterexample',
        'Số clause và công việc tìm kiếm của Glucose3 tại N=64.',
        ['Mã hóa', 'Clause', 'Solve (s)', 'Xung đột', 'Lan truyền'],
        counter,
        (
            'Bộ đếm xung đột và lan truyền trùng nhau giữa ba lượt của mỗi mã hóa ở N=64. Thời '
            'gian là trung vị; các mã hóa có cấu trúc khác nhau.'
        ),
    )
    write_table(
        output_dir,
        'pairwise_binomial',
        'Đối chiếu với Binomial trên tập cả hai hoàn tất 3/3.',
        ['Encoding', '$|S|$', 'Nhanh hơn', 'Chậm hơn', 'Hệ số hình học'],
        [
            [d['method'], d['matched'], d['wins'], d['losses'], f"{d['geometric_speedup']:.3f}"]
            for d in pairs
        ],
        (
            'Dùng $T_{work}$. Hệ số lớn hơn 1 nghĩa là nhanh hơn Binomial. Tập so sánh khác '
            'nhau giữa các hàng, nên không dùng làm xếp hạng chung.'
        ),
    )
    write_table(
        output_dir,
        'matched_winners',
        'Số kích thước có trung vị nhanh nhất trên tập chung.',
        ['Phương pháp', 'Theo $T_{work}$', 'Theo $T_{total}$'],
        [
            [
                LABEL[m],
                sum((v == m for v in winners['work'].values())),
                sum((v == m for v in winners['total'].values())),
            ]
            for m in METHODS
        ],
        (
            f'Tập chung gồm {len(common)} kích thước: ' + ', '.join(map(str, common))
            + '. Mỗi kích thước có trọng số bằng nhau; không thay thế đánh giá mức độ hoàn tất.'
        ),
    )
    write_table(
        output_dir,
        'native_size',
        'Kích thước mô hình CP và MIP ở giao diện người dùng.',
        ['$N$', 'Biến CP', 'AllDifferent', 'Biến MIP', 'Ràng buộc MIP'],
        [[n, n, 3, count_fmt(n * n), count_fmt(6 * n - 2)] for n in [4, 216, 1331]],
        (
            'Không quy đổi biến nguyên hoặc ràng buộc mức cao thành biến/clause CNF. Không phải'
            ' số lượng bên trong solver sau presolve.'
        ),
    )
    # 5. Giữ đầy đủ thông tin của trường hợp thành công một phần.
    partial = sorted(groups[125, 'Product'], key=lambda r: r['repetition'])
    write_table(
        output_dir,
        'partial_product',
        'Ba lượt Product đệ quy tại N=125.',
        ['Lượt', 'Trạng thái', 'Build (s)', 'Load (s)', 'Solve (s)', 'Total (s)', 'RSS (MiB)'],
        [
            [
                r['repetition'],
                r['status'],
                timing(r['build_s']),
                timing(r['load_s']),
                (timing(r['solve_s']) if r['status'] == 'SAT' else '--'),
                timing(r['total_s']),
                f"{r['peak_rss_mib']:.1f}",
            ]
            for r in partial
        ],
        size='footnotesize',
        note=(
            'Cả ba lượt đã nạp đủ 161.882 clause. Build/load của lượt TIMEOUT là số ghi nhận '
            'gần nhất; solve chưa hoàn tất nên không dùng giá trị 0 trong log. Không công bố '
            'trung vị hoàn tất của cả cấu hình từ một lượt SAT.'
        ),
    )
    to = [r for r in raw if r['solver'] == 'sat' and r['status'] == 'TIMEOUT']
    write_table(
        output_dir,
        'timeout_progress',
        'Tiến độ nạp CNF trong các lượt SAT bị TIMEOUT.',
        ['Encoding', 'Số TO', 'Đã báo nạp đủ', 'Chưa báo nạp đủ'],
        [
            [
                m,
                len((g := [r for r in to if r['encoding'] == m])),
                sum((r.get('clauses_loaded') == r['cnf_clauses'] for r in g)),
                sum((r.get('clauses_loaded') != r['cnf_clauses'] for r in g)),
            ]
            for m in SAT
        ],
        (
            'Tiến độ là thông báo gần nhất. Đã nạp đủ không có nghĩa đã giải xong; nhãn phase '
            'có thể cũ. Không lấy solve\\_s=0 của lượt bị ngắt làm thời gian tìm kiếm.'
        ),
    )
    write_table(
        output_dir,
        'progress_1331',
        'Kích thước đầy đủ và tiến độ nạp tại N=1331.',
        ['Encoding', 'Clause đầy đủ', 'Nạp: nhỏ nhất', 'Nạp: lớn nhất', 'Trạng thái'],
        [
            [
                m,
                count_fmt(counts(1331, m)['cnf_clauses']),
                count_fmt(min((r.get('clauses_loaded', 0) for r in groups[1331, m]))),
                count_fmt(max((r.get('clauses_loaded', 0) for r in groups[1331, m]))),
                '3TO',
            ]
            for m in SAT
        ],
        size='footnotesize',
        note=(
            'Các giá trị nạp là bản cập nhật đã nhận trước khi ngắt. Không phải kích thước CNF '
            'rút gọn và không bao gồm clause học.'
        ),
    )
    # 6. Mô tả độ phân tán, chỉ trên nhóm có đủ ba lượt hoàn tất.
    dispersion = []
    for n in [4, 64, 81, 216, 512]:
        for m in SAT:
            d = summary[n, m]
            if d['status'] == 'SAT':
                iqr = d['q3_work_s'] - d['q1_work_s']
                med = d['median_work_s']
                dispersion.append([n, m, timing(med), timing(iqr), f'{100 * iqr / med:.1f}'])
    write_table(
        output_dir,
        'dispersion',
        'Độ phân tán mô tả của $T_{work}$ tại một số kích thước.',
        ['$N$', 'Encoding', 'Trung vị (s)', 'IQR (s)', 'IQR/trung vị (\\%)'],
        dispersion,
        size='footnotesize',
        note=(
            'Q1/Q3 dùng nội suy inclusive trên ba lượt hoàn tất. IQR không phải khoảng tin cậy;'
            ' không áp dụng bảng này cho nhóm Product N=125 chỉ có một lượt SAT.'
        ),
    )
