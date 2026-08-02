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
1. Đặt file `credentials.json` ở thư mục gốc repo (không commit). `gdrive_connector.py` nằm ở `src/gdrive_connector.py`, cùng package với `src/main.py` — không phải file rời ở gốc repo.
2. **Cực kỳ quan trọng:** Mở file `.gitignore` và thêm dòng `credentials.json` vào. Tuyệt đối không được push file chìa khóa này lên Github!
3. Mở file `.env`, thêm cấu hình đường dẫn file chìa khóa: `GOOGLE_SERVICE_ACCOUNT_JSON=credentials.json`.
4. Mở Terminal, cài đặt thư viện Google API bằng lệnh:
   ```bash
   uv add google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv
   ```

---

## 🚀 Nhiệm vụ của bạn (What To Do)

Kiến trúc code **KHÔNG** dồn vào 1 file `extract.py` duy nhất — tách theo package `config/` (khai báo tĩnh) + `src/extract/` (logic ingest, mỗi module 1 trách nhiệm) + `src/extract/unit_of_work/` (logic riêng từng nguồn). Breakdown ticket chi tiết: xem Epic 1 trong `docs/jira_new_structure.md`.

1. **Kết nối + lấy danh sách file từ Google Drive:**
   - `src/gdrive_connector.py` — `get_drive_service()` (auth bằng Service Account) và `list_files_in_folder(FOLDER_ID)`; phải duyệt hết `nextPageToken` nếu folder có nhiều hơn 1 trang kết quả.

2. **Tải file về `data/raw/`:**
   - Viết hoàn thiện `download_file(file_id, file_name)` trong `src/gdrive_connector.py` (hàm này để trống `TODO`) bằng `MediaIoBaseDownload`.
   - `src/extract/parser.py` — `download_all_sources(folder_id, batch_id)` lặp qua danh sách file lấy được ở bước 1, tải cả 10 file về `data/raw/`; 1 file lỗi (network/permission) ghi `status=failed` cho riêng file đó, KHÔNG được crash 9 file còn lại.

3. **Khai báo nguồn + đọc file thành DataFrame theo `unit_of_work`:**
   - `config/sources.py` — khai báo tĩnh `CSV_SOURCES` (SRC01, SRC03, SRC06, SRC09) và `EXCEL_SOURCES` (SRC02, SRC04, SRC05, SRC07, SRC08, SRC10).
   - `src/extract/parser.py` — `read_csv_source()` (`pl.read_csv(path, infer_schema_length=0)`) và `read_excel_source()` (`pl.read_excel(path).select(pl.all().cast(pl.String))`) — mỗi hàm chỉ đọc ĐÚNG 1 file, không tự lặp.
   - `src/extract/unit_of_work/base.py` — `process_source()` dùng chung cho cả 10 nguồn: đọc (qua `read_fn` truyền vào) → gắn lineage (bước 4) → ép String (bước 5) → đo `duration_sec`.
   - `src/extract/unit_of_work/src01_*.py` .. `src10_*.py` — 10 module, mỗi file chỉ khai `SOURCE_FILE` + `run()` gọi `process_source()` với đúng `read_fn` (CSV hay Excel).
   - `src/extract/registry.py` — `UNIT_OF_WORK: dict[str, Callable]` map `source_file → run()` tương ứng, đúng 10 entry, khớp `CSV_SOURCES ∪ EXCEL_SOURCES`.

4. **Gắn Metadata (Dấu vết dữ liệu):**
   - `src/extract/lineage.py` — `attach_lineage(df, source_file, run_date, batch_id)` dùng Polars (`with_columns`) thêm 5 cột sau vào mỗi DataFrame:

   | Cột metadata | Kiểu | Mô tả |
   |---|---|---|
   | `_source_file` | TEXT | Tên file gốc, ví dụ: `SRC01_sales_transactions.csv` |
   | `_source_platform` | TEXT | `'google_drive'` |
   | `_run_date` | DATE/TEXT | Ngày chạy pipeline, lấy từ tham số `--run-date` (VD: `'2026-07-22'`) |
   | `_ingested_at` | TIMESTAMP | Thời điểm ghi file (NOW()), stamp tại thời điểm gọi — không dùng chung 1 timestamp cho cả batch |
   | `_batch_id` | UUID | ID duy nhất cho mỗi lần chạy pipeline (sinh 1 lần ở `main.py`, dùng chung cho cả 10 nguồn) |

   - Wire `attach_lineage()` vào `unit_of_work/base.py.process_source()`, gọi ngay sau khi đọc — mọi nguồn đi qua đây, không có đường tắt nào bỏ qua bước gắn lineage.

5. **Đổ dữ liệu thô vào Bronze Lake (Partitioning & Idempotency):**
   - `src/extract/lineage.py` — `cast_to_string(df)` = `df.select(pl.all().cast(pl.String))`, ép TOÀN BỘ cột (kể cả `_ingested_at`) về String ngay trước khi ghi, để tránh lỗi sập pipeline.
   - `config/settings.py` — hằng số path `RAW_DIR/BRONZE_DIR/SILVER_DIR/GOLD_DIR` (KHÔNG chứa Drive credentials — `FOLDER_ID`/`SERVICE_ACCOUNT_FILE` giữ inline trong `gdrive_connector.py`).
   - `src/extract/orchestrator.py` — `run_bronze_ingestion(run_date, batch_id)` lặp qua `registry.UNIT_OF_WORK`, ghi mỗi DataFrame thành 1 file `.parquet` vào thư mục ngày chạy: `data/bronze/20260722/SRC01_sales_transactions.parquet` — ghi đè, không append. 1 nguồn lỗi (đọc/ghi) không được crash cả batch.
   - 💡 **Idempotency**: Việc lưu dữ liệu vào đúng thư mục ngày chạy (yyyymmdd) và ghi đè file bên trong đảm bảo pipeline chạy lại 100 lần không nhân bản dữ liệu rác.

6. **Ghi log vào Data Lake (ingest_log):**
   - `src/extract/ingest_log.py` — `build_ingest_log_record(batch_id, source_file, rows_loaded, status, duration_sec, source_platform="google_drive")` dựng 1 dòng log (7 cột: `batch_id, source_name, source_file, source_platform, rows_loaded, status, duration_sec`).
   - `write_ingest_log(records, bronze_run_dir)` ghi toàn bộ record thành `ingest_log.parquet`, nằm CÙNG TRONG thư mục `data/bronze/yyyymmdd/` — ghi đè, không append, giữ idempotency.
   - Wire `write_ingest_log()` vào cuối `orchestrator.run_bronze_ingestion()`, chạy sau khi loop xong cả 10 nguồn (dù có nguồn lỗi hay không).

---

## ✅ Tiêu chí Nghiệm thu (Acceptance Criteria)
- [ ] Chạy pipeline không bị văng lỗi.
- [ ] Thư mục `data/raw/` chứa đủ 10 file gốc.
- [ ] Thư mục `data/bronze/` chứa đủ 11 file `.parquet` (10 file data + 1 file `ingest_log.parquet`).
- [ ] Dùng lệnh `pl.read_parquet('data/bronze/20260722/SRC01_sales_transactions.parquet')` thấy có đủ 5 cột metadata `_source_file`, `_source_platform`, `_run_date`, `_ingested_at`, `_batch_id`.
- [ ] `registry.UNIT_OF_WORK` có đúng 10 entry, khớp `config.sources.CSV_SOURCES ∪ EXCEL_SOURCES`.
- [ ] Rerun cùng `run_date` 2 lần liên tiếp: row count từng file Bronze không đổi (idempotent).

## 💡 Gợi ý (Hints)
- Polars đọc file Excel cần thêm một engine ẩn phía sau, nếu báo lỗi thiếu engine, hãy cài thêm `fastexcel` hoặc `xlsx2csv` qua `uv add`.
