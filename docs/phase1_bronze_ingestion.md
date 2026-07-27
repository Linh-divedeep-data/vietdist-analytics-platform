# 🏆 VietDist Phase 1: Bronze Data Lake

**Thời hạn nộp bài:** Cuối Tuần 2

## 📝 Bối cảnh dự án (Context)
VietDist là một công ty phân phối hàng tiêu dùng nhanh (FMCG). Mỗi ngày, bộ phận Sales, Marketing và Kế toán sẽ tải các file báo cáo doanh thu, thông tin khách hàng, và thông tin sản phẩm lên một thư mục dùng chung trên Google Drive. 
Đội ngũ Data Analytics đang gặp khó khăn vì dữ liệu bị phân mảnh trên quá nhiều file Excel và CSV.

Là một Data Engineer, nhiệm vụ của bạn trong **Phase 1** là xây dựng một Data Pipeline tự động kết nối vào thư mục Google Drive của công ty, tải dữ liệu thô về, gắn thêm các thông tin metadata cần thiết, và lưu trữ vào thư mục **Bronze Lake** dưới định dạng siêu tốc **Parquet**.

---

## 🎁 Tài nguyên được cung cấp (Handover Materials)
Giảng viên sẽ cung cấp cho bạn 2 tài nguyên quan trọng để làm bài:
1. **File `credentials.json`**: Đây là "Chìa khóa" (Service Account) giúp code Python của bạn có quyền truy cập vào Google Drive của công ty.
2. **File `gdrive_connector.py`**: Đây là đoạn code mẫu đã được cấu hình sẵn để giao tiếp với Google Drive API (vì phần này khá phức tạp với người mới). Bạn chỉ cần import file này vào code của mình để sử dụng.

---

## ⚙️ Hướng dẫn Setup ban đầu (Setup Instructions)
Trước khi code, hãy làm đúng các bước sau để môi trường không bị lỗi:
1. Đặt file `credentials.json` và `gdrive_connector.py` vào cùng thư mục với file code chính của bạn (VD: `main.py`).
2. **Cực kỳ quan trọng:** Mở file `.gitignore` và thêm dòng `credentials.json` vào. Tuyệt đối không được push file chìa khóa này lên Github!
3. Mở file `.env`, thêm cấu hình đường dẫn file chìa khóa: `GOOGLE_SERVICE_ACCOUNT_JSON=credentials.json`.
4. Mở Terminal, cài đặt thư viện Google API bằng lệnh:
   ```bash
   uv add google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv
   ```

---

## 🚀 Nhiệm vụ của bạn (What To Do)

1. **Lấy danh sách file từ Google Drive:**
   - Dùng hàm `list_files_in_folder(FOLDER_ID)` trong file `gdrive_connector.py` để lấy danh sách toàn bộ file.

2. **Tải dữ liệu về thư mục cục bộ (Local Download):**
   - Viết code hoàn thiện hàm `download_file(file_id, file_name)` trong file `gdrive_connector.py` để tải dữ liệu (hàm này hiện đang để trống `TODO`). Hãy đọc kỹ comment gợi ý trong file để biết cách dùng Google Drive API.
   - Dùng hàm vừa viết để tải toàn bộ 10 file từ Google Drive về thư mục `data/raw/`.
   - Sử dụng Polars (`pl.read_csv`, `pl.read_excel`) để đọc các file vật lý này từ thư mục `data/raw/` lên thành DataFrame.
   - Đảm bảo vòng lặp của bạn tải và đọc chính xác 10 file nguồn (từ `SRC01` đến `SRC10`). Có thể dùng hàm `glob.glob()` để lặp qua danh sách file.

3. **Gắn Metadata (Dấu vết dữ liệu):**
   - Trước khi lưu vào Data Lake, bạn phải dùng Polars (`with_columns`) để thêm 5 cột sau vào mỗi DataFrame:
   
   | Cột metadata | Kiểu | Mô tả |
   |---|---|---|
   | `_source_file` | TEXT | Tên file gốc, ví dụ: `SRC01_sales_transactions.csv` |
   | `_source_platform` | TEXT | `'google_drive'` |
   | `_run_date` | DATE/TEXT | Ngày chạy pipeline, lấy từ tham số `--run-date` (VD: `'2026-07-22'`) |
   | `_ingested_at` | TIMESTAMP | Thời điểm ghi file (NOW()) |
   | `_batch_id` | UUID | ID duy nhất cho mỗi lần chạy pipeline (dùng thư viện `uuid`) |

4. **Đổ dữ liệu thô vào Bronze Lake (Partitioning & Idempotency):**
   - Pipeline của bạn không được ghi đè hỏng dữ liệu của ngày hôm trước. Hãy tạo một thư mục con theo tham số ngày chạy: `data/bronze/20260722/`.
   - Tất cả các cột dữ liệu nên được ép kiểu thành chuỗi (String/VARCHAR) ở lớp này để tránh lỗi sập pipeline (Dùng `pl.all().cast(pl.String)`).
   - Dùng lệnh `df.write_parquet()` của Polars để ghi mỗi DataFrame thành 1 file `.parquet` vào thư mục của ngày hôm đó (Ví dụ: `data/bronze/20260722/SRC01_sales_transactions.parquet`). 
   - 💡 **Idempotency**: Việc lưu dữ liệu vào đúng thư mục ngày chạy (yyyymmdd) và ghi đè các file bên trong đảm bảo pipeline có thể chạy lại 100 lần mà không bị nhân bản dữ liệu rác.

5. **Ghi log vào Data Lake (ingest_log):**
   - Tạo ra một DataFrame `ingest_log` chứa thông tin các file đã tải: `batch_id`, `source_name`, `source_file`, `source_platform`, `rows_loaded`, `status`, `duration_sec`.
   - Lưu log này thành file `ingest_log.parquet` nằm CÙNG TRONG thư mục `data/bronze/yyyymmdd/`. Việc này đảm bảo Idempotency thay vì rủi ro nối dài (append) vô tận vào 1 file log duy nhất.

---

## ✅ Tiêu chí Nghiệm thu (Acceptance Criteria)
- [ ] Chạy pipeline không bị văng lỗi.
- [ ] Thư mục `data/raw/` chứa đủ 10 file gốc.
- [ ] Thư mục `data/bronze/` chứa đủ 11 file `.parquet` (10 file data + 1 file `ingest_log.parquet`).
- [ ] Dùng lệnh `pl.read_parquet('data/bronze/20260722/SRC01_sales_transactions.parquet')` thấy có đủ 5 cột metadata `_source_file`, `_source_platform`, `_run_date`, `_ingested_at`, `_batch_id`.

## 💡 Gợi ý (Hints)
- Polars đọc file Excel cần thêm một engine ẩn phía sau, nếu báo lỗi thiếu engine, hãy cài thêm `fastexcel` hoặc `xlsx2csv` qua `uv add`.
