# 🚀 Dự án Cuối khóa: VietDist Analytics Platform

Chào mừng bạn đến với **Capstone Project** của khóa học Python & Polars for Data Engineering!

Đây không phải là một bài tập về nhà thông thường. Đây là một **Dự án thực tế (Real-world Project)** mô phỏng chính xác những gì một Data Engineer làm việc tại các tập đoàn lớn. 

> **💡 Lưu ý Công nghệ (Tech Stack Shift):**
> Trong các bài tập hàng ngày trên lớp (Từ Tuần 1 đến Tuần 4), bạn sử dụng **Pandas** và **PostgreSQL** để rèn luyện nền tảng truyền thống. Tuy nhiên, ở Dự án Cuối khóa này, chúng ta sẽ chuyển sang một kiến trúc Big Data hoàn toàn mới: Sử dụng **Polars** và định dạng **Parquet (Data Lakehouse)**. Đây là cách tuyệt vời nhất để bạn so sánh ưu nhược điểm của 2 thế hệ công nghệ này!

---

## 📌 Khuyến nghị quan trọng về Github Repository
Mặc dù bạn có thể viết code dự án này chung với các bài tập thực hành hàng ngày của khóa học, **bạn có thể:**
👉 **TẠO MỘT GITHUB REPOSITORY RIÊNG BIỆT** chỉ dành cho dự án VietDist.

**Lý do:**
1. **Làm Portfolio xin việc:** Nhà tuyển dụng muốn xem một repo sạch sẽ, chuyên nghiệp, có cấu trúc rõ ràng (Data Lakehouse) chứ không muốn xem một đống code bài tập lộn xộn.
2. **Quản lý Môi trường cô lập:** Dự án này yêu cầu cài đặt thư viện Google API, Polars, Pytest... Việc tạo 1 repo mới với 1 file `pyproject.toml` và `.env` riêng sẽ giúp bạn không bị xung đột với các bài học khác.

---

## 🔍 Hướng dẫn xem dữ liệu Parquet
Vì chúng ta đã chuyển sang kiến trúc Data Lakehouse (lưu file `.parquet` thay vì lưu vào PostgreSQL), bạn sẽ không thể mở file Parquet bằng cách click đúp thông thường. 
Để truy vấn và xem dữ liệu Parquet bằng ngôn ngữ SQL quen thuộc, bạn có thể sử dụng phần mềm **DBeaver** kết hợp với **DuckDB**:
1. Mở DBeaver, tạo kết nối mới (New Database Connection).
2. Tìm kiếm và chọn **DuckDB**. DBeaver sẽ tự động tải DuckDB JDBC driver về.
3. Ở mục `Path`, bạn có thể để trống (chạy in-memory).
4. Sau khi kết nối, bạn có thể mở một SQL Editor mới và gõ lệnh truy vấn thẳng vào thư mục chứa file Parquet của bạn. Ví dụ:
   ```sql
   SELECT * FROM 'data/bronze/*.parquet' LIMIT 100;
   ```
Đây là một kỹ năng cực kỳ mạnh mẽ giúp bạn query dữ liệu Big Data ngay trên ổ cứng mà không cần cài đặt Database Server!

---

## 📅 Lộ trình thực hiện (Timeline)

Dự án được chia làm 3 Phase. Bạn KHÔNG cần phải làm dự án này ngay từ Tuần 1. Dưới đây là thời điểm bạn nên bắt đầu:

| Giai đoạn | Tên Giai đoạn | Thời điểm bắt đầu | Deadline Nộp bài | Mục tiêu |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1** | [Bronze Lake (Ingestion)](phase1_bronze_ingestion.md) | Cuối Tuần 2 | Đầu Tuần 3 | Kết nối Google API, kéo file về máy, lưu ra Parquet. |
| **Phase 2** | [Silver Lake (Cleansing)](phase2_silver_cleansing.md) | Cuối Tuần 3 | Đầu Tuần 4 | Dùng Polars dọn dẹp rác, xử lý null, ép kiểu dữ liệu. |
| **Phase 3** | [Gold Lakehouse (Star Schema)](phase3_gold_production.md) | Cuối Tuần 4 | Bế giảng | Dùng Polars Join tạo Star Schema, viết Unit Test, kết nối Power BI. |

---

## ⚙️ Cấu trúc thư mục (Nên có)
Nếu bạn tạo Repo mới, đây là cấu trúc thư mục tiêu chuẩn mà khuyến nghị bạn nên xây dựng:

```text
vietdist-lakehouse/
│
├── data/
│   ├── raw/                 # Chứa file vật lý tải từ Google Drive
│   ├── bronze/              # Chứa file Parquet (Nguyên bản)
│   ├── silver/              # Chứa file Parquet (Đã làm sạch)
│   └── gold/                # Chứa file Parquet (Star Schema)
│
├── src/
│   ├── extract.py           # Gọi API Google Drive (Dùng gdrive_connector)
│   ├── transform_silver.py  # Code dọn dẹp data
│   └── transform_gold.py    # Code join data tạo báo cáo
│
├── tests/
│   └── test_pipeline.py     # Code Pytest kiểm tra dữ liệu
│
├── credentials.json         # KHÔNG PUSH LÊN GITHUB
├── .env                     # KHÔNG PUSH LÊN GITHUB
├── .gitignore               # Đã chặn credentials.json và .env
├── pyproject.toml           # Quản lý thư viện qua lệnh `uv`
└── main.py                  # CLI tự động chạy toàn bộ pipeline
```

Hãy click vào **[Phase 1](phase1_bronze_ingestion.md)** để bắt đầu nhiệm vụ đầu tiên khi bạn kết thúc Tuần 2 nhé. Chúc bạn code thật "cháy"! 🔥
