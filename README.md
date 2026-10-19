# N-Queens Solver

Bài tập lớn số 1 — môn **Các vấn đề hiện đại Khoa học máy tính**.

Dự án tìm một cách đặt N quân hậu trên bàn cờ N × N sao cho không có hai quân hậu tấn công nhau; đồng thời so sánh kích thước mô hình, thời gian và bộ nhớ giữa các phương pháp.

## Các phương pháp

- **SAT — Glucose3:** Binomial, Binary, Commander, Product và Sequential. Commander và Product dùng đệ quy; Sequential dùng chuỗi Sinz, chuyển sang Pairwise cho nhóm không quá ba biến.
- **CP/ILP:** OR-Tools CP-SAT, CPLEX CP Optimizer, CPLEX MIP và Gurobi.
- **Mô hình SAT:** mỗi ô là một biến Boolean; ALO kết hợp AMO bảo đảm đúng một hậu trên mỗi hàng/cột; các đường chéo chỉ áp dụng AMO.

## Nội dung repository

| Vị trí | Nội dung |
|---|---|
| [`src/`](src/) | Mã hóa bài toán, tích hợp solver và chương trình thực nghiệm |
| [`results/experiment_02/`](results/experiment_02/) | Kết quả thực nghiệm gốc và cấu hình chạy |
| [`analysis/`](analysis/) | Kiểm tra dữ liệu, tính thống kê, xuất CSV và vẽ hình |
| [`analysis_output/data/tables/`](analysis_output/data/tables/) | CSV riêng cho từng bảng kết quả |
| [`analysis_output/data/`](analysis_output/data/) | Thống kê chung, số đo từng pha và thông tin kiểm tra |
| [`analysis_output/figures/`](analysis_output/figures/) | Biểu đồ PDF/PNG |
| [`analysis_output/data/figure_points/`](analysis_output/data/figure_points/) | Các điểm dữ liệu dùng để vẽ từng hình |
| [`tests/`](tests/) | Kiểm thử mã nguồn và quy tắc xử lý dữ liệu |

**Python xuất CSV và hình; các bảng và nội dung báo cáo được trình bày thủ công trên Overleaf.** Mã nguồn LaTeX không nằm trong phiên bản công bố hiện tại. Hướng dẫn chạy phần phân tích và ghép tệp nằm trong [README_ANALYSIS_VI.md](README_ANALYSIS_VI.md).

## Dữ liệu thực nghiệm

Đợt `20261015T101136Z_afe2720f` có **486 lượt**, gồm **18 kích thước từ N=4 đến N=1331**, **9 cấu hình phương pháp** và **3 lần lặp**. Mỗi lượt có ngân sách **100 giây toàn lượt**, ngưỡng RSS quan sát **6144 MiB**, cấu hình **1 luồng**, và không bỏ qua theo số clause.

- [`experiment_results.csv`](results/experiment_02/experiment_results.csv): số liệu từng lượt chạy.
- [`results.jsonl`](results/experiment_02/results.jsonl): bản ghi chi tiết, nghiệm và thông tin chẩn đoán.
- [`manifest.json`](results/experiment_02/manifest.json): cấu hình, môi trường và định danh mã chạy thực nghiệm.
- [`summary.csv`](results/experiment_02/summary.csv): bảng tổng hợp gốc do runner xuất.

Số liệu dùng để trình bày nằm trong `analysis_output/data/`. Tệp [`table_catalog.csv`](analysis_output/data/table_catalog.csv) ghi tên, đơn vị và quy ước của từng bảng. `data_audit.json` lưu kết quả kiểm tra; `analysis_provenance.json` lưu dấu vân tay đầu vào và mã phân tích.

## Cách đọc bảng kết quả

| Đại lượng | Ý nghĩa |
|---|---|
| Vars / Clauses | Số biến và mệnh đề của CNF đầy đủ theo công thức, trước tiền xử lý và không gồm clause học |
| Build | Thời gian sinh CNF hoặc xây dựng mô hình đã ghi nhận |
| Load | Thời gian nạp CNF vào SAT solver; native không đo riêng pha này |
| Solve | Thời gian quanh lời gọi giải; với native có thể gồm xuất mô hình, presolve và giao tiếp với engine |
| Work | SAT: Build + Load + Solve; native: Build + Solve |
| Total | Thời gian toàn lượt đến khi nhận kết quả hoặc bị dừng, gồm cả chi phí khởi động và phối hợp |
| RSS | Đỉnh bộ nhớ quan sát qua lấy mẫu, đơn vị MiB; không phải lượng RAM bảo đảm đủ để giải thành công |

Thời gian trong các bảng dùng **giây**, riêng `small_n.csv` dùng **mili giây**. CSV giữ số chưa làm tròn. Với Work, cộng các pha **trong từng lượt trước**, rồi mới lấy trung vị; không cộng các trung vị riêng.

Các bảng pha giữ số đo có thật kể cả khi cả lượt TIMEOUT/UNKNOWN. Mỗi cột thời gian có cột `_info` đi kèm:

| Ví dụ `_info` | Cách hiểu |
|---|---|
| `3/3;final;3SAT` | Ba số đo đã xác nhận hoàn tất; cả ba lượt tìm được nghiệm |
| `3/3;last_update;3TO` | Ba số đo tích lũy cuối đã nhận; cả ba lượt timeout, chưa xác nhận phép đo cuối cùng |
| `3/3;mixed;2TO+1U` | Trộn số đo đã xác nhận và bản cập nhật cuối; hai TIMEOUT và một UNKNOWN |
| `1/3;final;1S+2TO` | Chỉ một lượt có số đo dùng được; không phải trung vị của đủ ba lượt |
| `0/3;unavailable;3TO` | Chưa có số đo pha dùng được; ô số để trống |
| `0/3;not_measured;3SAT` | Không đo riêng pha này |
| `3/3;elapsed;3TO` | Thời gian thực tế đến lúc dừng, không phải thời gian tìm được nghiệm |

`final` xác nhận phép đo, không xác nhận có nghiệm: một lời gọi trả UNKNOWN vẫn có thể có số đo hoàn tất. Các bảng Work chỉ công bố trung vị khi đủ **3/3 SAT**; nhóm khác để trống kèm `needs_3_SAT`. Các bảng Total ghi thời gian đến khi kết thúc/dừng của mọi nhóm và giữ trạng thái riêng.

**Không đổi TIMEOUT thành UNSAT và không coi ô trống là 0.** Giá trị `solve_s=0` chưa được xác nhận trong bản ghi bị ngắt không được dùng như thời gian giải bằng 0. Thông tin từng phép đo nằm trong [`phase_measurements.csv`](analysis_output/data/phase_measurements.csv); cách tổng hợp từng ô nằm trong [`table_measurements.csv`](analysis_output/data/table_measurements.csv).

TIMEOUT không làm giảm kích thước CNF đầy đủ. Dùng `clauses_generated` và `clauses_loaded` trong bản ghi gốc để xem tiến độ; nạp đủ CNF không đồng nghĩa đã giải xong hoặc mọi đồng hồ đã được cập nhật lần cuối.

## Cách đọc biểu đồ

| Tên hình | Nội dung |
|---|---|
| `formula_sizes` | Số biến và clause theo N |
| `sat_runtime`, `native_runtime` | So sánh Work và Total của các nhóm hoàn tất đủ 3/3 SAT |
| `status_matrix` | Trạng thái từng phương pháp tại từng N |
| `cactus` | Số kích thước giải đủ 3/3 theo ngưỡng thời gian; trục ngang là thời gian, không phải N |
| `sat_iqr` | Trung vị và độ phân tán Q1–Q3 của Work; không phải khoảng tin cậy |
| `phase_breakdown` | Phân rã một lượt có Total ở vị trí trung vị, không cộng các trung vị pha |
| `memory` | Trung vị RSS của cả ba lượt; dấu × đánh dấu nhóm không hoàn tất đủ 3/3 |

Trên trục log, khoảng cách đều biểu thị tỷ lệ nhân. Các hình runtime chỉ vẽ nhóm đủ 3/3 SAT, nên không chứa mọi số đo của lượt bị ngắt trong các bảng CSV. Khi so sánh, cần xét cả thời gian và mức độ hoàn tất; ít clause hơn không bảo đảm giải nhanh hơn.

## Data Availability

Repository cung cấp mã giải bài toán, dữ liệu thực nghiệm gốc, mã tổng hợp CSV và mã vẽ biểu đồ. Số liệu và hình dùng trong báo cáo nằm tại `analysis_output/`, có thể đối chiếu với dữ liệu gốc trong `results/experiment_02/`. Phần trình bày LaTeX được biên soạn thủ công trên Overleaf và không được cung cấp trong phiên bản repository hiện tại.
