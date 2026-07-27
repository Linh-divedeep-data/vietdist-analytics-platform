# 🥇 VietDist Phase 3: Star Schema & Production (Gold Lakehouse)

**Thời hạn nộp bài:** Cuối Tuần 4

## 📝 Bối cảnh dự án (Context)
Dữ liệu của công ty hiện tại đã rất sạch sẽ và được nén gọn gàng trong các file Parquet (Silver Lake). 
Tuy nhiên, sếp của bạn (Giám đốc Phân tích) yêu cầu một báo cáo "Doanh số thực tế so với Target theo từng vùng". Để làm được báo cáo này, các bạn Data Analyst cần phải thực hiện những câu lệnh `JOIN` vô cùng phức tạp nếu dữ liệu không được mô hình hóa.

Nhiệm vụ cuối cùng của bạn trong **Phase 3** là thực hiện Mô hình hóa Dữ liệu đa chiều (Dimensional Modeling) bằng Polars, tạo ra kiến trúc **Star Schema** (Lược đồ hình sao), lưu ra thư mục **Gold Lake** dưới định dạng Parquet để Power BI có thể kết nối thẳng vào vẽ báo cáo. Cuối cùng, bạn sẽ nâng cấp đoạn code thành một "Cỗ máy chuẩn Production" (Production-ready).

---

## 🚀 Nhiệm vụ của bạn (What To Do)

### Phần A: Dimensional Modeling (Gold Layer)
1. **Khởi tạo Dimension Tables (Bảng Chiều):**
   - Đọc dữ liệu từ thư mục của ngày chạy (Ví dụ: `data/silver/20260722/`).
   - Tạo các DataFrame `dim_customers`, `dim_products`, `dim_distributors`, `dim_date`.
   - **🔥 Thử thách (SCD Type 2):** Đối với bảng `dim_employees` (từ file `employee_master`), hãy theo dõi sự thay đổi vị trí/vùng của nhân viên theo thời gian. Cấu trúc bảng kết quả phải có các cột: `employee_key`, `employee_id`, `name`, `valid_from`, `valid_to`, `is_current`. (Gợi ý: Dùng `shift()` hoặc `over()` của Polars).

2. **Khởi tạo Fact Tables (Bảng Sự kiện):**
   - Tạo bảng `fact_sales` (từ `sales_transactions`), `fact_targets` (từ `sales_target_plan`).
   - Dùng lệnh `.join()` của Polars để tra cứu khóa ngoại (Surrogate Keys) từ các bảng Dim và gán vào bảng Fact.
   - 🛡️ **Data Lineage:** Đảm bảo các bảng Fact vẫn giữ lại các cột metadata (`_run_date`, `_batch_id`, v.v.) để biết chính xác mỗi dòng doanh thu được nạp vào hệ thống từ mẻ chạy (batch) nào.

3. **Tính toán Data Marts & Ghi ra Gold Lake:**
   - Dùng `.group_by().agg()` tạo bảng `mart_sales_vs_target` (So sánh tổng doanh thu thực tế và chỉ tiêu theo tháng và vùng).
   - Đẩy toàn bộ các bảng Dim, Fact và Mart ra thư mục đích theo định dạng ngày chạy `data/gold/20260722/` bằng lệnh `.write_parquet()`. Việc này tiếp tục tuân thủ quy tắc Idempotency xuyên suốt toàn dự án.

### Phần B: Nâng cấp chuẩn Production
1. **Lazy Evaluation:**
   - Cập nhật hàm đọc file ở Phase 2 và 3 từ `pl.read_parquet()` thành `pl.scan_parquet()` để khai thác tối đa trình tối ưu hóa bộ nhớ của Polars (Chỉ thực hiện `collect()` ở bước cuối cùng trước khi write).
2. **Kiểm thử (Testing):**
   - Viết ít nhất 2 hàm test bằng `pytest` trong file `test_pipeline.py`.
   - Test 1: Kiểm tra xem logic tính Data Mart `mart_sales_vs_target` có trả về số liệu chính xác không (sử dụng 1 DataFrame giả lập siêu nhỏ).
   - Test 2: Kiểm tra hàm xử lý SCD Type 2 có cập nhật ngày `valid_to` chính xác không.
3. **Giao diện Dòng lệnh (CLI):**
   - Sử dụng thư viện `argparse` trong `main.py` để chạy pipeline.
   - Bắt buộc phải có các tham số: 
     - `--layer`: (Nhận giá trị `bronze`, `silver`, `gold`, hoặc `all`).
     - `--run-date`: (Truyền ngày chạy pipeline, định dạng YYYY-MM-DD).

---

## ✅ Tiêu chí Nghiệm thu (Acceptance Criteria)
- [ ] Chạy thành công lệnh: `uv run main.py --layer all --run-date 2026-07-22`.
- [ ] Pipeline chạy tự động luồng: Google Drive -> data/raw -> data/bronze -> data/silver -> data/gold. Toàn bộ là file Parquet.
- [ ] Chạy `uv run pytest test_pipeline.py` trả về màn hình màu Xanh Lá (Passed 100%).
- [ ] Submit bài tập qua chức năng Pull Request (PR) trên Github.

## 🎓 Chúc mừng!
Hoàn thành Phase 3, bạn đã chính thức nắm giữ bộ kỹ năng Data Lakehouse hoàn chỉnh của một Modern Data Engineer. Bạn hoàn toàn có thể tự tin đặt dự án này lên đầu trang CV của mình!
