# N-Queens Solver

Bài tập lớn số 1 — môn **Các vấn đề hiện đại Khoa học máy tính**.

Dự án tìm một cách đặt N quân hậu trên bàn cờ N × N sao cho không có hai quân hậu cùng hàng, cột hoặc đường chéo; đồng thời so sánh kích thước mô hình, thời gian xử lý và bộ nhớ giữa các phương pháp.

## Các phương pháp

- **SAT — Glucose3:** Binomial, Binary, Commander, Product và Sequential. Commander và Product trong phiên bản này dùng **đệ quy**.
- **CP/ILP:** CP-SAT, CPLEX CP Optimizer, CPLEX MIP và Gurobi.
- **Mô hình SAT:** mỗi ô là một biến Boolean; mỗi hàng/cột có đúng một hậu bằng ALO (*ít nhất một*) kết hợp AMO (*tối đa một*); mỗi đường chéo chỉ áp dụng AMO.

## Nội dung repository

| Thư mục | Nội dung |
|---|---|
| [`src/`](src/) | Mã hóa bài toán, tích hợp solver và chương trình thực nghiệm |
| [`results/experiment_02/`](results/experiment_02/) | Bộ kết quả gốc được dùng trong báo cáo |
| [`analysis/`](analysis/) | Kiểm tra, tổng hợp dữ liệu và tạo bảng, biểu đồ |
| [`report/`](report/) | Nguồn LaTeX và tài nguyên báo cáo |
| [`report/tables/`](report/tables/) | Các bảng số liệu LaTeX |
| [`report/figures/`](report/figures/) | Các biểu đồ kết quả |
| [`report/data/`](report/data/) | Bản sao dữ liệu đầu vào và số liệu tổng hợp phục vụ báo cáo |

## Dữ liệu thực nghiệm

Bộ dữ liệu dùng trong báo cáo có định danh `20261015T101136Z_afe2720f`, lưu tại `results/experiment_02/`.

| File | Cách sử dụng |
|---|---|
| [`experiment_results.csv`](results/experiment_02/experiment_results.csv) | Xem số liệu của từng lượt chạy |
| [`results.jsonl`](results/experiment_02/results.jsonl) | Tra cứu bản ghi chi tiết, trạng thái và thông tin chẩn đoán |
| [`manifest.json`](results/experiment_02/manifest.json) | Xem cấu hình và thông tin môi trường của đợt thực nghiệm |
| [`summary.csv`](results/experiment_02/summary.csv) | Xem bảng tổng hợp do chương trình thực nghiệm xuất |

Đợt thực nghiệm sử dụng **3 lượt cho mỗi cấu hình**, giới hạn **100 giây cho toàn lượt**, ngưỡng bộ nhớ **6.144 MiB**, cấu hình **1 luồng** và không bỏ qua SAT theo ngưỡng số clause. Thông tin cấu hình chi tiết được lưu trong `manifest.json`.

Trong `report/data/`, `summary_runner.csv` là bản sao bảng tổng hợp của runner; `summary_report.csv` là bảng tổng hợp phục vụ trình bày báo cáo.

## Cách đọc các bảng

| Trường | Ý nghĩa |
|---|---|
| `N` / `n` | Kích thước bàn cờ N × N |
| Encoding / Solver | Phương pháp mã hóa hoặc bộ giải được sử dụng |
| Vars | Với SAT: tổng biến của CNF, gồm biến ô cờ và biến phụ |
| Clauses | Số mệnh đề của CNF; không đồng nhất với số ràng buộc CP/ILP |
| `build_s` | Thời gian sinh CNF hoặc xây dựng mô hình |
| `load_s` | Thời gian nạp CNF vào SAT solver, khi được ghi riêng |
| `solve_s` | Thời gian thực hiện bước giải |
| `Total_s` / `total_s` | Thời gian toàn lượt, gồm cả chi phí ngoài bước xây dựng và giải |
| RAM / `peak_rss_mib` | Mức bộ nhớ RSS đỉnh mà bộ giám sát ghi nhận, đơn vị MiB |

`build_s + load_s + solve_s` thể hiện thời gian xây dựng, nạp và giải SAT. Khi lấy trung vị, cộng ba thành phần **trong từng lượt trước**, sau đó lấy trung vị các tổng; không cộng ba trung vị riêng.

Số biến/clause theo công thức mô tả **CNF đầy đủ dự kiến**. Với lượt bị ngắt, cần xem thêm `clauses_generated` và `clauses_loaded` để biết tiến độ ghi nhận được; không mặc định toàn bộ CNF đã được tạo và nạp.

| Trạng thái | Ý nghĩa |
|---|---|
| `SAT` | Tìm được nghiệm thỏa mãn |
| `UNSAT` | Chứng minh không tồn tại nghiệm |
| `TIMEOUT` / `TO` | Hết giới hạn thời gian trước khi hoàn tất |
| `MEM_LIMIT` | Vượt ngưỡng bộ nhớ được giám sát |
| `UNKNOWN` | Bộ giải chưa kết luận được SAT hoặc UNSAT; xem bản ghi chi tiết |

**TO không phải UNSAT.** Ô trống hoặc dấu “—” không có nghĩa là 0. Một giá trị thời gian bằng 0 ở bản ghi bị ngắt cũng không đủ để kết luận bước giải không tốn thời gian. Giới hạn 100 giây không phải thời gian giải thành công.

## Cách đọc các biểu đồ

| Nhóm biểu đồ | Câu hỏi cần xem |
|---|---|
| Thời gian theo N | Khi bàn cờ lớn hơn, phương pháp nào mất nhiều thời gian hơn? Chú ý đồ thị dùng `solve_s`, tổng build/load/solve hay `Total_s`. |
| Số biến và clause theo N | Mỗi cách mã hóa làm kích thước CNF tăng như thế nào? |
| Bộ nhớ theo N | Phương pháp nào sử dụng nhiều RAM hơn trong các lượt được đo? |
| Số trường hợp/lượt giải được | Phương pháp hoàn tất được bao nhiêu trường hợp dưới cùng giới hạn tài nguyên? |
| Độ phân tán giữa các lượt | Thời gian đo có ổn định giữa các lần chạy hay không? |

Nếu trục dùng thang log, khoảng cách đều biểu thị tỷ lệ nhân, không phải mức tăng cộng đều. Các điểm timeout hoặc thiếu điểm cần được đọc theo chú thích của từng hình.

Khi so sánh, hãy xem **cả thời gian và số lượt thành công**. Ví dụ, trung vị từ một lượt thành công trên ba lượt không thể hiện hai lượt còn lại bị timeout. Ít clause hơn cũng không bảo đảm giải nhanh hơn. Các kết luận hiệu năng chỉ áp dụng cho cài đặt, cấu hình và môi trường đã khảo sát.

## Data Availability

Repository cung cấp mã nguồn, dữ liệu thực nghiệm, mã phân tích và nguồn báo cáo. Bảng và biểu đồ được tạo từ dữ liệu bằng các script trong `analysis/`. Để đối chiếu một kết quả, xem bảng/hình trong `report/`, bản ghi gốc trong `results/experiment_02/` và cấu hình tương ứng trong `manifest.json`.
