# 🥈 VietDist Phase 2: Silver Data Lake (Cleansing)

**Thời hạn nộp bài:** Cuối Tuần 3

## 📝 Bối cảnh dự án (Context)
Cảm ơn bạn! Nhờ có Phase 1, toàn bộ 10 file nguồn của công ty đã nằm gọn gàng trong **Bronze Lake** dưới định dạng Parquet siêu tốc độ.

Tuy nhiên, đội ngũ Data Analyst (Phân tích dữ liệu) đang phàn nàn:
- Bảng khách hàng (`customer_master`) bị trùng lặp dữ liệu do nhân viên vô tình up lại file cũ.
- Bảng lịch sử thay đổi nhân viên (`employee_master`) bị thiếu mã số thuế (tax_code), để trống (NULL).
- Kiểu dữ liệu trong Parquet hiện tại đều là dạng chuỗi (`String`), không thể tính toán tổng doanh thu.

Nhiệm vụ của bạn trong **Phase 2** là đọc ngược dữ liệu thô từ thư mục `data/bronze/` lên, dùng "phép thuật" Polars để dọn dẹp sạch sẽ, và lưu trữ kết quả xuống **Silver Lake** dưới định dạng Parquet.

---

## 🚀 Nhiệm vụ của bạn (What To Do)

1. **Đọc dữ liệu từ Bronze:**
   - Dùng lệnh `pl.read_parquet()` quét dữ liệu thô của đúng ngày đang chạy (Ví dụ: `data/bronze/20260722/*.parquet`).

2. **Dọn dẹp & Ép kiểu (Clean & Cast):**
   - Dùng `.with_columns()` và `.cast()` để chuyển các cột số tiền (string) sang kiểu `Float` hoặc `Integer`.
   - Chuyển các cột ngày tháng sang kiểu `Date` hoặc `Datetime` chuẩn của Polars.
   - Chuẩn hóa các giá trị Text: Xóa khoảng trắng thừa (`.str.strip_chars()`), đưa về chữ hoa (`.str.to_uppercase()`).

3. **Xử lý Dữ liệu Lỗi & Lưu vết (Data Quality & Lineage):**
   - Xóa bỏ (hoặc thay thế) các dòng có ID khách hàng, ID sản phẩm bị `NULL`.
   - Loại bỏ các dòng giao dịch bị trùng lặp 100% dữ liệu (Duplicates).
   - 🛡️ **Data Lineage:** Tuyệt đối KHÔNG ĐƯỢC xóa 5 cột metadata (`_source_file`, `_run_date`, v.v.) đã tạo ở Bronze. Chúng phải được mang nguyên vẹn sang Silver Lake để phục vụ truy vết lỗi (Troubleshooting) sau này.

4. **Lưu trữ vào Silver Lake (Đảm bảo Idempotency):**
   - Không được ghi gộp vào 1 cục. Hãy tiếp tục duy trì cơ chế Partitioning: Lưu dữ liệu sạch ra các file `.parquet` tương ứng vào thư mục của ngày đó (Ví dụ: `data/silver/20260722/customer_master.parquet`).
   - 💡 **Idempotency**: Nhờ việc tách folder theo ngày `yyyymmdd`, nếu chạy lại pipeline, dữ liệu chỉ được ghi đè vào thư mục của ngày đó, không phá hỏng dữ liệu lịch sử của các ngày khác.

---

## ✅ Tiêu chí Nghiệm thu (Acceptance Criteria)
- [ ] Code chạy mượt mà, không báo lỗi.
- [ ] Thư mục `data/silver/` xuất hiện đủ 10 file định dạng `.parquet`.
- [ ] Load thử file `data/silver/SRC01_sales_transactions.parquet` lên Polars và kiểm tra cột `amount` - nó phải là kiểu số (Float), không phải chuỗi (String).
- [ ] Kiểm tra bảng `customer_master` ở Silver, không còn bất cứ ô `tax_code` nào mang giá trị NULL.

## 💡 Gợi ý (Hints)
- **Cẩn thận khi ép kiểu:** Đôi khi dữ liệu số có chứa dấu phẩy phân cách ngàn (VD: `1,000,000`). Nếu ép thẳng bằng `.cast(pl.Float64)` sẽ bị báo lỗi. Bạn phải dùng hàm thay thế `.str.replace_all(",", "")` trước khi ép kiểu!
- Lưu ý múi giờ (Timezone) khi xử lý các cột ngày tháng.
- Nếu bạn có thời gian, hãy thử nghiệm `pl.scan_parquet()` (Lazy API) thay cho `pl.read_parquet()` (Eager API) để thấy sự khác biệt về cách Polars tối ưu hóa quy trình.
