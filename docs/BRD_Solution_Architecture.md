# VietDist Analytics Platform — BRD & Solution Architecture

**Loại tài liệu:** Business Requirements Document (BRD) + System Architecture
**Vai trò biên soạn:** Solution Architect / Senior BA (mô phỏng)
**Đối tượng dự án:** Portfolio cá nhân — Fresher Data Engineer
**Ngày:** 2026-07-26
**Trạng thái:** Draft v1.0 — nền tảng để triển khai Phase 1-2-3 đã có sẵn (xem `phase1_bronze_ingestion.md`, `phase2_silver_cleansing.md`, `phase3_gold_production.md`)

> **Ghi chú khả thi:** Toàn bộ actor, use case, kiến trúc trong tài liệu này được thiết kế khớp 100% với 10 file dữ liệu mẫu đã có sẵn trong `raw_data/` và stack công nghệ đã chốt (Polars, Parquet, DuckDB, Power BI). Không có hạng mục nào yêu cầu hạ tầng/API/tài khoản trả phí ngoài những gì giảng viên đã cấp. Đây là tài liệu BA "bọc ngoài" cho project kỹ thuật đã có — dùng để chứng minh tư duy sản phẩm khi phỏng vấn, không phát sinh thêm rủi ro triển khai.

---

## 1. Bối cảnh & Luồng Nghiệp vụ (Business Flow)

### 1.1 Bài toán kinh doanh

**Công ty:** VietDist — nhà phân phối FMCG (hàng tiêu dùng nhanh) hoạt động qua mạng lưới nhà phân phối (distributor) và nhân viên kinh doanh (sales rep) trải khắp các vùng/miền.

**Hiện trạng (As-Is):**

| Vấn đề | Hậu quả kinh doanh |
|---|---|
| Dữ liệu Sales, Marketing, Kế toán nằm rải rác trên Google Drive dưới dạng Excel/CSV, do từng phòng ban tự upload | Không ai có bức tranh tổng thể "một nguồn sự thật" (single source of truth) |
| Không có tiến trình chuẩn hóa dữ liệu | Báo cáo doanh thu build tay bằng Excel VLOOKUP, mất nhiều giờ/tuần, dễ sai sót |
| Không tách biệt dữ liệu thô — dữ liệu sạch — dữ liệu báo cáo | Sửa 1 lỗi ở nguồn có thể phải làm lại toàn bộ báo cáo tay từ đầu |
| Không lưu vết (lineage) dữ liệu | Khi số liệu sai, không biết lỗi phát sinh từ file nguồn nào, batch chạy nào |
| Chương trình khuyến mãi (`promotion_program`) không được đối chiếu với doanh số thực tế | Marketing không đo được ROI khuyến mãi, không biết campaign nào hiệu quả |
| Doanh số thực tế vs chỉ tiêu (`sales_target_plan`) phải so tay theo từng vùng/tháng | Ban giám đốc ra quyết định phân bổ target chậm, thiếu dữ liệu real-time |

**Mục tiêu dự án (To-Be):** Xây dựng một **Data Lakehouse tự động** (Bronze → Silver → Gold) chuẩn hóa toàn bộ 10 nguồn dữ liệu, tạo ra một **Star Schema** duy nhất phục vụ báo cáo, kết nối trực tiếp vào **Power BI/DuckDB** để 3 nhóm người dùng (Marketer, Data Analyst, Admin/DE) tự phục vụ (self-service) mà không cần chờ dựng báo cáo tay.

**Giá trị mang lại (Business Value):**
- Giảm thời gian tạo báo cáo doanh số vs target từ "vài giờ thao tác tay" xuống "chạy pipeline vài phút".
- Đo lường được hiệu quả khuyến mãi (`promotion_program`) theo doanh số thực tế (`fact_sales`) trong khoảng thời gian chương trình chạy.
- Truy vết (audit) được từng dòng dữ liệu về đúng file nguồn, ngày chạy, batch — phục vụ kiểm toán nội bộ.
- Đảm bảo pipeline chạy lại nhiều lần không làm hỏng/nhân bản dữ liệu (Idempotency) — yêu cầu bắt buộc ở môi trường production thật.

### 1.2 Actor & Use Case

| Actor | Vai trò nghiệp vụ | Nhu cầu chính với hệ thống |
|---|---|---|
| **Marketer** | Quản lý chương trình khuyến mãi, target theo vùng/kênh | Xem hiệu quả khuyến mãi, doanh số theo kênh/vùng, đề xuất phân bổ ngân sách |
| **Data Analyst (DA)** | Dựng báo cáo, phân tích ad-hoc | Query trực tiếp Gold layer bằng SQL (DuckDB), xây dashboard Power BI, không cần chờ DE viết query hộ |
| **Admin (Data Engineer/Vận hành)** | Vận hành pipeline, đảm bảo dữ liệu đúng — đủ — đúng hạn | Theo dõi log ingest, xử lý lỗi pipeline, quản lý credentials, đảm bảo idempotency |

**Danh sách Use Case chính:**

| # | Use Case | Actor chính | Mô tả ngắn |
|---|---|---|---|
| UC-01 | Kết nối & tải dữ liệu từ Google Drive | Admin | Hệ thống tự động lấy danh sách file + tải 10 file nguồn về `data/raw/` |
| UC-02 | Gắn metadata truy vết nguồn | Admin | Mỗi dòng dữ liệu được gắn `_source_file`, `_batch_id`, `_run_date`... trước khi lưu Bronze |
| UC-03 | Làm sạch & chuẩn hóa dữ liệu | Admin/DE | Ép kiểu, khử trùng lặp, xử lý NULL, chuẩn hóa text ở lớp Silver |
| UC-04 | Mô hình hóa Star Schema | Admin/DE | Tạo Dimension/Fact/Data Mart tại Gold layer để phục vụ báo cáo |
| UC-05 | Theo dõi lịch sử thay đổi nhân sự (SCD Type 2) | Admin/DE | Biết chính xác nhân viên X thuộc vùng nào tại thời điểm phát sinh đơn hàng Y |
| UC-06 | Truy vấn ad-hoc bằng SQL trên Data Lake | Data Analyst | Dùng DuckDB/DBeaver query thẳng file Parquet không cần Database Server |
| UC-07 | Xem báo cáo Doanh số thực tế vs Target | Marketer, DA | Dashboard Power BI so sánh theo vùng/tháng/nhân viên |
| UC-08 | Đánh giá hiệu quả chương trình khuyến mãi | Marketer | So sánh doanh số trong/ngoài thời gian khuyến mãi theo `promotion_program` |
| UC-09 | Giám sát chất lượng & tình trạng pipeline | Admin | Xem `ingest_log` để biết batch nào lỗi, chạy bao lâu, đọc bao nhiêu dòng |
| UC-10 | Chạy lại pipeline không phát sinh dữ liệu rác | Admin | Đảm bảo idempotency khi chạy lại pipeline cho cùng 1 `run_date` |

### 1.3 User Stories chính

| ID | User Story | Acceptance Criteria (tóm tắt) |
|---|---|---|
| US-01 | **Là Admin**, tôi muốn pipeline tự tải 10 file từ Google Drive về `data/raw/` mỗi ngày, **để** không phải tải tay | Chạy `--layer bronze` → đủ 10 file raw + 11 file Parquet Bronze (10 data + 1 log) |
| US-02 | **Là Admin**, tôi muốn mỗi dòng dữ liệu có `_batch_id`, `_run_date`, `_ingested_at`, **để** truy vết được nguồn gốc khi có sai lệch số liệu | Đọc bất kỳ file Bronze nào cũng thấy đủ 5 cột metadata |
| US-03 | **Là Data Analyst**, tôi muốn cột `amount`, `date` ở Silver đã đúng kiểu số/ngày, **để** tính tổng doanh thu mà không cần convert tay | Cột `amount` kiểu Float, không còn dấu phẩy ngăn cách hàng nghìn |
| US-04 | **Là Marketer**, tôi muốn xem báo cáo Doanh số thực tế vs Target theo vùng & tháng, **để** biết vùng nào đang lệch chỉ tiêu | Bảng `mart_sales_vs_target` có đủ cột region, month, actual_revenue, target_revenue, variance_pct |
| US-05 | **Là Marketer**, tôi muốn biết chương trình khuyến mãi nào tăng doanh số rõ rệt nhất, **để** đề xuất tiếp tục/dừng chương trình | Query join `fact_sales` với `dim_promotion` (theo `applicable_products` + khoảng `start_date`–`end_date`) ra doanh số trong kỳ khuyến mãi |
| US-06 | **Là DA**, tôi muốn biết nhân viên X phụ trách vùng nào tại đúng thời điểm phát sinh đơn hàng (không phải vùng hiện tại), **để** báo cáo hiệu suất nhân viên không bị sai lệch do chuyển vùng | `dim_employees` (SCD2) trả đúng `region` hiệu lực tại `order_date` |
| US-07 | **Là Admin**, tôi muốn chạy lại pipeline của cùng 1 ngày mà không tạo dữ liệu trùng, **để** an tâm retry khi gặp lỗi | Chạy lại `--run-date` cũ nhiều lần, số dòng dữ liệu không đổi |
| US-08 | **Là Admin**, tôi muốn có `ingest_log` cho từng batch, **để** biết ngay file nào tải lỗi, đọc được bao nhiêu dòng, chạy mất bao lâu | File `ingest_log.parquet` có `batch_id, source_file, rows_loaded, status, duration_sec` |

---

## 2. Luồng Dữ liệu & Sự kiện (Data Tracking & Schema)

### 2.1 Danh mục 10 nguồn dữ liệu (thực tế trong `raw_data/`)

| Mã nguồn | File | Grain (1 dòng = ?) | Tần suất cập nhật (giả định) | Vai trò trong mô hình Gold |
|---|---|---|---|---|
| SRC01 | `sales_transactions.csv` | 1 dòng đơn hàng bán lẻ/phân phối | Hàng ngày | `fact_sales` |
| SRC02 | `sales_target_plan.xlsx` | 1 chỉ tiêu doanh số/nhân viên/tháng | Hàng tháng (có versioning) | `fact_targets` |
| SRC03 | `customer_master.csv` | 1 khách hàng | Khi có KH mới/thay đổi | `dim_customers` |
| SRC04 | `product_master.xlsx` | 1 sản phẩm | Khi ra mắt/ngưng SP | `dim_products` |
| SRC05 | `distributor_orders.xlsx` | 1 đơn đặt hàng của NPP | Hàng ngày | `fact_distributor_orders` |
| SRC06 | `distributor_master.csv` | 1 nhà phân phối | Khi có NPP mới | `dim_distributors` |
| SRC07 | `employee_master.xlsx` | 1 bản ghi lịch sử nhân viên (có `version`, `effective_date`) | Khi có thay đổi vị trí/vùng | `dim_employees` (SCD Type 2) |
| SRC08 | `territory_mapping.xlsx` | 1 phân công khách hàng ↔ nhân viên theo kỳ hiệu lực | Khi thay đổi phân vùng | `dim_territory` / bridge table |
| SRC09 | `return_transactions.csv` | 1 dòng trả hàng | Hàng ngày | `fact_returns` |
| SRC10 | `promotion_program.xlsx` | 1 chương trình khuyến mãi | Khi mở/đóng chương trình | `dim_promotion` |

### 2.2 Data Dictionary — cột thực tế theo từng nguồn

| Nguồn | Các cột chính (đã kiểm tra thực tế trong file) |
|---|---|
| **SRC01** sales_transactions | `order_id, order_date, order_month, order_quarter, order_year, customer_id, region, province, channel, employee_id, product_id, product_category, quantity, unit_price, discount_pct, discount_amount, gross_amount, net_amount, delivery_status, payment_method, payment_status` |
| **SRC02** sales_target_plan | `plan_version, version_date, effective_from, effective_to, employee_id, employee_name, region, team, year, month, target_revenue, target_quantity, target_new_customers` |
| **SRC03** customer_master | `customer_id, customer_name, customer_type, channel, province, region, address, phone, tax_code, join_date, credit_limit, status` |
| **SRC04** product_master | `product_id, product_name, category, sub_category, unit, unit_price, cost_price, weight_gram, status, launch_date` |
| **SRC05** distributor_orders | `order_id, order_date, order_month, order_quarter, distributor_id, region, channel, product_id, product_category, qty_ordered, qty_delivered, fill_rate_pct, unit_price_list, distributor_price, gross_amount, delivered_amount, expected_delivery_date, actual_delivery_date, ontime_delivery, delivery_status, payment_terms` |
| **SRC06** distributor_master | `distributor_id, distributor_name, tier, channel, province, region, contact_person, phone, email, tax_code, join_date, credit_limit, status, assigned_supervisor_id` |
| **SRC07** employee_master | `employee_id, full_name, gender, date_of_birth, join_date, position, region, team, email, phone, status, version, effective_date, resign_date, transfer_note` |
| **SRC08** territory_mapping | `territory_id, employee_id, customer_id, region, team, effective_date, expiry_date, version` |
| **SRC09** return_transactions | `return_id, original_order_id, return_date, return_month, customer_id, employee_id, product_id, region, province, return_quantity, unit_price, return_amount, return_reason, status` |
| **SRC10** promotion_program | `promotion_id, promotion_name, promotion_type, target_channel, target_region, start_date, end_date, applicable_products, discount_pct, min_order_quantity, budget_vnd, actual_cost_vnd, status, created_by` |

### 2.3 Vòng đời dữ liệu qua 3 lớp (Bronze → Silver → Gold)

| Lớp | Mục tiêu | Kiểu dữ liệu | Metadata bắt buộc |
|---|---|---|---|
| **Bronze** | Lưu nguyên trạng dữ liệu thô + gắn dấu vết | Toàn bộ ép về `String` | `_source_file, _source_platform, _run_date, _ingested_at, _batch_id` |
| **Silver** | Làm sạch, ép kiểu đúng nghiệp vụ, khử trùng/NULL | `Float/Int` cho số tiền-số lượng, `Date/Datetime` cho ngày, `String` chuẩn hóa (strip, uppercase) | Giữ nguyên 5 cột metadata Bronze (data lineage) |
| **Gold** | Mô hình hóa Star Schema, sẵn sàng cho BI | Dimension (`dim_*`) + Fact (`fact_*`) + Data Mart (`mart_*`) | Fact table giữ `_run_date, _batch_id` để biết batch nạp |

### 2.4 Mô hình Star Schema (Gold Layer)

```
                         dim_date
                            │
      dim_customers ───┐    │    ┌─── dim_products
                        │   │    │
                    fact_sales (grain: 1 dòng/order line)
                        │   │    │
      dim_employees ────┘   │    └─── dim_territory
        (SCD Type 2)        │
                            │
                     fact_targets ──── dim_employees, dim_date
                     fact_returns ──── dim_customers, dim_products, dim_employees
              fact_distributor_orders ── dim_distributors, dim_products
                     dim_promotion ──── fact_sales (join theo product + khoảng ngày)

                     mart_sales_vs_target (Data Mart tổng hợp theo region + month)
```

**Bảng SCD Type 2 — `dim_employees`:** cột bắt buộc `employee_key (surrogate), employee_id, name, region, team, valid_from, valid_to, is_current` — giải quyết đúng bài toán US-06 (nhân viên đổi vùng giữa chừng vẫn ra đúng lịch sử).

---

## 3. Luồng Kiến trúc Hệ thống (System Architecture & Pipeline Flow)

### 3.1 End-to-End Data Flow

```
[Google Drive – Sales/Marketing/Kế toán upload file thủ công]
              │  (Service Account – credentials.json)
              ▼
[gdrive_connector.py]  ── list_files_in_folder() / download_file()
              │
              ▼
[data/raw/]  ── 10 file CSV/XLSX vật lý (SRC01 → SRC10)
              │  Polars: pl.read_csv / pl.read_excel
              ▼
[BRONZE — data/bronze/yyyymmdd/]
   - Ép toàn bộ cột về String (an toàn, không sập pipeline)
   - Gắn 5 cột metadata lineage
   - Ghi Parquet + ingest_log.parquet
              │  Polars: scan_parquet (lazy) → cast, dedup, xử lý NULL
              ▼
[SILVER — data/silver/yyyymmdd/]
   - Đúng kiểu dữ liệu (Float/Date/String chuẩn hóa)
   - Loại trùng lặp, xử lý NULL khóa chính
   - Vẫn giữ metadata lineage
              │  Polars: join() dựng Dimensional Model + SCD Type 2
              ▼
[GOLD — data/gold/yyyymmdd/]
   - dim_customers, dim_products, dim_distributors, dim_date, dim_territory, dim_promotion
   - dim_employees (SCD Type 2)
   - fact_sales, fact_targets, fact_returns, fact_distributor_orders
   - mart_sales_vs_target (data mart tổng hợp sẵn)
              │
       ┌──────┴───────┐
       ▼               ▼
[DuckDB + DBeaver]   [Power BI]
 truy vấn SQL ad-hoc   dashboard trực quan
 trực tiếp trên Parquet kết nối thẳng vào data/gold/
       │               │
       ▼               ▼
   Data Analyst    Marketer / Admin / Ban giám đốc
```

**Orchestration & CLI:** toàn bộ pipeline chạy qua 1 điểm vào duy nhất `main.py` với `argparse`:
```bash
uv run main.py --layer all --run-date 2026-07-22
# --layer: bronze | silver | gold | all
```
Đây là mô hình orchestration tối giản (single CLI) — mô phỏng đúng vai trò của Airflow/Prefect DAG nhưng gọn nhẹ, phù hợp quy mô 1 người làm portfolio. Ghi chú kiến trúc mở rộng: nếu lên production thật, bước tiếp theo là bọc lệnh CLI này vào 1 Airflow DAG chạy schedule hàng ngày.

### 3.2 Vai trò cụ thể của từng công nghệ trong stack

| Công nghệ | Vai trò trong pipeline | Vì sao chọn (so với lựa chọn khác) |
|---|---|---|
| **Google Drive API + Service Account** | Nguồn dữ liệu đầu vào (nơi các phòng ban thật sự upload file) | Mô phỏng đúng hiện trạng doanh nghiệp vừa/nhỏ chưa có hệ thống ERP tập trung |
| **Polars** | Engine xử lý dữ liệu chính (đọc CSV/Excel, transform, join, cast kiểu) | Nhanh hơn Pandas nhờ xử lý đa luồng (multi-threaded) + Lazy Evaluation, cú pháp gần SQL, tiết kiệm RAM |
| **Parquet** | Định dạng lưu trữ ở cả 3 lớp Bronze/Silver/Gold | Nén tốt, columnar (đọc nhanh khi chỉ cần vài cột), giữ được schema/kiểu dữ liệu — khác biệt rõ so với CSV |
| **Partitioning theo `run_date` (yyyymmdd)** | Cấu trúc thư mục đảm bảo Idempotency | Chạy lại pipeline không đè/nhân bản dữ liệu ngày khác, dễ rollback (xóa 1 thư mục ngày lỗi) |
| **DuckDB** | Query engine SQL chạy trực tiếp trên file Parquet, không cần Database Server | Cho phép Data Analyst tự truy vấn ad-hoc bằng SQL quen thuộc mà không cần ETL vào Postgres |
| **DBeaver** | GUI client kết nối DuckDB để xem/query dữ liệu | Công cụ quen thuộc với DA, giảm rào cản kỹ thuật khi thao tác Data Lakehouse |
| **Power BI** | Lớp trình bày (Presentation Layer) — dashboard cho Marketer/Ban giám đốc | Kết nối thẳng vào Gold layer (Parquet/DuckDB), là chuẩn công cụ BI phổ biến nhất trong doanh nghiệp Việt Nam |
| **argparse (CLI)** | Điểm vào duy nhất điều phối 3 lớp Bronze/Silver/Gold theo tham số `--layer`, `--run-date` | Đơn giản hóa orchestration cho quy mô 1 pipeline/1 người vận hành, dễ nâng cấp lên Airflow sau này |
| **pytest** | Kiểm thử logic transform (data mart, SCD Type 2) | Đảm bảo logic tính toán đúng trước khi merge code — tư duy production, không chỉ "chạy ra số" |
| **uuid + `ingest_log`** | Truy vết từng lần chạy pipeline (batch) | Phục vụ audit, debug khi số liệu sai lệch — ai/khi nào/nạp bao nhiêu dòng |

### 3.3 Các nguyên tắc Production-Ready đã áp dụng

| Nguyên tắc | Cách áp dụng trong dự án |
|---|---|
| **Idempotency** | Partition theo `run_date`; ghi đè trong đúng thư mục ngày, không append vô hạn |
| **Data Lineage** | 5 cột metadata Bronze được giữ nguyên xuyên suốt Silver → Gold |
| **Fail-safe ingestion** | Bronze ép toàn bộ về String để không sập pipeline vì lỗi kiểu dữ liệu ở nguồn |
| **Observability tối thiểu** | `ingest_log.parquet` ghi `rows_loaded, status, duration_sec` mỗi batch |
| **Secrets management** | `credentials.json` không được push Git (`.gitignore`), cấu hình qua `.env` |
| **Testing** | `pytest` cho logic Data Mart và logic SCD Type 2 (2 test tối thiểu) |
| **Reproducibility** | Quản lý dependency bằng `uv` + `pyproject.toml`, môi trường tách biệt khỏi bài tập hàng ngày |

---

## 4. Yêu cầu Dashboard & Chỉ số Marketing (Key Metrics & Visualization)

### 4.1 Cấu trúc Dashboard đề xuất (Power BI — 4 trang)

| Trang Dashboard | Actor chính | Nội dung |
|---|---|---|
| **1. Executive Overview** | Marketer, Ban giám đốc | Tổng doanh thu, tăng trưởng MoM/YoY, top 5 vùng/kênh dẫn đầu |
| **2. Sales vs Target** | Marketer, DA | So sánh doanh số thực tế vs chỉ tiêu theo vùng — tháng — nhân viên (dùng `mart_sales_vs_target`) |
| **3. Promotion & Distributor Performance** | Marketer | ROI khuyến mãi (`dim_promotion` × `fact_sales`), fill-rate & on-time delivery của NPP (`fact_distributor_orders`) |
| **4. Data Ops Monitoring** | Admin | Trạng thái từng batch chạy (`ingest_log`), số dòng lỗi/loại bỏ qua từng lớp |

### 4.2 Bộ chỉ số (KPI) chính & công thức

| Nhóm | Chỉ số | Công thức | Nguồn bảng |
|---|---|---|---|
| Doanh số | **Revenue thực tế** | `SUM(net_amount)` | `fact_sales` |
| Doanh số | **Growth rate MoM/YoY** | `(revenue_kỳ_này − revenue_kỳ_trước) / revenue_kỳ_trước` | `fact_sales` + `dim_date` |
| Target | **Achievement rate** | `SUM(net_amount) / SUM(target_revenue)` theo region+month | `fact_sales` × `fact_targets` |
| Target | **Variance** | `actual_revenue − target_revenue` | `mart_sales_vs_target` |
| Khuyến mãi | **Promotion Uplift** | `AVG(revenue trong kỳ KM) − AVG(revenue trước kỳ KM)` cùng sản phẩm/vùng | `fact_sales` × `dim_promotion` |
| Khuyến mãi | **Promotion ROI** | `(uplift_revenue − actual_cost_vnd) / actual_cost_vnd` | `fact_sales` × `dim_promotion` |
| Nhà phân phối | **Fill Rate** | `AVG(qty_delivered / qty_ordered)` | `fact_distributor_orders` |
| Nhà phân phối | **On-time Delivery %** | `COUNT(ontime_delivery=True) / COUNT(*)` | `fact_distributor_orders` |
| Khách hàng | **Return Rate** | `SUM(return_amount) / SUM(gross_amount)` | `fact_returns` × `fact_sales` |
| Nhân sự | **Doanh số/nhân viên theo đúng vùng lịch sử** | `SUM(net_amount)` join `dim_employees` (SCD2) theo `valid_from/valid_to` bao trùm `order_date` | `fact_sales` × `dim_employees` |
| Vận hành (Admin) | **Pipeline Success Rate** | `COUNT(status='success') / COUNT(*)` theo batch | `ingest_log` |

### 4.3 Ánh xạ nhu cầu Actor ↔ Metric

| Actor | Câu hỏi nghiệp vụ cần trả lời | Metric/Trang dashboard tương ứng |
|---|---|---|
| Marketer | "Vùng nào đang lệch target nhiều nhất tháng này?" | Achievement rate, Variance — Trang 2 |
| Marketer | "Chương trình khuyến mãi nào đáng chi tiếp?" | Promotion Uplift/ROI — Trang 3 |
| Data Analyst | "Cho tôi query thẳng SQL để dựng báo cáo tùy biến" | DuckDB/DBeaver trên `data/gold/*.parquet` |
| Admin | "Batch hôm qua có lỗi không, đọc thiếu file nào không?" | Pipeline Success Rate, `ingest_log` — Trang 4 |

---

## Phụ lục: Checklist nghiệm thu tổng thể (map với BRD)

- [ ] Toàn bộ 10 use case (UC-01 → UC-10) có Acceptance Criteria đo lường được, đã khớp với AC kỹ thuật trong `phase1/2/3_*.md`.
- [ ] Data Dictionary (mục 2.2) khớp 100% với cột thực tế trong `raw_data/`.
- [ ] Star Schema (mục 2.4) dựng đủ Dimension + Fact + 1 Data Mart, có SCD Type 2.
- [ ] Kiến trúc end-to-end (mục 3.1) chạy được bằng đúng 1 lệnh CLI `--layer all`.
- [ ] Dashboard Power BI có tối thiểu 2/4 trang đề xuất (ưu tiên trang 2 và 3 vì phục vụ đúng actor Marketer/DA nêu trong đề bài).
