# Báo cáo N-Queens — mã nguồn LaTeX

Chọn XeLaTeX và `main.tex` khi upload gói `NQueens_LaTeX.zip` lên Overleaf. Font được đóng kèm trong `fonts/` để hiển thị tiếng Việt. PDF, bảng và hình đã được tạo sẵn; Overleaf không cần chạy Python.

## Tự sửa

- `metadata.tex`: tên, MSSV, lớp, khoa/trường, giảng viên, URL và revision repository.
- `sections/*.tex`: nội dung năm phần chính và phụ lục.
- `tables/*.tex`: 24 bảng thực nghiệm sinh tự động.
- `figures/*.pdf`: tám hình sinh tự động.
- `data/`: bốn đầu vào, thống kê và CSV điểm hình. `summary_runner.csv` chính là summary gốc được đổi tên.

Để tái tạo assets trên máy local trong gói LaTeX độc lập:

```text
python -m pip install -r requirements_report.txt
python build_report.py
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
```

`build_report.py` gọi bộ `analysis/` đóng kèm. Trong gói repository `NQueens_TaiTao.zip`, module này ở cạnh thư mục `report/`; lệnh chuẩn từ gốc dự án là:

```text
python -m analysis --input results/experiment_02 --output report
```

Đọc `HUONG_DAN_TAI_TAO.md` trong gói mã tái tạo (hoặc cùng cấp trong gói LaTeX) để biết lệnh PowerShell, thứ tự đọc code, ý nghĩa tám hình, quy tắc median/timeout, kiểm tra từng điểm và cách đưa lên GitHub.

Báo cáo phân tích đúng đợt `20261015T101136Z_afe2720f` với Commander/Product đệ quy. Dữ liệu mới cần rà lại câu chữ, các ví dụ cụ thể và kiểm tra cấu hình; không chỉ thay CSV để giữ nguyên diễn giải.

URL repository/revision và thông tin tác giả còn được đánh dấu để bạn điền. `code_hash` của runner không phải Git commit hash. Gói này chưa chứa solver nguồn; cần công bố dự án `src/` tương ứng cùng dữ liệu trong repository.
