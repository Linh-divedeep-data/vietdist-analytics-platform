# VDAP — Backlog Jira cho Space mới (theo cấu trúc thư mục Bronze đã tách package)

> Backlog chuẩn hóa để tạo trên **Jira Space MỚI + repo MỚI hoàn toàn** (không phải bản vá cho space/project hiện tại) — dùng file này làm input feed thẳng vào AI để gen issue trên space mới. Toàn bộ link Confluence và issue key `VDAP-xx` xuất hiện trong file là **placeholder/ví dụ định dạng**, không phải link/issue key thật của space cũ — điền lại bằng key project thực tế của space mới sau khi tạo Epic đầu tiên. Điều chỉnh **Sprint 0 → S0.1** và toàn bộ **Epic Phase 1 (Bronze)** theo cấu trúc thư mục mới:
> `config/{sources.py,settings.py}` + `src/extract/{parser,lineage,registry,orchestrator,ingest_log}.py` + `src/extract/unit_of_work/{base,src01..src10}.py`.
> Phase 2 (Silver), Phase 3 (Gold + CLI), Phase 3 (Dashboard) **giữ nguyên cấu trúc thư mục cũ** (không đổi tên file/module), nhưng đã qua 1 vòng review kỹ thuật (Senior BA + Principal DE góc nhìn) sửa 5 lỗ hổng nghiệp vụ/kỹ thuật thật phát hiện được — xem đánh dấu `_[SỬA]_`/`_[MỚI]_` rải trong Epic 2-4: (1) SCD2 `valid_to` không coalesce với `resign_date` → as-of join gán nhầm nhân viên đã nghỉ việc cho đơn hàng phát sinh sau ngày nghỉ; (2) cột `valid_from` bị thiếu hẳn 1 subtask dù là cột bắt buộc theo CLAUDE.md; (3) Silver ép ngày về 1 format cứng `%Y-%m-%d` trong khi Bronze String-hoá không đồng nhất giữa nguồn CSV (giữ text gốc) và Excel (Polars tự cast) → rủi ro NULL hàng loạt âm thầm; (4) không có validate schema/cột bắt buộc trước khi cast, và test coverage Silver = 0 (chỉ "check thủ công") trong khi đây là tầng nhiều logic nghiệp vụ nhất; (5) `fact_targets` (grain tháng) bị để "hoặc" tùy chọn cách join `dim_date` (grain ngày) thay vì chốt 1 phương án; (6) PII sống tới Gold nhưng Epic Dashboard không có bước rà soát trước khi `.pbix` rời máy cá nhân.
>
> **Vòng review thứ 2** (2026-08-02, đối chiếu lại với góc nhìn Principal DE) sửa thêm: (7) đánh số Epic Dashboard trùng "Phase 3" với Epic Gold → đổi đúng thành **Phase 4**; (8) FK không match khi join Fact→Dim chuẩn hóa từ "để NULL" sang **"-1 Unknown Member"** (chuẩn Kimball, tránh Power BI gộp lẫn nhiều lý do lỗi khác nhau vào 1 "blank"); (9) schema-drift validation dời từ Silver lên **Bronze** (fail-fast sớm nhất có thể, `status="schema_mismatch"` riêng trong `ingest_log`), Silver giữ lại làm lớp phòng vệ thứ 2; (10) PII chuyển từ "rà soát tay trước khi share `.pbix`" sang **drop cột PII ngay khi build Gold Dim** (kiểm soát kiến trúc, không phải quy trình — bảo vệ được cả người đọc thẳng file Parquet, không chỉ người mở `.pbix`); (11) thêm retry/backoff cho Google Drive API, exit-code/summary log khi pipeline fail (alerting tối thiểu, kéo từ P4.5 stretch lên core S0.5), quyết định tường minh hoãn partition Gold theo cột, và bổ sung `tests/test_parser.py`/`tests/test_lineage.py` (trước đó Bronze chỉ được test gián tiếp qua `test_unit_of_work.py`). 3 mục nice-to-have (backfill nhiều run_date, data dictionary Gold, rollback Gold build dở dang) ghi nhận ở mục riêng ngay dưới cây tổng hợp, chưa tách Story/Subtask.
>
> Format tuân thủ đúng `docs/jira.md` (Bước 3 Epic / Bước 4 Story / Bước 5 Subtask). Tạo issue theo đúng thứ tự phân cấp: **Epic → Story (parent=Epic key) → Subtask (parent=Story key)**. Đừng tạo Subtask trước khi Story cha đã có key. `_[MỚI]_` = nội dung mới hoàn toàn so với Jira gốc, `_[SỬA]_` = có chỉnh sửa, không đánh dấu = giữ nguyên 100%.

## Cây tổng hợp (Bước 6 docs/jira.md — duyệt trước khi tạo hàng loạt)

```
Epic: Sprint 0 — Project Setup & DevOps Foundation
├── S0.1 Repo Skeleton & Dependency Management   [SỬA — thêm subtask config/, src/extract package]
├── S0.2 Secrets & Environment Config             [giữ nguyên]
├── S0.3 CI Pipeline Skeleton                     [giữ nguyên]
├── S0.4 Dependency Vulnerability Scan Baseline   [giữ nguyên]
├── S0.5 Logging & Observability Skeleton         [SỬA — thêm exit code/alerting tối thiểu]
│   ├── src/logger.py: trace_id/timestamp/level format
│   ├── Wire logger into main.py, correlate batch_id as trace_id
│   └── Exit code + summary log phản ánh pipeline fail (core alerting tối thiểu)   [MỚI]
├── S0.6 README Setup Instructions                [giữ nguyên]
└── S0.7 Branching & Commit Convention            [giữ nguyên]

Epic: Phase 1 — Bronze Data Lake Ingestion         [SỬA TOÀN BỘ — theo package extract/ mới]
├── P1.1 Google Drive Discovery & Download (US-01)   [SỬA — thêm retry/backoff]
│   ├── Kết nối Google Drive Service Account + list_files_in_folder()   [MỚI]
│   ├── Implement download_file() qua Drive API + retry/backoff   [SỬA]
│   ├── Loop download toàn bộ 10 SRC vào data/raw/
│   └── Per-file error handling (status=failed, không crash batch)
├── P1.2 Read Raw Files theo unit_of_work per source   [SỬA — tách package + schema validation]
│   ├── config/sources.py — CSV_SOURCES/EXCEL_SOURCES                   [MỚI vị trí]
│   ├── extract/parser.py — read_csv_source()/read_excel_source() đơn nguồn
│   ├── config/sources.py — REQUIRED_COLUMNS + validate_schema() (fail-fast schema drift)   [MỚI]
│   ├── extract/unit_of_work/base.py — process_source() dùng chung, gọi validate_schema()      [SỬA]
│   ├── extract/unit_of_work/src01..src10.py — 10 module per-source     [MỚI]
│   ├── extract/registry.py — UNIT_OF_WORK dict map source→run()        [MỚI]
│   └── tests/test_parser.py — unit test read_csv/read_excel/validate_schema độc lập   [MỚI]
├── P1.3 Attach Lineage Metadata Columns (US-02)
│   ├── extract/lineage.py — attach_lineage()
│   ├── Wire attach_lineage() vào unit_of_work/base.py.process_source()
│   ├── uuid batch_id sinh 1 lần/run, share qua toàn bộ 10 nguồn
│   └── tests/test_lineage.py — unit test attach_lineage/cast_to_string độc lập   [MỚI]
├── P1.4 Write Bronze Parquet, Idempotent (US-01)   [SỬA — orchestrator.py + schema_mismatch status]
│   ├── extract/lineage.py — cast_to_string()
│   ├── config/settings.py — RAW_DIR/BRONZE_DIR/SILVER_DIR/GOLD_DIR     [MỚI]
│   ├── extract/orchestrator.py — run_bronze_ingestion() loop registry, phân biệt schema_mismatch/failed   [SỬA]
│   └── Idempotency check: rerun same run_date, row count stable
└── P1.5 Ingest Log (US-08)   [SỬA — thêm status="schema_mismatch"]
    ├── extract/ingest_log.py — build_ingest_log_record()+write_ingest_log()
    ├── Collect rows_loaded/status/duration_sec trong unit_of_work/base.py
    └── Wire write_ingest_log() vào orchestrator.py

Epic: Phase 2 — Silver Data Lake Cleansing
├── P2.1 Type Casting — Numeric & Date (US-03)        [SỬA — validate = lớp phòng vệ thứ 2 + date format per-source]
│   ├── Validate required columns (lớp phòng vệ thứ 2) + mapping format ngày theo từng nguồn   [SỬA]
│   ├── Strip thousand-separator + cast money/qty cols to Float64/Int64
│   ├── Cast date columns to pl.Date/Datetime theo format riêng từng nguồn   [SỬA]
│   └── pytest test_transform_silver.py: verify dtype + format ngày đúng   [SỬA]
├── P2.2 Text Standardization & Deduplication
│   ├── Strip+uppercase standardize text columns
│   ├── Drop duplicate rows in customer_master + other sources
│   └── Drop/handle rows with NULL customer_id/product_id keys
├── P2.3 NULL Handling — customer_master.tax_code
│   └── fill_null("UNKNOWN") on customer_master.tax_code
└── P2.4 Write Silver Parquet, Idempotent
    ├── write_parquet mỗi source vào data/silver/<run_date>/
    └── Idempotency check: rerun same run_date, no duplication/append

Epic: Phase 3 — Gold Star Schema & Production Hardening
├── P3.1 Dimension Tables (customers/products/distributors/date)   [SỬA — Unknown Member + drop PII]
│   ├── dim_customers + dim_products build w/ surrogate keys
│   ├── dim_distributors build w/ surrogate keys
│   ├── Thêm dòng "Unknown Member" (key = -1) vào mọi Dim   [MỚI]
│   ├── dim_date generate calendar dimension
│   └── Drop cột PII khỏi Gold Dim tables (thay vì rà soát tay lúc share)   [MỚI]
├── P3.2 SCD Type 2 — dim_employees (US-06)          [SỬA — valid_to coalesce resign_date]
│   ├── Sort by employee_id+effective_date, compute valid_from/valid_to (coalesce resign_date)   [SỬA]
│   ├── Derive is_current flag   [SỬA]
│   ├── Generate surrogate employee_key
│   └── Unit test SCD2 valid_to correctness, gồm case nghỉ việc (small fixture)   [SỬA]
├── P3.3 Fact Tables — fact_sales/fact_targets        [SỬA — fact_targets grain quyết dứt điểm + Unknown Member]
│   ├── fact_sales join dim_customers/dim_products/dim_employees(SCD2)/dim_date, left join+fill_null(-1)   [SỬA]
│   ├── fact_targets join dim_employees (as-of), giữ year/month riêng — KHÔNG ép qua dim_date   [SỬA]
│   └── Preserve _run_date,_batch_id lineage cols on fact tables
├── P3.4 fact_returns/fact_distributor_orders + dim_territory/dim_promotion   [SỬA — Unknown Member]
│   ├── dim_territory + dim_promotion build (+ Unknown Member)   [SỬA]
│   ├── fact_returns join dims (left join + fill_null(-1))   [SỬA]
│   └── fact_distributor_orders join dim_distributors/dim_products (left join + fill_null(-1))   [SỬA]
├── P3.5 Data Mart — mart_sales_vs_target (US-04)
│   ├── group_by/agg actual vs target revenue by region+month
│   ├── Compute variance_pct column
│   └── write_parquet mart_sales_vs_target to data/gold/<run_date>/
├── P3.6 Lazy Evaluation Refactor
│   └── Refactor read_parquet→scan_parquet in Silver+Gold modules
├── P3.7 Pytest — SCD2 + Data Mart logic              [SỬA — thêm case nghỉ việc]
│   ├── test_mart_sales_vs_target() với fixture nhỏ giả lập
│   ├── test_scd2_valid_to() kiểm tra valid_to đúng khi đổi vùng VÀ khi nghỉ việc   [SỬA]
│   └── Wire pytest vào CI pipeline skeleton (cập nhật S0.3)
└── P3.8 CLI Orchestration (main.py --layer --run-date)
    ├── argparse setup với --layer,--run-date, validate input
    ├── Wire --layer=bronze/silver/gold gọi đúng module tương ứng
    └── Wire --layer=all chạy tuần tự Bronze→Silver→Gold trong 1 lệnh

Epic: Phase 4 — Power BI Dashboard & Reporting Layer   [SỬA — đổi số Phase 3→4, PII giờ chỉ còn xác nhận]
├── P4.1 Power BI Data Source Connection Setup        [SỬA — PII control chính đã dời sang Gold P3.1]
│   ├── Connect Power BI to data/gold/<run_date>/ folder, load dim/fact tables
│   ├── Build relationships in model matching star schema
│   ├── Parameterize run_date so dashboard refreshes to latest gold folder
│   └── Xác nhận PII đã bị drop ở Gold (lớp phòng vệ thứ 2, không phải kiểm soát chính)   [SỬA]
├── P4.2 Dashboard Page: Sales vs Target (US-04)
│   ├── Matrix/bar visual: actual vs target revenue by region+month
│   ├── Achievement rate + Variance DAX measures
│   └── Region/month slicers
├── P4.3 Dashboard Page: Promotion & Distributor Performance (US-05)
│   ├── Promotion Uplift/ROI DAX measures + visual
│   ├── Fill Rate + On-time Delivery % visuals
│   └── Channel/region filters
├── P4.4 Dashboard Page: Executive Overview [Stretch]
│   ├── Total revenue + MoM/YoY growth measures
│   └── Top 5 region/channel visual
└── P4.5 Dashboard Page: Data Ops Monitoring [Stretch]
    ├── Load ingest_log across run_dates
    └── Pipeline Success Rate + batch status visual
```

## Ghi nhận backlog — không chặn, làm sau nếu còn thời gian

_(Từ review Principal DE, mức độ "nice-to-have" — không tạo Story/Subtask riêng ngay, ghi lại để không quên)_

* **Backfill nhiều `run_date` cùng lúc:** CLI (P3.8) hiện chỉ nhận đúng 1 `--run-date`/lần chạy. Muốn nạp lại lịch sử nhiều ngày phải gọi CLI nhiều lần (script ngoài tự loop) — chấp nhận được cho MVP, nâng cấp `--run-date-range` là việc sau.
* **Data dictionary cho Gold layer:** người đọc dashboard (Marketer/DA) không có tài liệu mô tả ý nghĩa từng cột ở `dim_*`/`fact_*`/`mart_sales_vs_target` ngoài code — nên có 1 file `docs/gold_data_dictionary.md` liệt kê cột + ý nghĩa + đơn vị, làm sau khi Epic 3 Done và schema đã ổn định (làm sớm quá sẽ phải sửa lại nhiều lần).
* **Rollback khi Gold build fail giữa chừng:** `write_parquet()` từng bảng trong P3.5 (Dim/Fact/Mart) không có transaction — nếu build fail ở bảng thứ 8/12, 7 bảng trước đã ghi thành công nằm lại trong `data/gold/<run_date>/`, tạo Gold folder "nửa vời" (thiếu bảng) mà không có cờ đánh dấu rõ ràng. Rerun cùng `run_date` sẽ ghi đè lại nên tự phục hồi được, nhưng nếu ai đó vô tình dùng Gold folder dở dang trước khi rerun thì dễ hiểu sai. Chấp nhận rủi ro này cho capstone; nếu làm thêm, hướng đơn giản nhất là ghi ra `_tmp` rồi rename cả thư mục khi xong toàn bộ (atomic ở mức filesystem).

---

# EPIC 0 — Sprint 0: Project Setup & DevOps Foundation

## EPIC — Sprint 0: Project Setup & DevOps Foundation

**Labels:** devops, infra, phase-0, sprint-0 | **Priority:** Medium

# 🚀 EPIC: Sprint 0 - Project Setup & DevOps Foundation

### 🎯 Objective & End-to-End Scope

* **Data Flow Scope:** README.md / BRD setup instructions ➔ Repo skeleton + CI + secrets + logging + docs ➔ Working local dev environment sẵn sàng cho Phase 1-3.
* **Epic AC:**

    * \[ \] Repo có `pyproject.toml`, `data/{raw,bronze,silver,gold}`, `src/`, `tests/`
    * \[ \] `.gitignore` chặn `credentials.json`, `.env`, `.venv`, `__pycache__`
    * \[ \] CI workflow chạy được (dù rỗng/placeholder)
    * \[ \] Dependency vulnerability baseline đã lưu
    * \[ \] Logging module chuẩn (trace_id, timestamp, level) tồn tại
    * \[ \] README có hướng dẫn setup, CONTRIBUTING.md có branch/commit convention
    
* **Epic DOD:** `uv sync` chạy sạch, `uv run python -c "import polars"` không lỗi, `git status` sau khi chạy pipeline không lộ secret/rác.

---

### 🔗 Dependencies, RACI & Timeline

* **Blocked By:** None
* **Blocks:** Epic 1 (Bronze Ingestion), Epic 2 (Silver Cleansing), Epic 3 (Gold Star Schema), Epic 4 (Dashboard) — mọi Feature Epic đều phụ thuộc nền tảng Sprint 0
* **Target Phase / Sprint:** Phase 0 / Sprint 0
* **Start Date / Due Date:** 2026-07-26 / 2026-07-28
* **Product Owner (sign-off):** Linh Nguyen
* **Required Reviewer(s):** Linh Nguyen (self-review, solo capstone)
* **On-call khi go-live:** Linh Nguyen
* **Confluence spec/decision log:** _(tạo page "Epic 0 — Sprint 0 Setup Spec & Decision Log" trên Confluence space mới, điền link vào đây sau khi tạo)_

---

### ⚠️ Risk Register

_(PROD do chứa Story xử lý credentials thật — Google Service Account)_

| Risk | Probability | Impact | Mitigation | Owner |
| --- | --- | --- | --- | --- |
| `credentials.json` bị commit lên Git trước khi `.gitignore` được cấu hình | M | H | Story S0.2 bắt buộc tạo `.gitignore` là subtask đầu tiên, trước khi đặt file credentials thật | Linh Nguyen |
| CI pipeline chạy "xanh" giả (không test thật gì) tạo cảm giác an toàn sai | M | L | CI workflow bắt buộc chạy `pytest --collect-only` để phát hiện lỗi collection sớm; test thật bổ sung ở Epic 3 (P3.7) | Linh Nguyen |
| Bỏ sót Dependency Vulnerability Scan baseline, mất mốc so sánh sau này | L | M | Baseline output lưu file trong `docs/`, AC yêu cầu artifact đính kèm | Linh Nguyen |

---

### 🔒 Non-Functional Requirements

* **Performance Target:** N/A (setup, không phải logic nghiệp vụ)
* **Security & Compliance:** `credentials.json`/`.env` không bao giờ được commit; `.env.example` không chứa giá trị thật
* **Rollout Strategy:** N/A — chạy local, không có môi trường deploy

---

### 📝 Assumptions Made

* \[2026-07-26\] Dự án là capstone/portfolio cá nhân (theo BRD), không có hạ tầng Production/CI-CD/Staging thật, không có SLA/on-call thật → áp dụng framing "Simulated Production Practice": vẫn làm đủ checklist DevOps chuẩn để luyện kỹ năng, nhưng NFR/SLA phản ánh đúng thực tế local/solo — Người duyệt: PO (Linh Nguyen, qua AskUserQuestion)
* \[2026-07-26\] RACI toàn dự án: PO = Reviewer = On-call = Linh Nguyen (solo) — Người duyệt: PO
* \[2026-07-26\] Tuần 1 của khóa học neo vào ngày 2026-07-26 (hôm nay = Thứ Hai Tuần 1) để tính ngày Sprint/Phase cụ thể từ timeline theo tuần trong README.md — Người duyệt: PO
* \[2026-07-26\] Không có tool tạo/liệt kê Jira Sprint (board sprint object) trong bộ MCP hiện có → không set được field Sprint gốc (customfield_10020) bằng ID thật; dùng Label (sprint-X) + Start date/Due date thay thế để track — Người duyệt: PO (giới hạn kỹ thuật, không phải lựa chọn)

---

### STORY — S0.1 Repo Skeleton & Dependency Management  _[SỬA]_

**Labels:** devops, infra, phase-0, sprint-0 | **Priority:** High

# 📋 USER STORY: Repo Skeleton & Dependency Management

### 👤 User Story

* **As a:** Data Engineer (Admin)
* **I want to:** một repo skeleton chuẩn + dependency quản lý qua `uv`
* **So that:** code Phase 1-3 chạy được ngay, không xung đột môi trường với bài tập khác

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** README.md mục "Cấu trúc thư mục (Nên có)"
* **⚙️ Processing:** `git init` → `uv init` + `uv add polars, google-api-python-client...` → tạo `data/{raw,bronze,silver,gold}`, `src/`, `tests/`
* **📤 Output:** Repo git skeleton, `uv run` không lỗi import, cấu trúc thư mục đủ theo README

---

### ✅ Definition of Ready

- [x] Spec/AC đã rõ (README.md mục Cấu trúc thư mục)
- [x] Không cần Design/Wireframe
- [x] Không có Dependency chặn
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** None / S0.2, S0.3, tất cả Epic 1-4
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 0 / 2026-07-27

---

### 🏷️ Metadata

* **Labels:** sprint-0, phase-0, infra, devops
* **Priority:** High
* **Story Points:** 2

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given repo mới, When chạy `uv sync`, Then toàn bộ dependency cài thành công
* \[ \] **Scenario 2 (Error/Exception):** Given thiếu thư mục `data/bronze`, When pipeline chạy write_parquet, Then không lỗi `FileNotFoundError` (thư mục đã tạo sẵn)

---

### 🔒 Non-Functional Requirements

N/A (Production Impact: Không)

---

### 📊 Observability Requirements

N/A

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

Cấu hình credentials/.env (xem S0.2)

### 🛠️ Technical Notes

`uv add google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv polars fastexcel pytest`

#### SUBTASK — Initialize git repo + first commit

**Labels:** infra, phase-0, sprint-0 | **Priority:** Medium

**Goal:** Khởi tạo git repository cho project (hiện chưa có `.git`).
**Input Spec:** Thư mục project hiện tại (README.md, docs/, credentials.json, gdrive_connector.py, raw_data/).
**Output/Deliverable:** Repo git với commit đầu tiên.
**Tech Stack:** git.
**File(s):** `.git/`
**Technical Steps:** `git init` → `git add README.md docs/ gdrive_connector.py` (KHÔNG add credentials.json) → `git commit -m "chore: initial commit"`.
**Acceptance Criteria:** `git log` hiện ít nhất 1 commit; `git status` không báo "not a git repository".
**💡 Vì sao cần:** Không làm → không có "sổ nhật ký" lưu lịch sử code, code hỏng không sửa lại được, không tạo nhánh/PR được, mọi bước sau (CI, review, sync Jira) đều cần git nên không làm được gì tiếp. Có nó → có nền tảng để lưu, revert, và làm việc nhóm trên code.

#### SUBTASK — Init pyproject.toml + uv add core deps

**Labels:** devops, infra, phase-0, sprint-0 | **Priority:** Medium

**Goal:** Khởi tạo dependency management bằng `uv`.
**Input Spec:** Danh sách lib cần: polars, google-api-python-client, google-auth-httplib2, google-auth-oauthlib, python-dotenv, fastexcel, pytest.
**Output/Deliverable:** `pyproject.toml` + `uv.lock` commit được.
**Tech Stack:** uv, Python 3.11+.
**File(s):** `pyproject.toml`
**Technical Steps:** `uv init` → `uv add polars google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv fastexcel pytest`.
**Acceptance Criteria:** `uv run python -c "import polars, googleapiclient"` không lỗi.
**💡 Vì sao cần:** Không làm → mỗi máy cài thư viện tự do, version lệch nhau — kiểu lỗi kinh điển "chạy trên máy tôi thì được mà". Có nó → khóa đúng version thư viện vào file, ai clone repo về cũng cài y hệt, không đoán mò khi có lỗi lạ.

#### SUBTASK — Create data/{raw,bronze,silver,gold}, src/, tests/ skeleton

**Labels:** infra, phase-0, sprint-0 | **Priority:** Medium

**Goal:** Tạo cấu trúc thư mục chuẩn theo README.md.
**Input Spec:** README.md mục "Cấu trúc thư mục (Nên có)".
**Output/Deliverable:** Thư mục `data/raw/`, `data/bronze/`, `data/silver/`, `data/gold/`, `src/`, `tests/` tồn tại (`.gitkeep` cho thư mục rỗng).
**Tech Stack:** shell/filesystem.
**File(s):** thư mục gốc repo.
**Technical Steps:** `mkdir -p data/{raw,bronze,silver,gold} src tests` + thêm `.gitkeep`.
**Acceptance Criteria:** `ls data/` hiện đủ 4 thư mục con.
**💡 Vì sao cần:** Không làm → code ghi file ra thư mục chưa tồn tại, lỗi ngay từ dòng đầu tiên ("No such file or directory") dù logic code đúng. Có nó → khung thư mục có sẵn, chạy code không cần tự tạo thư mục thủ công mỗi lần.

#### SUBTASK — Tạo config/ package + src/extract/ package skeleton  _[MỚI]_

**Labels:** backend, phase-1, sprint-1 | **Priority:** Medium

**Goal:** Dựng khung thư mục cho lớp Bronze theo kiến trúc tách package (không phải 1 file extract.py to) — sẵn cho Epic Phase 1 đổ logic vào từng file.
**Input Spec:** Cấu trúc thư mục mục tiêu (xem cây tổng hợp đầu file này).
**Output/Deliverable:** `config/__init__.py`, `config/sources.py` (rỗng/stub), `config/settings.py` (rỗng/stub); `src/extract/__init__.py`, `src/extract/parser.py`, `src/extract/lineage.py`, `src/extract/registry.py`, `src/extract/orchestrator.py`, `src/extract/ingest_log.py`; `src/extract/unit_of_work/__init__.py`, `src/extract/unit_of_work/base.py` — toàn bộ file tồn tại, nội dung thật đổ vào ở Epic Phase 1.
**Tech Stack:** Python package (`__init__.py`), filesystem.
**File(s):** config/, src/extract/, src/extract/unit_of_work/
**Technical Steps:**
1. `mkdir -p config src/extract/unit_of_work`
2. Tạo `__init__.py` rỗng ở mỗi package
3. Tạo stub file (docstring + `pass`/để trống) cho từng module liệt kê ở Deliverable — KHÔNG viết logic thật ở subtask này, chỉ dựng khung.
**Acceptance Criteria:** `python -c "import config.sources, config.settings, src.extract.parser, src.extract.lineage, src.extract.registry, src.extract.orchestrator, src.extract.ingest_log, src.extract.unit_of_work.base"` chạy không lỗi ImportError.
**💡 Vì sao cần:** Không làm → tới lúc code Bronze (Epic 1) mới nghĩ chỗ đặt file, dễ dồn hết logic vào 1 file to, sau này tách ra rất mất công (đổi import khắp nơi). Có nó → khung sẵn từ đầu, biết chính xác code nào nằm file nào trước khi viết dòng logic đầu tiên.

---

### STORY — S0.2 Secrets & Environment Config

**Labels:** compliance-nd13, devops, phase-0, pii, sprint-0 | **Priority:** High

# 📋 USER STORY: Secrets & Environment Config

### 👤 User Story

* **As a:** Admin
* **I want to:** `credentials.json` (Service Account thật) không lọt lên Git, `.env` trỏ đúng path, có `.env.example` cho dev khác
* **So that:** không rò rỉ chìa khóa truy cập Google Drive của công ty

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** `credentials.json` do giảng viên cấp
* **⚙️ Processing:** Tạo `.gitignore` baseline trước → tạo `.env.example` (placeholder) → đặt `credentials.json`/`​.env` thật, verify git-ignored
* **📤 Output:** `git status`/`git check-ignore` xác nhận không track credentials/​.env; `gdrive_connector.py` đọc được key qua `.env`

---

### ✅ Definition of Ready

* \[x\] Spec rõ (phase1_bronze_ingestion.md mục Setup Instructions)
* \[x\] Không cần Design
* \[x\] Dependency: Blocked By S0.1 (cần `.gitignore` baseline có sẵn) — Done trước khi bắt đầu
* \[x\] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** S0.1 / Epic 1 (P1.1)
* **Design Link:** N/A
* **Production Impact:** Có (credentials là chìa khóa truy cập Google Drive thật)
* **Target Sprint / Due Date:** Sprint 0 / 2026-07-27

---

### 🏷️ Metadata

* **Labels:** sprint-0, phase-0, devops, pii, compliance-nd13
* **Priority:** High
* **Story Points:** 2

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given `.gitignore` có `credentials.json`+`.env`, When `git add .`, Then 2 file không xuất hiện trong staged changes
* \[ \] **Scenario 2 (Error/Exception):** Given thiếu biến `GOOGLE_SERVICE_ACCOUNT_JSON` trong `.env`, When pipeline chạy, Then báo lỗi rõ ràng thay vì crash không rõ nguyên nhân

---

### 🔒 Non-Functional Requirements

* **Security:** `credentials.json`/`.env` không commit; `.env.example` liệt kê tên biến, không chứa giá trị thật

---

### 📊 Observability Requirements

N/A

---

### 🔁 Rollback Plan

Nếu lỡ commit credentials.json: revoke Service Account key trên Google Cloud Console + rotate key mới, sau đó `git filter-repo` xóa khỏi lịch sử git.

---

### ❌ Out of Scope

Implement logic gọi Drive API (xem Epic 1)

### 🛠️ Technical Notes

Không dùng cách nào khác ngoài `.gitignore` — không commit rồi xóa sau (vẫn còn trong git history).

#### SUBTASK — .gitignore baseline (credentials.json, .env, .venv, data/*)

**Labels:** compliance-nd13, devops, phase-0, pii, sprint-0 | **Priority:** Medium

**Goal:** .gitignore baseline chặn secret + file rác trước khi đặt credentials thật.
**Input Spec:** Chuẩn Python .gitignore (`.venv/`, `__pycache__/`, `.env`, `credentials.json`).
**Output/Deliverable:** File `.gitignore` ở repo root.
**Tech Stack:** git.
**File(s):** `.gitignore`
**Technical Steps:** Tạo `.gitignore` với `.venv/`, `__pycache__/`, `.env`, `credentials.json`, `data/raw/*`, `data/bronze/*`, `data/silver/*`, `data/gold/*` (giữ `.gitkeep`).
**Acceptance Criteria:** `git check-ignore -v credentials.json` trả về match.
**💡 Vì sao cần:** Không làm → chỉ cần 1 lần gõ nhầm `git add .` là file chìa khóa Google Drive thật bị đẩy công khai lên GitHub — không xóa sạch được nữa vì vẫn còn trong lịch sử git. Có nó → git tự động bỏ qua file secret, dù có lỡ tay cũng không dính.

#### SUBTASK — .env.example with placeholder vars

**Labels:** devops, phase-0, sprint-0 | **Priority:** Medium

**Goal:** Cung cấp `.env.example` liệt kê đủ biến môi trường cần thiết, không chứa giá trị thật.
**Input Spec:** phase1_bronze_ingestion.md bước 3 Setup Instructions (`GOOGLE_SERVICE_ACCOUNT_JSON`).
**Output/Deliverable:** File `.env.example` commit được (không có secret thật).
**Tech Stack:** dotenv convention.
**File(s):** `.env.example`
**Technical Steps:** Tạo `.env.example` với `GOOGLE_SERVICE_ACCOUNT_JSON=credentials.json` (placeholder path, không phải secret thật).
**Acceptance Criteria:** File `.env.example` được commit lên git, không chứa key/token thật nào.
**💡 Vì sao cần:** Không làm → người khác (hoặc chính mình sau vài tháng) không biết cần khai báo biến môi trường tên gì để chạy được project, phải dò code mới ra. Có nó → có file mẫu chỉ đúng tên biến cần điền, copy-đổi giá trị là chạy được.

#### SUBTASK — Place real credentials.json + .env, verify git-ignored

**Labels:** compliance-nd13, devops, phase-0, pii, sprint-0 | **Priority:** Medium

**Goal:** Đặt `credentials.json` thật + `.env` thật vào repo root, đảm bảo git không track.
**Input Spec:** File `credentials.json` do giảng viên cấp (Service Account key).
**Output/Deliverable:** `.env` với `GOOGLE_SERVICE_ACCOUNT_JSON=credentials.json`; cả 2 file bị git ignore.
**Tech Stack:** git, python-dotenv.
**File(s):** `credentials.json`, `.env`
**Technical Steps:** Copy credentials.json vào repo root → tạo `.env` thật → `git check-ignore -v credentials.json .env` → `git status` xác nhận không track.
**Acceptance Criteria:** `git add .` không stage 2 file này; `os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")` trả đúng path.
**💡 Vì sao cần:** Không làm → chưa có chìa khóa thật thì không gọi được Google Drive API, toàn bộ pipeline (từ Epic 1 trở đi) không chạy được bước nào. Có nó → có đủ chìa khóa để pipeline hoạt động thật, và đã verify chắc chắn không bị lộ ra ngoài.

> Story cha \[PROD\]: nếu bước này đổi kiến trúc lưu secret so với BRD, cập nhật Confluence decision log của Epic Sprint 0 (link ở đầu Epic).

---

### STORY — S0.3 CI Pipeline Skeleton

**Labels:** devops, infra, phase-0, sprint-0 | **Priority:** Medium

# 📋 USER STORY: CI Pipeline Skeleton

### 👤 User Story

* **As a:** Admin/Data Engineer
* **I want to:** một CI pipeline chạy build/lint/test tự động trên mỗi push
* **So that:** phát hiện lỗi sớm thay vì dồn tới cuối sprint

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** Source code repo (push/PR event)
* **⚙️ Processing:** GitHub Actions workflow: setup Python/uv → `uv sync` → lint → `pytest --collect-only`
* **📤 Output:** Workflow run "green" hiển thị trên tab Actions của repo

---

### ✅ Definition of Ready

- [x] Spec rõ (BRD §3.3 Testing/Reproducibility)
- [x] Không cần Design
- [x] Blocked By S0.1 (cần pyproject.toml tồn tại)
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** S0.1 / P3.7 (real pytest wired vào CI ở Epic 3)
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 0 / 2026-07-28

---

### 🏷️ Metadata

* **Labels:** sprint-0, phase-0, devops, infra
* **Priority:** Medium
* **Story Points:** 2

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given push lên branch bất kỳ, When workflow chạy, Then step `uv sync` + `pytest --collect-only` pass
* \[ \] **Scenario 2 (Error/Exception):** Given code có lỗi syntax, When workflow chạy, Then job fail rõ ràng (không silent pass)

---

### 🔒 Non-Functional Requirements

N/A (Production Impact: Không)

---

### 📊 Observability Requirements

N/A

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

Test logic nghiệp vụ thật (viết ở P3.7), deploy step (không có môi trường deploy)

### 🛠️ Technical Notes

`.github/workflows/ci.yml`, dùng `astral-sh/setup-uv` action.

#### SUBTASK — GitHub Actions workflow: lint+test job (placeholder)

**Labels:** devops, infra, phase-0, sprint-0 | **Priority:** Medium

**Goal:** Tạo workflow CI chạy trên push/PR.
**Input Spec:** `pyproject.toml` (từ S0.1).
**Output/Deliverable:** `.github/workflows/ci.yml`.
**Tech Stack:** GitHub Actions, astral-sh/setup-uv.
**File(s):** `.github/workflows/ci.yml`
**Technical Steps:** Job: checkout → setup-uv → `uv sync` → `uv run ruff check .` (hoặc lint đơn giản) → placeholder test step.
**Acceptance Criteria:** Workflow file valid YAML, hiện trong tab Actions khi push.
**💡 Vì sao cần:** Không làm → code lỗi cú pháp/import bị đẩy lên GitHub mà không ai biết, tới khi người khác pull về chạy mới phát hiện. Có nó → mỗi lần push, máy tự kiểm tra hộ, thấy lỗi ngay trên tab Actions trước khi merge.

#### SUBTASK — Verify pytest --collect-only runs clean in CI

**Labels:** devops, infra, phase-0, sprint-0 | **Priority:** Medium

**Goal:** Đảm bảo bước test trong CI ít nhất phát hiện lỗi collection (import error, syntax error).
**Input Spec:** `tests/` skeleton rỗng (từ S0.1).
**Output/Deliverable:** Step CI `uv run pytest --collect-only` pass.
**Tech Stack:** pytest, GitHub Actions.
**File(s):** `.github/workflows/ci.yml`, `tests/`
**Technical Steps:** Thêm step `uv run pytest --collect-only` vào workflow → verify chạy pass với `tests/` rỗng (hoặc file test placeholder).
**Acceptance Criteria:** CI job pass khi chưa có test thật; fail rõ ràng nếu có lỗi import trong `src/`.
**💡 Vì sao cần:** Không làm → CI "xanh" nhưng thực ra không kiểm tra được gì cả (chưa có test thật), tạo cảm giác an toàn giả. Có nó → ít nhất phát hiện được lỗi import/cú pháp sớm, trước khi có test thật ở P3.7.

---

### STORY — S0.4 Dependency Vulnerability Scan Baseline

**Labels:** devops, phase-0, sprint-0 | **Priority:** Low

# 📋 USER STORY: Dependency Vulnerability Scan Baseline

### 👤 User Story

* **As a:** Admin
* **I want to:** chạy scan lỗ hổng dependency lần đầu và lưu làm baseline
* **So that:** sau này biết có phát sinh lỗ hổng mới hay đã tồn tại từ đầu

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** `pyproject.toml`/`uv.lock` (từ S0.1)
* **⚙️ Processing:** Chạy `uv run pip-audit` (hoặc `uvx pip-audit`)
* **📤 Output:** File `docs/security_baseline_20260726.txt` chứa kết quả scan lần đầu

---

### ✅ Definition of Ready

- [x] Spec rõ (checklist Sprint 0 mục 3)
- [x] Không cần Design
- [x] Blocked By S0.1
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** S0.1 / None
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 0 / 2026-07-28

---

### 🏷️ Metadata

* **Labels:** sprint-0, phase-0, devops
* **Priority:** Low
* **Story Points:** 1

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given dependency đã cài, When chạy `pip-audit`, Then output được lưu vào `docs/security_baseline_<date>.txt`
* \[ \] **Scenario 2 (Error/Exception):** Given pip-audit tìm thấy lỗ hổng, When scan chạy, Then vẫn lưu baseline (không block Sprint 0), ghi chú lỗ hổng đã biết từ đầu

---

### 🔒 Non-Functional Requirements

N/A

---

### 📊 Observability Requirements

N/A

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

Fix lỗ hổng tìm thấy (chỉ ghi nhận baseline, xử lý là việc riêng)

### 🛠️ Technical Notes

`uvx pip-audit > docs/security_baseline_20260726.txt`

#### SUBTASK — Run pip-audit, save baseline to docs/security_baseline.txt

**Labels:** devops, phase-0, sprint-0 | **Priority:** Medium

**Goal:** Lưu baseline lỗ hổng dependency lần đầu.
**Input Spec:** `uv.lock` (từ S0.1).
**Output/Deliverable:** `docs/security_baseline_20260726.txt`.
**Tech Stack:** pip-audit.
**File(s):** `docs/security_baseline_20260726.txt`
**Technical Steps:** `uvx pip-audit > docs/security_baseline_20260726.txt` → commit file.
**Acceptance Criteria:** File tồn tại, chứa output scan (kể cả nếu 0 lỗ hổng).
**💡 Vì sao cần:** Không làm → sau này scan lại thấy có lỗ hổng, không biết là mới xuất hiện hay đã có sẵn từ đầu dự án, không đánh giá được mức độ nghiêm trọng thật. Có nó → có mốc so sánh gốc, lần scan sau chỉ cần đối chiếu là biết ngay cái gì mới.

---

### STORY — S0.5 Logging & Observability Skeleton

**Labels:** devops, phase-0, sprint-0 | **Priority:** Medium

# 📋 USER STORY: Logging & Observability Skeleton

### 👤 User Story

* **As a:** Admin
* **I want to:** log chuẩn hóa (trace_id, timestamp, level) xuyên suốt pipeline
* **So that:** khi có lỗi (kể cả local) có đủ thông tin debug thay vì mù thông tin

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** Sự kiện runtime của `main.py`/`extract.py`/`transform_*.py`
* **⚙️ Processing:** Module `src/logger.py` dùng `logging` chuẩn, format có `batch_id` (làm trace_id), timestamp, level; wire vào entrypoint CLI
* **📤 Output:** Log console có format nhất quán; `batch_id` khớp với `ingest_log.parquet` để cross-reference

---

### ✅ Definition of Ready

- [x] Spec rõ (BRD §3.3 Observability tối thiểu)
- [x] Không cần Design
- [x] Blocked By S0.1
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** S0.1 / Epic 1 (P1.5 ingest_log dùng chung batch_id)
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 0 / 2026-07-28

---

### 🏷️ Metadata

* **Labels:** sprint-0, phase-0, devops
* **Priority:** Medium
* **Story Points:** 2

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given pipeline chạy, When log dòng bất kỳ, Then dòng log có đủ `batch_id`, timestamp, level
* \[ \] **Scenario 2 (Error/Exception):** Given 1 file nguồn tải lỗi, When exception xảy ra, Then log level ERROR có traceback + batch_id tương ứng

---

### 🔒 Non-Functional Requirements

N/A (Production Impact: Không, local logging only)

---

### 📊 Observability Requirements

Log format chuẩn console (chưa cần kết nối Grafana/Datadog thật — không có stack đó ở dự án solo)

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

Kết nối observability stack ngoài (Grafana/Datadog) — không áp dụng cho portfolio local

### 🛠️ Technical Notes

`src/logger.py`: `logging.Formatter('%(asctime)s [%(levelname)s] [batch_id=%(batch_id)s] %(message)s')`

#### SUBTASK — src/logger.py: trace_id/timestamp/level format

**Labels:** devops, phase-0, sprint-0 | **Priority:** Medium

**Goal:** Module logging chuẩn hóa dùng chung toàn pipeline.
**Input Spec:** BRD §3.3 Observability tối thiểu.
**Output/Deliverable:** `src/logger.py` export hàm `get_logger(batch_id)`.
**Tech Stack:** Python `logging` stdlib.
**File(s):** `src/logger.py`
**Technical Steps:** Tạo `logging.Formatter` có `%(asctime)s [%(levelname)s] [batch_id=...] %(message)s`; hàm `get_logger()` gắn batch_id vào LoggerAdapter.
**Acceptance Criteria:** Import `src.logger`, gọi `get_logger("test-batch").info("hello")` in ra đúng format.
**💡 Vì sao cần:** Không làm → mỗi module tự in log kiểu riêng, khi có lỗi phải dò từng dòng không theo format nào, không biết dòng nào thuộc lần chạy nào. Có nó → mọi log trong pipeline cùng 1 định dạng thống nhất, dễ đọc/dễ lọc khi debug.

#### SUBTASK — Wire logger into main.py, correlate batch_id as trace_id

**Labels:** devops, phase-0, sprint-0 | **Priority:** Medium

**Goal:** Đảm bảo mọi module pipeline dùng chung 1 `batch_id` cho logging + ingest_log.
**Input Spec:** `src/logger.py` (subtask trước).
**Output/Deliverable:** `main.py` generate `batch_id` (uuid) 1 lần/run, truyền xuống các module con.
**Tech Stack:** Python, uuid.
**File(s):** `main.py`
**Technical Steps:** `main.py` tạo `batch_id = str(uuid.uuid4())` đầu chương trình → truyền vào `get_logger(batch_id)` + các hàm extract/transform.
**Acceptance Criteria:** Chạy `main.py`, mọi dòng log trong 1 lần chạy có cùng `batch_id`; `batch_id` khớp với ingest_log.parquet ở Epic 1.
**💡 Vì sao cần:** Không làm → mỗi module tự sinh mã lần chạy riêng, log console và file ingest_log.parquet không khớp nhau, không thể đối chiếu "lỗi này thuộc lần chạy nào". Có nó → 1 mã dùng chung xuyên suốt cả pipeline, đối chiếu log với ingest_log dễ dàng khi có sự cố.

#### SUBTASK — Exit code + summary log phản ánh pipeline fail (core alerting tối thiểu)  _[MỚI]_

**Labels:** devops, phase-0, sprint-0 | **Priority:** High

**Goal:** Đảm bảo pipeline fail LUÔN lộ ra được cho người/hệ thống ngoài biết — không chỉ nằm im trong file log mà không ai đọc. Đây là mức alerting tối thiểu; Slack/email thật là stretch, không có trong scope capstone hiện tại (không có webhook/SMTP server để tích hợp), nhưng cơ chế báo hiệu fail phải có ngay từ Sprint 0, không đợi tới P4.5.
**Input Spec:** `main.py` (CLI, P3.8), `records: list[dict]` (ingest_log) trả về từ mỗi layer.
**Output/Deliverable:** `main.py` thoát với `sys.exit(1)` + in dòng summary rõ ràng (`"FAILED: N/M nguồn lỗi ở layer=X, xem ingest_log.parquet"`) ra stderr nếu bất kỳ nguồn nào có `status != "success"` sau khi chạy xong 1 layer; `sys.exit(0)` + summary "OK" nếu toàn bộ thành công.
**Tech Stack:** Python `sys.exit()`, `src/logger.py`.
**File(s):** `main.py`
**Technical Steps:**
1. Sau mỗi layer (bronze/silver/gold) chạy xong, đếm số record có `status != "success"` trong list trả về
2. Có ít nhất 1 lỗi → log ERROR summary + `sys.exit(1)` (để script/cron ngoài — kể cả `&& echo fail` đơn giản — bắt được exit code khác 0)
3. Ghi rõ trong README/Technical Notes: đây là hook điểm để nối Slack/email thật sau này (`if exit_code != 0: send_alert(...)`), không tự làm tích hợp Slack thật trong capstone vì không có webhook thật để test
**Acceptance Criteria:** Giả lập 1 nguồn `status="failed"` → `main.py` thoát với exit code `1`, có dòng summary lỗi rõ ràng trên stderr; chạy thành công hết → exit code `0`.
**💡 Vì sao cần:** Không làm → pipeline chạy lỗi nhưng vẫn thoát bình thường như thành công, ai chạy tự động (cron, script ngoài) sẽ tưởng mọi thứ ổn, không ai biết để xử lý cho tới khi nhìn thấy hậu quả (báo cáo sai số liệu). Có nó → lỗi thì báo hiệu rõ ràng ngay lập tức, không phải tự mò log mới phát hiện.

---

### STORY — S0.6 README Setup Instructions

**Labels:** infra, phase-0, sprint-0 | **Priority:** Low

# 📋 USER STORY: README Setup Instructions

### 👤 User Story

* **As a:** Dev mới (hoặc chính mình sau này quay lại project)
* **I want to:** hướng dẫn setup rõ ràng từng bước trong README
* **So that:** không mất thời gian đoán lại cách chạy project

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** Các bước setup thực tế đã làm ở S0.1-S0.5
* **⚙️ Processing:** Viết section "Getting Started" trong README.md: clone → copy `.env.example`→`.env` → `uv sync` → chạy local
* **📤 Output:** README.md có section Getting Started đầy đủ, verify được bằng cách làm theo đúng từng bước

---

### ✅ Definition of Ready

- [x] Spec rõ
- [x] Không cần Design
- [x] Blocked By S0.1, S0.2
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** S0.1, S0.2 / None
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 0 / 2026-07-28

---

### 🏷️ Metadata

* **Labels:** sprint-0, phase-0, infra
* **Priority:** Low
* **Story Points:** 1

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given README mới, When 1 người làm theo đúng từng bước từ đầu, Then chạy được `uv run main.py --help` thành công
* \[ \] **Scenario 2 (Error/Exception):** Given thiếu `credentials.json`, When chạy pipeline theo README, Then README có ghi chú rõ lỗi thường gặp + cách xử lý

---

### 🔒 Non-Functional Requirements

N/A

---

### 📊 Observability Requirements

N/A

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

Hướng dẫn deploy production (không áp dụng)

### 🛠️ Technical Notes

Cập nhật README.md section mới, giữ nguyên nội dung khóa học hiện có.

#### SUBTASK — "Getting Started" section: clone→.env.example→uv sync→run local

**Labels:** infra, phase-0, sprint-0 | **Priority:** Medium

**Goal:** README có hướng dẫn setup từng bước.
**Input Spec:** Các bước thực tế từ S0.1, S0.2.
**Output/Deliverable:** Section "Getting Started" mới trong README.md.
**Tech Stack:** Markdown.
**File(s):** `README.md`
**Technical Steps:** Viết steps: clone repo → `cp .env.example .env` → điền `GOOGLE_SERVICE_ACCOUNT_JSON` → `uv sync` → `uv run main.py --layer all --run-date <date>`.
**Acceptance Criteria:** Người mới làm theo đúng thứ tự chạy được pipeline không cần hỏi thêm.
**💡 Vì sao cần:** Không làm → người mới (hoặc chính mình sau vài tháng quay lại) không biết bắt đầu từ đâu, phải dò từng file mới ráp lại được các bước. Có nó → làm theo đúng thứ tự trong README là chạy được ngay, không tốn thời gian hỏi lại hay đoán mò.

---

### STORY — S0.7 Branching & Commit Convention

**Labels:** infra, phase-0, sprint-0 | **Priority:** Low

# 📋 USER STORY: Branching & Commit Convention

### 👤 User Story

* **As a:** Admin/Data Engineer
* **I want to:** quy ước branch + commit message rõ ràng, ghi trong CONTRIBUTING.md
* **So that:** lịch sử git sạch, dễ rollback theo issue key khi cần

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** Chuẩn Conventional Commit + Git Flow phổ biến
* **⚙️ Processing:** Viết `CONTRIBUTING.md`: branch strategy (`feature/VDAP-xx-...`, `hotfix/...`), commit mẫu (`feat:`, `fix:`, `docs:`...)
* **📤 Output:** File `CONTRIBUTING.md` ở repo root

---

### ✅ Definition of Ready

- [x] Spec rõ
- [x] Không cần Design
- [x] Blocked By S0.1
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** S0.1 / None
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 0 / 2026-07-28

---

### 🏷️ Metadata

* **Labels:** sprint-0, phase-0, infra
* **Priority:** Low
* **Story Points:** 1

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given CONTRIBUTING.md, When commit mới được tạo theo mẫu `feat(VDAP-12): ...`, Then message khớp Conventional Commit format
* \[ \] **Scenario 2 (Error/Exception):** Given commit không theo convention, When review lại lịch sử git, Then dễ nhận diện commit lệch chuẩn để nhắc nhở (không có hook chặn tự động ở scope này)

---

### 🔒 Non-Functional Requirements

N/A

---

### 📊 Observability Requirements

N/A

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

Git hook tự động chặn commit sai convention (có thể làm sau, không bắt buộc Sprint 0)

### 🛠️ Technical Notes

Ví dụ: `feat(VDAP-15): implement download_file() Drive API`

#### SUBTASK — CONTRIBUTING.md: feature/hotfix branches + Conventional Commits

**Labels:** infra, phase-0, sprint-0 | **Priority:** Medium

**Goal:** Ghi rõ quy ước branch + commit để lịch sử git sạch, dễ trace theo issue key.
**Input Spec:** Conventional Commit spec, Git Flow phổ biến.
**Output/Deliverable:** `CONTRIBUTING.md`.
**Tech Stack:** Markdown.
**File(s):** `CONTRIBUTING.md`
**Technical Steps:** Viết branch strategy (`feature/VDAP-xx-slug`, `hotfix/VDAP-xx-slug`) + commit mẫu (`feat(VDAP-12): ...`, `fix(VDAP-20): ...`, `docs:`, `chore:`).
**Acceptance Criteria:** File tồn tại ở repo root, có ví dụ cụ thể cho từng loại.
**💡 Vì sao cần:** Không làm → mỗi commit đặt tên tùy hứng, nhìn lịch sử git không biết commit nào sửa gì, không link được với issue trên Jira. Có nó → nhìn vào 1 dòng commit là hiểu ngay đang sửa cái gì, thuộc ticket nào.

---

# EPIC 1 — Phase 1: Bronze Data Lake Ingestion  _[SỬA TOÀN BỘ]_

**Labels:** api, backend, phase-1, sprint-1 | **Priority:** Medium

# 🚀 EPIC: Phase 1 - Bronze Data Lake Ingestion  _[SỬA — theo package extract/ mới]_

### 🎯 Objective & End-to-End Scope

* **Data Flow Scope:** Google Drive (10 file SRC01-SRC10) ➔ `data/raw/` (thô, qua `gdrive_connector.py`) ➔ đọc + gắn lineage + ép String theo từng `unit_of_work` ➔ `data/bronze/<run_date>/` (Parquet, đủ 5 cột lineage) + `ingest_log.parquet`.
* **Thay đổi so với Epic gốc:** logic đọc/ghi Bronze tách khỏi 1 file `src/extract.py` duy nhất, chia theo trách nhiệm: `parser.py` (đọc), `lineage.py` (gắn metadata + ép String), `registry.py` (map nguồn → xử lý), `unit_of_work/` (logic riêng từng SRC, dùng chung `base.py`), `orchestrator.py` (vòng lặp chính + ghi Parquet), `ingest_log.py` (ghi log). `config/sources.py`, `config/settings.py` tách khỏi `src/` để tách config khỏi code logic.
* **Epic AC:**
    * [ ] Thư mục `data/raw/` chứa đủ 10 file gốc (SRC01-SRC10)
    * [ ] Thư mục `data/bronze/<run_date>/` chứa đủ 11 file `.parquet` (10 file data + `ingest_log.parquet`)
    * [ ] `pl.read_parquet('data/bronze/<run_date>/SRC01_sales_transactions.parquet')` có đủ 5 cột metadata `_source_file, _source_platform, _run_date, _ingested_at, _batch_id`, toàn bộ cột kiểu String
    * [ ] Rerun cùng `run_date` 2 lần: row count không đổi (idempotent)
    * [ ] `registry.UNIT_OF_WORK` có đúng 10 entry, khớp `config.sources.CSV_SOURCES ∪ EXCEL_SOURCES`
    * [ ] Nguồn thiếu cột bắt buộc so với `REQUIRED_COLUMNS` (Data Dictionary) bị chặn NGAY TẠI BRONZE — `status="schema_mismatch"` trong `ingest_log`, không ghi file Parquet cho nguồn đó, không lộ xuống Silver/Gold
* **Epic DOD:** `uv run python -m src.main --layer bronze --run-date <date>` chạy xong không lỗi, đủ AC trên, `uv run pytest` pass 100% cho toàn bộ test mới (`tests/test_registry.py`, `tests/test_unit_of_work.py`, `tests/test_ingest_log.py`, `tests/test_orchestrator.py`, `tests/test_parser.py`, `tests/test_lineage.py`). 2 file cuối bắt buộc thêm vì `parser.py` (đọc CSV/Excel, `validate_schema()`) và `lineage.py` (`attach_lineage()`, `cast_to_string()`) trước đó chỉ được test gián tiếp qua `test_unit_of_work.py` — không có test riêng cho từng hàm, dễ lọt lỗi khi 1 trong 2 file này đổi mà `unit_of_work/base.py` mock `read_fn` che mất.

---

### 🔗 Dependencies, RACI & Timeline

* **Blocked By:** Sprint 0 (Foundation) complete, đặc biệt S0.1 (config/ + extract package skeleton)
* **Blocks:** Epic 2 (Silver Cleansing) — Silver đọc từ `data/bronze/<run_date>/`
* **Target Phase / Sprint:** Phase 1 / Sprint 1
* **Product Owner (sign-off):** Linh Nguyen
* **Required Reviewer(s):** Linh Nguyen (self-review, solo capstone)

---

### ⚠️ Risk Register

* **Rủi ro:** logic tách nhiều file (`parser/lineage/registry/orchestrator/unit_of_work`) dễ tạo vòng import lẫn nhau (circular import) nếu không cẩn thận thứ tự phụ thuộc.
  **Giảm thiểu:** `unit_of_work/*.py` chỉ import từ `parser.py` + `lineage.py` (không import ngược `registry.py`/`orchestrator.py`); `registry.py` import từ `unit_of_work/`; `orchestrator.py` import từ `registry.py` + `ingest_log.py`. Không có cạnh ngược nào trong đồ thị phụ thuộc này.
* **Rủi ro:** đặt `FOLDER_ID`/`SERVICE_ACCOUNT_FILE` vào `config/settings.py` phá test dùng `importlib.reload(gdrive_connector)` (giá trị bị cache qua module trung gian).
  **Giảm thiểu:** `config/settings.py` CHỈ chứa path constants (`RAW_DIR/BRONZE_DIR/SILVER_DIR/GOLD_DIR`), KHÔNG chứa Drive credentials — giữ `FOLDER_ID`/`SERVICE_ACCOUNT_FILE` inline trong `gdrive_connector.py` như hiện tại.

---

### 🔒 Non-Functional Requirements

N/A (Production Impact: Không — chạy local, không traffic thật)

---

### 📝 Assumptions Made

* Mỗi `unit_of_work/srcXX_*.py` chỉ có trách nhiệm đọc 1 nguồn — không tự ghi Parquet (việc ghi thuộc `orchestrator.py`), giữ tách biệt đọc/ghi để dễ test bằng `tmp_path` fixture.
* `registry.py` dùng `dict` tĩnh (không phải dynamic discovery/plugin) — vì chỉ có đúng 10 nguồn cố định theo BRD, không cần cơ chế phức tạp hơn.

---

### STORY — P1.1 Google Drive Discovery & Download (US-01)

# 📋 USER STORY: P1.1 Google Drive Discovery & Download (US-01)

### 👤 User Story
* **As a:** Admin
* **I want to:** pipeline tự tải 10 file từ Google Drive về `data/raw/`
* **So that:** không phải tải tay mỗi ngày

---
### ⚙️ Context & Pre-conditions
* **Pre-conditions:** S0.1 (repo skeleton + gdrive_connector.py stub), S0.2 (Secrets Config — credentials.json + .env) đã Done
* **Design Link:** N/A
* **Production Impact:** Có (gọi Drive API thật bằng Service Account thật)

---
### 🏷️ Metadata
* **Labels:** backend, phase-1, sprint-1
* **Priority:** High
* **Story Points:** 5

---
### ✅ Acceptance Criteria (AC)
- [ ] **Scenario 1 (Happy path):** Given `FOLDER_ID` hợp lệ + credentials đúng, When chạy download loop, Then `data/raw/` có đủ 10 file SRC01-SRC10
- [ ] **Scenario 2 (Error/Exception):** Given 1 file bị lỗi permission/network giữa chừng, When download thất bại, Then log lỗi rõ ràng + record `status=failed` cho file đó, không crash toàn bộ batch

---
### 🔒 Non-Functional Requirements
**Security:** chỉ dùng scope Drive API read-only; không log nội dung `credentials.json`. **Reliability:** try/except per-file, 1 file lỗi không hỏng cả batch.

---
### 📊 Observability Requirements
Log mỗi lần download (file name, status, duration) qua `src/logger.py`, dùng chung `batch_id`.

---
### 🔁 Rollback Plan
Xóa `data/raw/` của run lỗi + `data/bronze/<run_date>/` tương ứng (nếu đã ghi), chạy lại `--layer bronze --run-date <date>` (idempotent).

---
### ❌ Out of Scope
Đọc file thành DataFrame (P1.2), gắn metadata (P1.3).

---
### 🛠️ Technical Notes
`gdrive_connector.py`: `service.files().get_media(fileId=file_id)` + `MediaIoBaseDownload`. Danh sách file lấy qua `list_files_in_folder(FOLDER_ID)`, phải duyệt hết `nextPageToken` (folder > 1 trang kết quả).

#### SUBTASK — Kết nối Google Drive Service Account + list_files_in_folder()  _[MỚI]_

**Labels:** backend, phase-1, sprint-1 | **Priority:** High

**Goal:** Khởi tạo Drive API client bằng Service Account (`credentials.json`) và lấy toàn bộ danh sách file trong `FOLDER_ID` nguồn — bước kết nối bắt buộc trước khi tải bất kỳ file nào.
**Input Spec:** `credentials.json` (Service Account key, từ S0.2), `GDRIVE_FOLDER_ID` trong `.env`.
**Output/Deliverable:** `src/gdrive_connector.py` — `get_drive_service()` (auth + build client) và `list_files_in_folder(folder_id)` trả về `list[dict]` gồm `id, name, mimeType` của toàn bộ file trong folder.
**Tech Stack:** `google-auth`, `googleapiclient.discovery.build()`, Drive API v3 (`files().list()`).
**File(s):** src/gdrive_connector.py
**Technical Steps:**
1. `Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)` với scope `drive.readonly`
2. `build("drive", "v3", credentials=credentials)`
3. `list_files_in_folder(folder_id)`: query `"'{folder_id}' in parents and trashed=false"`, duyệt hết `nextPageToken` (Drive API trả tối đa ~100 file/trang)
4. Module-level fail-fast: raise `RuntimeError` rõ ràng nếu thiếu `GDRIVE_FOLDER_ID` — không để lỗi HttpError 404 mơ hồ
**Acceptance Criteria:** `list_files_in_folder(FOLDER_ID)` trả đúng 10 file (SRC01-SRC10), kể cả khi folder có > 100 file (test bằng pagination giả lập qua `monkeypatch`).
**💡 Vì sao cần:** Không làm → không kết nối được Google Drive thì không biết folder có file gì để tải, cả pipeline đứng ngay bước đầu tiên. Có nó → có danh sách đầy đủ mọi file trong folder (kể cả khi folder nhiều hơn 100 file, Drive trả nhiều trang) để bước sau tải về.

#### SUBTASK — Implement download_file() qua Drive API + retry/backoff  _[SỬA — thêm retry]_

**Labels:** backend, phase-1, sprint-1 | **Priority:** High

**Goal:** Tải 1 file cụ thể từ Drive về `data/raw/` bằng `file_id`, chịu được lỗi tạm thời (rate limit, network timeout) thay vì fail ngay lần đầu.
**Input Spec:** `file_id`, `file_name` (từ `list_files_in_folder()`).
**Output/Deliverable:** `download_file(file_id, file_name, destination_folder="data/raw")` — trả về path file đã tải; retry tối đa 3 lần với exponential backoff cho lỗi tạm thời (HTTP 429/500/503, network timeout).
**Tech Stack:** `googleapiclient.http.MediaIoBaseDownload`, `googleapiclient.errors.HttpError`.
**File(s):** src/gdrive_connector.py
**Technical Steps:**
1. `drive_service.files().get_media(fileId=file_id)`
2. `MediaIoBaseDownload` ghi từng chunk vào `io.FileIO`
3. Bọc bước tải bằng retry loop: bắt `HttpError` với status `429`/`500`/`503` hoặc `TimeoutError` → sleep theo exponential backoff (`1s, 2s, 4s`), thử lại tối đa 3 lần; lỗi khác (403 permission, 404 not found) KHÔNG retry — raise ngay vì retry không giải quyết được
4. Hết 3 lần vẫn lỗi: xoá file dở dang (`os.remove`) rồi raise lại — không để lại file rác nửa vời
**Acceptance Criteria:** File tải về đúng nội dung gốc (so `pl.read_csv`/`pl.read_excel` số dòng khớp Drive gốc); lỗi giữa chừng không để lại file 0-byte/dở dang; giả lập (`monkeypatch`) 2 lần lỗi 429 rồi thành công ở lần thứ 3 → `download_file()` vẫn trả về path đúng, không raise; giả lập lỗi 403 → raise ngay lần đầu, không retry vô ích.
**💡 Vì sao cần:** Không làm → mạng chập chờn hoặc Google giới hạn tốc độ gọi API (rất hay gặp) làm cả lần chạy pipeline fail dù dữ liệu chẳng có vấn đề gì, phải chạy lại thủ công từ đầu. Có nó → tự thử lại vài lần cho lỗi tạm thời, chỉ báo lỗi thật khi chắc chắn không phải do mạng/rate-limit.

#### SUBTASK — Loop download toàn bộ 10 SRC vào data/raw/

**Labels:** backend, phase-1, sprint-1 | **Priority:** High

**Goal:** Nối `list_files_in_folder()` + `download_file()` thành vòng lặp tải hết 10 nguồn 1 lần.
**Input Spec:** Kết quả `list_files_in_folder(FOLDER_ID)`.
**Output/Deliverable:** `src/extract/parser.py` — `download_all_sources(folder_id, batch_id)` trả `list[dict]` record `{source_file, status, path, error}`.
**Tech Stack:** Python loop, `src/logger.py` (batch_id trace).
**File(s):** src/extract/parser.py
**Technical Steps:**
1. Loop `files = list_files_in_folder(folder_id)`
2. Với mỗi file: `download_file(file_info["id"], file_info["name"])`, ghi record `status=success`
3. Log qua `get_logger(batch_id)`
**Acceptance Criteria:** Chạy 1 lần tải đúng 10 file, trả về đúng 10 record.
**💡 Vì sao cần:** Không làm → phải gọi `download_file()` tay 10 lần cho 10 nguồn mỗi lần chạy pipeline. Có nó → 1 lệnh tải hết cả 10 nguồn, tự động lặp qua danh sách file lấy được ở bước trước.

#### SUBTASK — Per-file error handling (status=failed, không crash batch)

**Labels:** backend, phase-1, sprint-1 | **Priority:** Medium

**Goal:** 1 file lỗi (network/permission) không được làm crash các file còn lại.
**Input Spec:** `download_all_sources()` (subtask trước).
**Output/Deliverable:** Try/except quanh từng `download_file()` trong vòng lặp — lỗi ghi `status=failed, error=str(e)`, tiếp tục file kế tiếp.
**Tech Stack:** Python `try/except Exception`.
**File(s):** src/extract/parser.py
**Technical Steps:**
1. Bọc `download_file()` bằng try/except
2. Lỗi: `logger.error(...)`, append record `status=failed`
3. KHÔNG re-raise — vòng lặp tiếp tục file kế
**Acceptance Criteria:** Giả lập 1/10 file lỗi (`monkeypatch` raise `ConnectionError`) → 9 file còn lại vẫn `status=success`, record đủ 10, không exception nào thoát ra ngoài `download_all_sources()`.
**💡 Vì sao cần:** Không làm → 1 file lỗi (VD file bị xóa, mất mạng giữa chừng) làm cả 10 nguồn crash theo, dù 9 file kia hoàn toàn ổn — mất cả buổi chạy pipeline chỉ vì 1 file. Có nó → 1 nguồn lỗi chỉ đánh dấu riêng nguồn đó, 9 nguồn còn lại vẫn có dữ liệu bình thường.

---

### STORY — P1.2 Read Raw Files theo unit_of_work per source

# 📋 USER STORY: P1.2 Read Raw Files theo unit_of_work per source

### 👤 User Story
* **As a:** Admin/Data Engineer
* **I want to:** đọc 10 file CSV/XLSX vừa tải thành Polars DataFrame, mỗi nguồn qua 1 unit_of_work riêng
* **So that:** có dữ liệu trong bộ nhớ sẵn sàng gắn metadata + ghi Bronze, và cấu trúc code tách rõ theo từng nguồn để dễ sửa/test độc lập

---
### ⚙️ Context & Pre-conditions
* **Pre-conditions:** P1.1 Done (`data/raw/` có đủ 10 file), S0.1 subtask config/+extract skeleton Done
* **Design Link:** N/A
* **Production Impact:** Không (chỉ đọc file local đã tải)

---
### 🏷️ Metadata
* **Labels:** backend, phase-1, sprint-1
* **Priority:** High
* **Story Points:** 5

---
### ✅ Acceptance Criteria (AC)
- [ ] **Scenario 1 (Happy path):** Given 10 file trong `data/raw/`, When gọi `registry.UNIT_OF_WORK[source_file](...)` cho từng nguồn, Then thu được đúng 10 DataFrame, số dòng khớp file gốc, toàn bộ cột kiểu String
- [ ] **Scenario 2 (Error/Exception):** Given file Excel thiếu engine đọc, When `read_excel_source()` lỗi, Then báo lỗi rõ ràng gợi ý cài `fastexcel` thay vì crash mơ hồ
- [ ] **Scenario 3 (Error/Exception — schema drift, fail-fast ngay ở Bronze):** Given nguồn Google Drive đổi cấu trúc file (thêm/xóa/đổi tên cột so với Data Dictionary), When `process_source()` đọc xong file đó, Then validate cột NGAY tại Bronze — dừng ghi Bronze cho riêng nguồn đó, record `status="schema_mismatch"` trong `ingest_log` (không phải `"failed"` chung chung), 9 nguồn còn lại vẫn chạy bình thường. Không đợi tới Silver mới phát hiện.

---
### 🔒 Non-Functional Requirements
N/A (Production Impact: Không)

---
### 📊 Observability Requirements
N/A

---
### 🔁 Rollback Plan
N/A

---
### ❌ Out of Scope
Tải file (P1.1), gắn metadata (P1.3), ghi Bronze (P1.4).

---
### 🛠️ Technical Notes
`uv add fastexcel` nếu thiếu engine đọc Excel. `unit_of_work/*.py` KHÔNG tự đọc trực tiếp `pl.read_csv`/`pl.read_excel` — luôn qua `parser.read_csv_source()`/`read_excel_source()` để logic đọc chỉ tồn tại 1 nơi.

#### SUBTASK — config/sources.py — CSV_SOURCES/EXCEL_SOURCES  _[SỬA]_

**Labels:** backend, phase-1, sprint-1 | **Priority:** Medium

**Goal:** Khai báo danh sách 10 nguồn cố định (SRC01-SRC10), tách khỏi logic đọc file.
**Input Spec:** BRD mục 2.2 — danh sách 10 nguồn.
**Output/Deliverable:** `config/sources.py` — `CSV_SOURCES` (4 file: SRC01,03,06,09), `EXCEL_SOURCES` (6 file: SRC02,04,05,07,08,10).
**Tech Stack:** Python list constant.
**File(s):** config/sources.py
**Technical Steps:**
1. Liệt kê đúng 10 tên file theo BRD 2.2
2. Không import gì từ `src/` ở đây (tránh vòng phụ thuộc ngược)
**Acceptance Criteria:** `len(CSV_SOURCES) + len(EXCEL_SOURCES) == 10`, không trùng tên file.
**💡 Vì sao cần:** Không làm → tên 10 file nguồn bị viết rải rác/lặp lại trong nhiều file code khác nhau, sửa 1 tên nguồn phải tìm sửa nhiều chỗ, dễ sót. Có nó → khai báo đúng 1 chỗ duy nhất, chỗ khác chỉ import về dùng, sửa 1 lần là đủ.

#### SUBTASK — extract/parser.py — read_csv_source()/read_excel_source() đơn nguồn  _[SỬA]_

**Labels:** backend, phase-1, sprint-1 | **Priority:** High

**Goal:** Đọc ĐÚNG 1 file CSV hoặc Excel thành DataFrame, ép String ngay lúc đọc (fail-safe ingestion).
**Input Spec:** `name` (tên file), `raw_dir` (mặc định `data/raw`).
**Output/Deliverable:** `read_csv_source(name, raw_dir) -> pl.DataFrame` (dùng `infer_schema_length=0`); `read_excel_source(name, raw_dir) -> pl.DataFrame` (đọc rồi `.select(pl.all().cast(pl.String))`, bắt `ImportError` báo rõ thiếu `fastexcel`).
**Tech Stack:** Polars `pl.read_csv`/`pl.read_excel`.
**File(s):** src/extract/parser.py
**Technical Steps:**
1. `read_csv_source`: `pl.read_csv(path, infer_schema_length=0)` — ép String ngay từ lúc đọc, tránh ComputeError do suy luận kiểu sai
2. `read_excel_source`: `pl.read_excel(path).select(pl.all().cast(pl.String))`, bọc try/except `ImportError` → raise lại kèm hướng dẫn `uv add fastexcel`
3. File thiếu/hỏng: KHÔNG bắt lỗi ở đây — để lỗi tự nhiên nổi lên caller
**Acceptance Criteria:** Đọc đúng số dòng, toàn bộ cột kiểu String; file thiếu raise `FileNotFoundError` tự nhiên; test riêng lỗi thiếu engine Excel.
**💡 Vì sao cần:** Không làm → mỗi `unit_of_work` tự viết code đọc CSV/Excel riêng, 10 chỗ code gần giống nhau, sửa 1 lỗi đọc file phải sửa 10 nơi. Có nó → logic đọc file chỉ tồn tại đúng 1 chỗ, ép String ngay từ lúc đọc để tránh Polars tự đoán sai kiểu dữ liệu rồi báo lỗi khó hiểu.

#### SUBTASK — config/sources.py — REQUIRED_COLUMNS + extract/parser.py — validate_schema()  _[MỚI]_

**Labels:** backend, phase-1, sprint-1 | **Priority:** High

**Goal:** Chặn schema drift NGAY TẠI BRONZE, ngay sau khi đọc raw file — không đợi tới Silver (P2.1) mới phát hiện nguồn đổi cấu trúc. Đây là fail-fast gate đầu tiên của pipeline.
**Input Spec:** Data Dictionary (BRD §2.2) — danh sách cột bắt buộc từng nguồn.
**Output/Deliverable:** `config/sources.py` — `REQUIRED_COLUMNS: dict[str, list[str]]` (source_file → cột bắt buộc); `src/extract/parser.py` — `validate_schema(df, source_file)` raise `SchemaMismatchError(source_file, missing_cols, extra_cols)` nếu lệch.
**Tech Stack:** Python dict config, custom Exception class.
**File(s):** `config/sources.py`, `src/extract/parser.py`
**Technical Steps:**
1. Khai báo `REQUIRED_COLUMNS` cho cả 10 nguồn theo Data Dictionary
2. `validate_schema(df, source_file)`: so `set(df.columns)` với `set(REQUIRED_COLUMNS[source_file])`, thiếu cột nào raise `SchemaMismatchError` liệt kê rõ tên cột thiếu + tên nguồn (cột thừa chỉ log warning, không chặn — nguồn thêm cột mới không phải lỗi)
3. Định nghĩa `SchemaMismatchError(Exception)` riêng (không dùng `ValueError` chung chung) để orchestrator (P1.4) phân biệt được với lỗi đọc file thông thường, map đúng sang `status="schema_mismatch"` ở ingest_log
**Acceptance Criteria:** File Bronze test thiếu 1 cột bắt buộc → `validate_schema()` raise `SchemaMismatchError` nêu rõ cột thiếu; nguồn có thêm cột lạ (không nằm trong `REQUIRED_COLUMNS`) KHÔNG bị chặn, chỉ log.
**💡 Vì sao cần:** Không làm → bộ phận Sales/Marketing đổi cấu trúc file Excel (xóa/đổi tên 1 cột) mà không báo trước — pipeline vẫn "chạy thành công" bình thường, chỉ là dữ liệu bị thiếu/sai âm thầm, phải đợi đến khi ai đó phát hiện số liệu báo cáo sai mới lần ngược lại tìm nguyên nhân. Có nó → phát hiện ngay tại bước đầu tiên (Bronze), báo rõ thiếu cột gì của nguồn nào, không để lỗi trôi xuống các bước sau.

#### SUBTASK — extract/unit_of_work/base.py — process_source() dùng chung  _[SỬA — gọi validate_schema() ngay sau đọc]_

**Labels:** backend, phase-1, sprint-1 | **Priority:** High

**Goal:** Logic dùng chung cho mọi `unit_of_work`: đọc 1 file (qua hàm truyền vào) → validate schema (fail-fast) → gắn lineage → ép String → đo duration → dựng ingest_log record. Tránh lặp lại ở 10 file `src0X`.
**Input Spec:** `read_fn` (`read_csv_source`/`read_excel_source`), `source_file`, `raw_dir`, `run_date`, `batch_id`, `validate_schema()` (subtask trước).
**Output/Deliverable:** `process_source(read_fn, source_file, raw_dir, run_date, batch_id) -> tuple[pl.DataFrame, dict]` — DataFrame sẵn sàng ghi Bronze + 1 ingest_log record (`status=success`).
**Tech Stack:** `time.monotonic()` đo duration, gọi `parser.validate_schema()`, `lineage.attach_lineage()` + `lineage.cast_to_string()` (xem P1.3/P1.4).
**File(s):** src/extract/unit_of_work/base.py
**Technical Steps:**
1. `started = time.monotonic()`
2. `df = read_fn(source_file, raw_dir)`
3. `validate_schema(df, source_file)` — gọi NGAY SAU đọc, TRƯỚC khi gắn lineage — `SchemaMismatchError` propagate lên, KHÔNG bắt ở đây
4. `df = attach_lineage(df, source_file, run_date, batch_id)`
5. `df = cast_to_string(df)`
6. `duration_sec = time.monotonic() - started`
7. Dựng record qua `ingest_log.build_ingest_log_record(...)`, `status="success"`
8. Lỗi đọc file / `SchemaMismatchError` KHÔNG bắt ở đây — orchestrator (P1.4) quyết định fail-safe theo từng nguồn, phân biệt `status="failed"` (lỗi đọc/khác) vs `status="schema_mismatch"` (riêng `SchemaMismatchError`)
**Acceptance Criteria:** Trả về DataFrame toàn String + đủ 5 cột lineage; record đúng schema, `rows_loaded` khớp `df.height`; nguồn thiếu cột bắt buộc raise `SchemaMismatchError` trước khi kịp gắn lineage/ghi Bronze.
**💡 Vì sao cần:** Không làm → 10 module `src01..src10` mỗi cái tự viết lại y hệt các bước (đọc → validate → gắn lineage → ép String → đo thời gian), sửa 1 bước chung phải sửa 10 chỗ. Có nó → viết đúng 1 lần, 10 nguồn chỉ cần gọi lại, đảm bảo bước nào cũng đi qua đủ quy trình như nhau, không nguồn nào bị bỏ sót bước.

#### SUBTASK — extract/unit_of_work/src01..src10.py — 10 module per-source  _[MỚI]_

**Labels:** backend, phase-1, sprint-1 | **Priority:** Medium

**Goal:** 1 module riêng cho mỗi SRC01-SRC10, mỗi file chỉ khai báo `SOURCE_FILE` + gọi `process_source()` với đúng `read_fn` (csv hay excel).
**Input Spec:** `config.sources` (tên file), `parser.read_csv_source`/`read_excel_source`, `unit_of_work.base.process_source`.
**Output/Deliverable:** 10 file `src01_sales_transactions.py` .. `src10_promotion_program.py`, mỗi file export `SOURCE_FILE: str` + `run(raw_dir, run_date, batch_id) -> tuple[pl.DataFrame, dict]`.
**Tech Stack:** Python module, không thêm logic mới ngoài delegate sang `process_source()`.
**File(s):** src/extract/unit_of_work/src01_sales_transactions.py ... src10_promotion_program.py
**Technical Steps:**
1. Mỗi file: `SOURCE_FILE = "SRCxx_ten.csv|xlsx"`
2. `def run(raw_dir, run_date, batch_id): return process_source(read_csv_source hoặc read_excel_source, SOURCE_FILE, raw_dir, run_date, batch_id)`
3. SRC01/03/06/09 dùng `read_csv_source`, SRC02/04/05/07/08/10 dùng `read_excel_source`
**Acceptance Criteria:** Mỗi `run()` trả DataFrame toàn String + đủ 5 cột lineage, record `status=success` kèm `rows_loaded` đúng — test bằng fixture file giả trong `tmp_path`.
**💡 Vì sao cần:** Không làm → không có cách nào để nói "nguồn SRC01 dùng hàm đọc CSV, SRC02 dùng hàm đọc Excel" một cách tường minh, orchestrator không biết gọi hàm nào cho nguồn nào. Có nó → mỗi nguồn có 1 file riêng khai rõ ràng "tôi là nguồn nào, đọc kiểu gì", dễ tìm dễ sửa khi có vấn đề với đúng 1 nguồn cụ thể.

#### SUBTASK — extract/registry.py — UNIT_OF_WORK dict map source→run()  _[MỚI]_

**Labels:** backend, phase-1, sprint-1 | **Priority:** Medium

**Goal:** Bảng tra cứu source_file → hàm `unit_of_work.run()` tương ứng, dùng cho orchestrator (P1.4) loop qua 10 nguồn.
**Input Spec:** 10 module `unit_of_work/src01..src10.py`.
**Output/Deliverable:** `config/sources.py` không đổi; `src/extract/registry.py` — `UNIT_OF_WORK: dict[str, Callable]` = `{src01.SOURCE_FILE: src01.run, ...}` đủ 10 entry.
**Tech Stack:** Python dict, import trực tiếp 10 module.
**File(s):** src/extract/registry.py
**Technical Steps:**
1. Import cả 10 module `unit_of_work`
2. Dựng dict `{module.SOURCE_FILE: module.run}`
3. KHÔNG dùng dynamic discovery/importlib — 10 nguồn cố định, dict tĩnh đơn giản hơn và IDE/type-check theo dõi được
**Acceptance Criteria:** `len(UNIT_OF_WORK) == 10`, `set(UNIT_OF_WORK.keys()) == set(CSV_SOURCES) | set(EXCEL_SOURCES)`.
**💡 Vì sao cần:** Không làm → orchestrator (P1.4) phải viết `if source == "SRC01": ... elif source == "SRC02": ...` dài 10 nhánh mỗi lần muốn chạy đúng nguồn. Có nó → tra 1 phát trong dict là ra đúng hàm cần gọi, orchestrator chỉ cần loop qua dict, không cần biết chi tiết từng nguồn.

#### SUBTASK — tests/test_parser.py: unit test read_csv_source()/read_excel_source()/validate_schema() độc lập  _[MỚI]_

**Labels:** backend, phase-1, sprint-1 | **Priority:** Medium

**Goal:** Test riêng `parser.py`, không chỉ dựa vào việc nó được gọi gián tiếp qua `unit_of_work/base.py` (nơi `read_fn` thường bị mock, che luôn logic đọc file thật).
**Input Spec:** File CSV/Excel giả nhỏ trong `tmp_path` (pytest fixture).
**Output/Deliverable:** `tests/test_parser.py` — test `read_csv_source()`, `read_excel_source()` (đọc đúng số dòng, toàn String, lỗi thiếu `fastexcel` báo rõ), `validate_schema()` (raise `SchemaMismatchError` đúng khi thiếu cột, không raise khi đủ cột hoặc thừa cột lạ).
**Tech Stack:** pytest, `tmp_path` fixture, Polars.
**File(s):** `tests/test_parser.py`
**Technical Steps:** Tạo file CSV/Excel giả trong `tmp_path` → gọi từng hàm → assert output/exception đúng như Acceptance Criteria của từng subtask ở trên trong story này.
**Acceptance Criteria:** `uv run pytest tests/test_parser.py` pass 100%, độc lập không cần mock `unit_of_work/base.py`.
**💡 Vì sao cần:** Không làm → nếu chỉ test qua `unit_of_work` (nơi thường giả lập luôn cả bước đọc file), logic đọc file THẬT trong `parser.py` có thể có bug mà không test nào bắt được. Có nó → test thẳng vào đúng chỗ code đọc file thật, phát hiện lỗi ở đúng nơi phát sinh, không bị "test giả" che mất.

---

### STORY — P1.3 Attach Lineage Metadata Columns (US-02)

# 📋 USER STORY: P1.3 Attach Lineage Metadata Columns (US-02)

### 👤 User Story
* **As a:** Admin
* **I want to:** mỗi dòng dữ liệu có `_source_file`, `_source_platform`, `_run_date`, `_ingested_at`, `_batch_id`
* **So that:** truy vết được nguồn gốc khi có sai lệch số liệu

---
### ⚙️ Context & Pre-conditions
* **Pre-conditions:** P1.2 Done (`unit_of_work/base.py` tồn tại, cần wire lineage vào đó)
* **Design Link:** N/A
* **Production Impact:** Không

---
### 🏷️ Metadata
* **Labels:** backend, phase-1, sprint-1
* **Priority:** High
* **Story Points:** 2

---
### ✅ Acceptance Criteria (AC)
- [ ] **Scenario 1 (Happy path):** Given DataFrame thô (từ `read_csv_source`/`read_excel_source`), When gắn metadata, Then đủ 5 cột `_source_file, _source_platform, _run_date, _ingested_at, _batch_id`
- [ ] **Scenario 2 (Error/Exception):** Given chạy pipeline 1 lần cho cả 10 nguồn, When kiểm tra `batch_id`, Then cả 10 DataFrame trong cùng 1 lần chạy có cùng `batch_id` (sinh 1 lần ở `main.py`, không sinh lại giữa chừng)

---
### 🔒 Non-Functional Requirements
N/A

---
### 📊 Observability Requirements
N/A

---
### 🔁 Rollback Plan
N/A

---
### ❌ Out of Scope
Ghi Bronze Parquet (P1.4).

---
### 🛠️ Technical Notes
`attach_lineage(df, source_file, run_date, batch_id)` là helper thuần (pure function, không side-effect) tái sử dụng cho cả 10 nguồn qua `unit_of_work/base.py.process_source()` — không gọi trực tiếp trong 10 module `src0X` riêng lẻ.

#### SUBTASK — extract/lineage.py — attach_lineage()

**Labels:** backend, phase-1, sprint-1 | **Priority:** High

**Goal:** Gắn 5 cột metadata lineage bắt buộc của Bronze vào 1 DataFrame.
**Input Spec:** `df, source_file, run_date, batch_id`.
**Output/Deliverable:** `attach_lineage(df, source_file, run_date, batch_id) -> pl.DataFrame` — thêm `_source_file` (lit), `_source_platform` (`"google_drive"`), `_run_date` (lit), `_ingested_at` (`datetime.now(UTC)`, stamp tại thời điểm gọi — không dùng 1 timestamp chung cho cả batch), `_batch_id` (lit).
**Tech Stack:** Polars `with_columns()`, `pl.lit()`.
**File(s):** src/extract/lineage.py
**Technical Steps:**
1. `df.with_columns(pl.lit(source_file).alias("_source_file"), pl.lit("google_drive").alias("_source_platform"), pl.lit(run_date).alias("_run_date"), pl.lit(datetime.now(UTC)).alias("_ingested_at"), pl.lit(batch_id).alias("_batch_id"))`
2. Giữ nguyên toàn bộ cột gốc + số dòng — không lọc/biến đổi dữ liệu nghiệp vụ ở bước này
**Acceptance Criteria:** Đủ 5 cột đúng giá trị; số dòng/cột gốc không đổi; gọi 2 lần liên tiếp ra 2 giá trị `_ingested_at` khác nhau (stamp theo thời điểm gọi).
**💡 Vì sao cần:** Không làm → sau này số liệu sai/lệch, không biết dữ liệu đến từ file nào, ngày nào, lần chạy nào — không truy vết được nguồn gốc lỗi. Có nó → mỗi dòng dữ liệu đều "có dấu vân tay" riêng, lần nào cũng biết chính xác lấy từ đâu.

#### SUBTASK — Wire attach_lineage() vào unit_of_work/base.py.process_source()  _[SỬA]_

**Labels:** backend, phase-1, sprint-1 | **Priority:** High

**Goal:** Đảm bảo MỌI nguồn đều tự động qua `attach_lineage()` — không có đường tắt nào bỏ qua bước gắn lineage.
**Input Spec:** `unit_of_work/base.py` (P1.2), `lineage.attach_lineage()`.
**Output/Deliverable:** `process_source()` gọi `attach_lineage()` ngay sau khi đọc, trước khi `cast_to_string()`.
**Tech Stack:** Python function composition.
**File(s):** src/extract/unit_of_work/base.py
**Technical Steps:**
1. Import `attach_lineage` vào `base.py`
2. Chèn vào đúng vị trí: đọc → `attach_lineage` → `cast_to_string`
**Acceptance Criteria:** Chạy `unit_of_work/src01.run(...)` trả DataFrame đủ 5 cột lineage — không cần gọi `attach_lineage()` thủ công ở nơi khác.
**💡 Vì sao cần:** Không làm → hàm `attach_lineage()` tồn tại nhưng không ai gọi nó thì vô dụng — hoặc tệ hơn, có nguồn quên gọi, có nguồn không, dữ liệu thiếu dấu vết không đồng đều. Có nó → cắm sẵn vào quy trình chung, nguồn nào đi qua `process_source()` cũng tự động có đủ lineage, không ai có thể quên.

#### SUBTASK — uuid batch_id sinh 1 lần/run, share qua toàn bộ 10 nguồn

**Labels:** backend, phase-1, sprint-1 | **Priority:** Medium

**Goal:** `batch_id` phải là 1 UUID duy nhất cho cả lần chạy pipeline, không sinh lại giữa chừng cho từng nguồn.
**Input Spec:** `main.py` entrypoint.
**Output/Deliverable:** `main.py`: `batch_id = str(uuid.uuid4())` sinh đúng 1 lần ở đầu `main()`, truyền xuống mọi lời gọi `download_all_sources()`/`run_bronze_ingestion()`.
**Tech Stack:** Python `uuid.uuid4()`.
**File(s):** src/main.py
**Technical Steps:**
1. Sinh `batch_id` ngay đầu `main()`
2. Truyền `batch_id` cho toàn bộ hàm downstream, KHÔNG sinh mới ở bất kỳ đâu khác
**Acceptance Criteria:** Log console + `ingest_log.parquet` của cùng 1 lần chạy đều mang đúng 1 `batch_id`.
**💡 Vì sao cần:** Không làm → nếu mỗi nguồn tự sinh mã riêng, không thể nhóm 10 dòng ingest_log lại thành "1 lần chạy pipeline" — không trả lời được câu "lần chạy sáng nay tải được bao nhiêu nguồn, có lỗi không". Có nó → 1 mã đại diện cho cả lần chạy, dễ dàng lọc/nhóm dữ liệu theo từng batch.

#### SUBTASK — tests/test_lineage.py: unit test attach_lineage()/cast_to_string() độc lập  _[MỚI]_

**Labels:** backend, phase-1, sprint-1 | **Priority:** Medium

**Goal:** Test riêng `lineage.py`, không chỉ dựa vào việc nó được gọi gián tiếp trong `test_unit_of_work.py`.
**Input Spec:** DataFrame fixture nhỏ (2-3 dòng, vài cột giả).
**Output/Deliverable:** `tests/test_lineage.py` — test `attach_lineage()` (đủ 5 cột, `_ingested_at` khác nhau giữa 2 lần gọi) và `cast_to_string()` (toàn bộ dtype ra String, kể cả cột Datetime).
**Tech Stack:** pytest, Polars.
**File(s):** `tests/test_lineage.py`
**Technical Steps:** Fixture DataFrame nhỏ → gọi `attach_lineage()` assert đủ cột + giá trị đúng → gọi `cast_to_string()` assert toàn bộ `df.dtypes == pl.String`.
**Acceptance Criteria:** `uv run pytest tests/test_lineage.py` pass 100%, độc lập không cần mock `unit_of_work/base.py`.
**💡 Vì sao cần:** Không làm → test qua `unit_of_work` có thể che mất bug thật trong `attach_lineage()`/`cast_to_string()` nếu fixture không đủ đa dạng. Có nó → test thẳng vào 2 hàm lõi này, chắc chắn chúng hoạt động đúng độc lập với mọi thứ khác.

---

### STORY — P1.4 Write Bronze Parquet, Idempotent (US-01)

# 📋 USER STORY: P1.4 Write Bronze Parquet, Idempotent (US-01)

### 👤 User Story
* **As a:** Admin
* **I want to:** ghi dữ liệu ra `data/bronze/<run_date>/` dưới dạng Parquet, ép toàn bộ cột về String
* **So that:** dữ liệu Bronze an toàn (fail-safe) và chạy lại nhiều lần không nhân bản

---
### ⚙️ Context & Pre-conditions
* **Pre-conditions:** P1.2 + P1.3 Done (`registry.py`, `unit_of_work/` trả DataFrame đủ lineage)
* **Design Link:** N/A
* **Production Impact:** Không (ghi file local)

---
### 🏷️ Metadata
* **Labels:** backend, phase-1, sprint-1
* **Priority:** High
* **Story Points:** 3

---
### ✅ Acceptance Criteria (AC)
- [ ] **Scenario 1 (Happy path):** Given `registry.UNIT_OF_WORK` đủ 10 entry, When chạy `orchestrator.run_bronze_ingestion(run_date, batch_id)`, Then `data/bronze/<run_date>/` có đủ 10 file `.parquet`, tất cả cột kiểu String
- [ ] **Scenario 2 (Error/Exception):** Given chạy lại cùng `run_date` 2 lần liên tiếp, When so sánh row count từng file, Then không đổi (idempotent — ghi đè, không nhân bản)

---
### 🔒 Non-Functional Requirements
N/A

---
### 📊 Observability Requirements
N/A

---
### 🔁 Rollback Plan
Xóa `data/bronze/<run_date>/` bị lỗi, chạy lại `--layer bronze --run-date <date>`.

---
### ❌ Out of Scope
Ghi ingest_log (P1.5).

---
### 🛠️ Technical Notes
Partition folder: `run_date.replace("-", "")` (VD `2026-08-01` → `20260801`), khớp pattern `data/bronze/20260722/SRC01_sales_transactions.parquet` trong `phase1_bronze_ingestion.md`.

#### SUBTASK — extract/lineage.py — cast_to_string()  _[SỬA]_

**Labels:** backend, phase-1, sprint-1 | **Priority:** High

**Goal:** Ép TOÀN BỘ cột về String ngay trước khi ghi Bronze — bắt buộc theo nguyên tắc fail-safe ingestion (CLAUDE.md), kể cả cột `_ingested_at` (Datetime) do `attach_lineage()` để lại.
**Input Spec:** DataFrame đã qua `attach_lineage()`.
**Output/Deliverable:** `cast_to_string(df) -> pl.DataFrame` — `df.select(pl.all().cast(pl.String))`.
**Tech Stack:** Polars `pl.all().cast(pl.String)`.
**File(s):** src/extract/lineage.py
**Technical Steps:**
1. `df.select(pl.all().cast(pl.String))`
2. Gọi SAU `attach_lineage()` trong `unit_of_work/base.py.process_source()` (đã wire ở P1.3) — đóng lại invariant "toàn String" của Bronze
**Acceptance Criteria:** Sau `cast_to_string()`, `all(dtype == pl.String for dtype in df.dtypes)` đúng cho mọi cột kể cả `_ingested_at`.
**💡 Vì sao cần:** Không làm → 1 cột số/ngày ở nguồn có giá trị lạ (VD chữ lẫn trong cột số lượng) làm cả pipeline crash ngay lúc ghi Bronze, vì Polars cố giữ đúng kiểu dữ liệu suy luận được. Có nó → mọi thứ về String hết, không có kiểu dữ liệu nào có thể "sai" ở bước này — dữ liệu bẩn tới đâu vẫn ghi được vào Bronze, xử lý sạch để ở bước Silver sau.

#### SUBTASK — config/settings.py — RAW_DIR/BRONZE_DIR/SILVER_DIR/GOLD_DIR  _[MỚI]_

**Labels:** backend, phase-1, sprint-1 | **Priority:** Medium

**Goal:** Tập trung đường dẫn 4 lớp Data Lake vào 1 nơi thay vì hardcode string rải rác (`"data/raw"`, `"data/bronze"`...) trong `parser.py`/`orchestrator.py`.
**Input Spec:** Kiến trúc Medallion (CLAUDE.md): `data/{raw,bronze,silver,gold}`.
**Output/Deliverable:** `config/settings.py` — `RAW_DIR = "data/raw"`, `BRONZE_DIR = "data/bronze"`, `SILVER_DIR = "data/silver"`, `GOLD_DIR = "data/gold"`.
**Tech Stack:** Python constants — KHÔNG dùng `os.getenv()` ở đây.
**File(s):** config/settings.py
**Technical Steps:**
1. Khai báo 4 constant path
2. **Không** đặt `FOLDER_ID`/`SERVICE_ACCOUNT_FILE` (Drive credentials) vào file này — nếu `gdrive_connector.py` đọc 2 giá trị đó qua module trung gian, `importlib.reload(gdrive_connector)` trong test sẽ không re-eval được env var mới (giá trị bị cache ở `config.settings`), phá test fail-fast validation. Giữ 2 giá trị đó inline trong `gdrive_connector.py`
**Acceptance Criteria:** `parser.py` và `orchestrator.py` import `RAW_DIR`/`BRONZE_DIR` từ đây thay vì hardcode string; test `gdrive_connector` fail-fast (`importlib.reload`) vẫn pass sau khi thêm file này.
**💡 Vì sao cần:** Không làm → đường dẫn `"data/bronze"` gõ tay rải rác nhiều file, sau này muốn đổi tên thư mục phải tìm-sửa từng chỗ, dễ sót 1 chỗ gây lỗi khó hiểu. Có nó → đổi đường dẫn chỉ cần sửa đúng 1 dòng ở đây, mọi nơi khác tự động dùng theo.

#### SUBTASK — extract/orchestrator.py — run_bronze_ingestion() loop registry  _[MỚI]_

**Labels:** backend, phase-1, sprint-1 | **Priority:** High

**Goal:** Vòng lặp chính của Bronze: chạy từng `unit_of_work` trong `registry.UNIT_OF_WORK`, ghi mỗi DataFrame thành 1 file Parquet vào `data/bronze/<run_date>/` (partition yyyymmdd, ghi đè = idempotent).
**Input Spec:** `run_date`, `batch_id`, `registry.UNIT_OF_WORK` (P1.2), `config.settings.RAW_DIR/BRONZE_DIR`.
**Output/Deliverable:** `run_bronze_ingestion(run_date, batch_id, raw_dir=RAW_DIR, bronze_dir=BRONZE_DIR) -> list[dict]` (trả list ingest_log record — dùng ở P1.5).
**Tech Stack:** Polars `write_parquet()`, `os.makedirs(exist_ok=True)`.
**File(s):** src/extract/orchestrator.py
**Technical Steps:**
1. `out_dir = os.path.join(bronze_dir, run_date.replace("-", ""))`, `os.makedirs(out_dir, exist_ok=True)`
2. Loop `for source_file, run_unit in UNIT_OF_WORK.items()`
3. `df, record = run_unit(raw_dir, run_date, batch_id)` → `df.write_parquet(os.path.join(out_dir, f"{name_khong_duoi}.parquet"))`
4. 1 nguồn lỗi: try/except phân biệt 2 loại — bắt `SchemaMismatchError` riêng trước (record `status="schema_mismatch"`), các exception khác (đọc/ghi file) record `status="failed"` — cả 2 đều KHÔNG crash cả batch, tiếp tục nguồn kế (cùng pattern `download_all_sources`)
5. Nguồn bị `schema_mismatch`/`failed` → KHÔNG ghi file `.parquet` cho nguồn đó (không ghi Bronze dữ liệu nghi ngờ sai schema)
6. Trả về `records` (list ingest_log — nối với P1.5)
**Acceptance Criteria:** Chạy xong `data/bronze/<run_date>/` có đủ 10 file `.parquet` (happy path); giả lập 1 nguồn lỗi đọc/ghi vẫn ra đủ 9 file còn lại + record `status=failed`; giả lập 1 nguồn thiếu cột bắt buộc → record `status="schema_mismatch"` riêng biệt, không lẫn với `status=failed`, và KHÔNG có file `.parquet` cho nguồn đó.
**💡 Vì sao cần:** Không làm → không có ai đứng ra "chỉ huy" chạy lần lượt 10 nguồn rồi ghi ra Bronze — mỗi nguồn chạy tay riêng lẻ, dễ quên/bỏ sót, không tổng hợp được kết quả cả lần chạy. Có nó → 1 hàm chạy hết cả 10 nguồn, tự biết nguồn nào ok, nguồn nào lỗi, nguồn nào sai schema — không cần người ngồi canh từng bước.

#### SUBTASK — Idempotency check: rerun same run_date, row count stable

**Labels:** backend, phase-1, sprint-1 | **Priority:** Medium

**Goal:** Verify chạy lại cùng `run_date` không nhân bản dữ liệu.
**Input Spec:** `run_bronze_ingestion()` đã hoạt động (subtask trước).
**Output/Deliverable:** Test + bằng chứng: rerun 2 lần liên tiếp cùng `run_date`, row count 10 file không đổi.
**Tech Stack:** Polars, pytest (`tmp_path`, `monkeypatch`).
**File(s):** tests/test_orchestrator.py
**Technical Steps:**
1. Chạy `run_bronze_ingestion(run_date="X", batch_id="b1", ...)`
2. Chạy lại `run_bronze_ingestion(run_date="X", batch_id="b2", ...)` — batch_id khác, run_date giống
3. So sánh `pl.read_parquet(...).shape[0]` trước/sau — phải bằng nhau, file không nhân bản (glob đúng 1 file/nguồn trong thư mục)
**Acceptance Criteria:** Row count không đổi giữa 2 lần chạy; `glob("SRCxx*.parquet")` trong thư mục run_date chỉ ra đúng 1 file.
**💡 Vì sao cần:** Không làm → chạy lại pipeline (vì lỗi giữa chừng, hoặc chỉ để test) có nguy cơ nhân đôi dữ liệu (dữ liệu cũ + dữ liệu mới cộng dồn), báo cáo sai số liệu mà không ai biết vì sao. Có nó → chắc chắn chạy lại bao nhiêu lần cũng ra đúng 1 bản dữ liệu cho mỗi ngày, không sợ chạy nhầm 2 lần.

---

### STORY — P1.5 Ingest Log (US-08)

# 📋 USER STORY: P1.5 Ingest Log (US-08)

### 👤 User Story
* **As a:** Admin
* **I want to:** có `ingest_log` cho từng batch
* **So that:** biết ngay file nào tải lỗi, đọc được bao nhiêu dòng, chạy mất bao lâu

---
### ⚙️ Context & Pre-conditions
* **Pre-conditions:** P1.4 Done (`orchestrator.py` chạy được, cần wire ghi log vào cuối)
* **Design Link:** N/A
* **Production Impact:** Không

---
### 🏷️ Metadata
* **Labels:** backend, phase-1, sprint-1
* **Priority:** High
* **Story Points:** 2

---
### ✅ Acceptance Criteria (AC)
- [ ] **Scenario 1 (Happy path):** Given pipeline chạy xong, When đọc `ingest_log.parquet`, Then có đủ 10 dòng (1/nguồn), cột `status='success'`, `rows_loaded` khớp số dòng thật
- [ ] **Scenario 2 (Error/Exception):** Given 1 nguồn lỗi đọc/ghi (không phải schema) ở orchestrator, When ghi ingest_log, Then dòng tương ứng có `status='failed'`, `rows_loaded=0`, không làm crash việc ghi log của 9 nguồn còn lại
- [ ] **Scenario 3 (Error/Exception):** Given 1 nguồn bị `SchemaMismatchError` (P1.2), When ghi ingest_log, Then dòng tương ứng có `status='schema_mismatch'` — phân biệt rõ với `'failed'` để Admin biết ngay là do đổi cấu trúc file, không phải lỗi mạng/tạm thời

---
### 🔒 Non-Functional Requirements
N/A

---
### 📊 Observability Requirements
`batch_id` trong ingest_log khớp với `batch_id` trong log console (S0.5) để cross-reference khi debug.

---
### 🔁 Rollback Plan
N/A (file log, không phải dữ liệu nghiệp vụ — xóa cùng `data/bronze/<run_date>/` nếu cần chạy lại).

---
### ❌ Out of Scope
Dashboard "Data Ops Monitoring" hiển thị ingest_log (Epic 4, P4.5).

---
### 🛠️ Technical Notes
Ghi CÙNG thư mục `data/bronze/<run_date>/` (không phải file riêng ngoài partition) để giữ idempotency — 1 file `ingest_log.parquet`/run_date, ghi đè không append.

#### SUBTASK — extract/ingest_log.py — build_ingest_log_record()+write_ingest_log()  _[SỬA]_

**Labels:** backend, phase-1, sprint-1 | **Priority:** High

**Goal:** Dựng 1 dòng ingest_log record + ghi toàn bộ record thành `ingest_log.parquet`.
**Input Spec:** `batch_id, source_file, rows_loaded, status, duration_sec` (từ `unit_of_work/base.py`, xem subtask kế).
**Output/Deliverable:** `build_ingest_log_record(batch_id, source_file, rows_loaded, status, duration_sec, source_platform="google_drive") -> dict` (7 cột: `batch_id, source_name, source_file, source_platform, rows_loaded, status, duration_sec`; `source_name` = `source_file` bỏ đuôi file); `write_ingest_log(records, bronze_run_dir) -> str` — ghi/ghi đè `ingest_log.parquet`.
**Tech Stack:** Polars `pl.DataFrame(records).write_parquet()`.
**File(s):** src/extract/ingest_log.py
**Technical Steps:**
1. `build_ingest_log_record`: dựng dict đúng 7 field, `source_name = os.path.splitext(source_file)[0]`
2. `write_ingest_log`: `os.makedirs(bronze_run_dir, exist_ok=True)`, `pl.DataFrame(records, schema=INGEST_LOG_COLUMNS).write_parquet(path)` — ghi đè (không append) để giữ idempotency
**Acceptance Criteria:** Đọc lại `ingest_log.parquet` đủ 7 cột; rerun cùng thư mục ghi đè không append (row count không tăng theo số lần chạy).
**💡 Vì sao cần:** Không làm → không có cách nào chuẩn hóa 1 dòng "báo cáo" cho mỗi nguồn (tải được bao nhiêu dòng, mất bao lâu, thành công hay lỗi) — mỗi nơi tự ghi log kiểu riêng. Có nó → có đúng 1 định dạng chuẩn, ghi ra file để sau này tra cứu/lọc bằng Polars hay Power BI đều được.

#### SUBTASK — Collect rows_loaded/status/duration_sec trong unit_of_work/base.py  _[SỬA]_

**Labels:** backend, phase-1, sprint-1 | **Priority:** Medium

**Goal:** Đo `duration_sec` + `rows_loaded` ngay trong `process_source()` (P1.2) — không đo lại ở nơi khác.
**Input Spec:** `process_source()` đã có sẵn khung đo `time.monotonic()` (xem P1.2).
**Output/Deliverable:** `process_source()` trả kèm `record` (dict) bên cạnh DataFrame — build qua `ingest_log.build_ingest_log_record()`.
**Tech Stack:** `time.monotonic()`, `df.height`.
**File(s):** src/extract/unit_of_work/base.py
**Technical Steps:**
1. Đo `duration_sec` bọc quanh đọc + `attach_lineage` + `cast_to_string`
2. `rows_loaded = df.height` (sau cast, số dòng không đổi qua các bước trên)
3. Gọi `ingest_log.build_ingest_log_record(..., status="success")`
**Acceptance Criteria:** Mỗi nguồn có 1 record đúng schema; `status=failed` + `rows_loaded=0` khi lỗi (dựng ở `orchestrator.py`, không phải ở `base.py` — lỗi đọc không bắt trong `process_source()`, xem P1.4).
**💡 Vì sao cần:** Không làm → không biết mỗi nguồn tải được bao nhiêu dòng, chạy mất bao lâu — không phát hiện được bất thường (VD nguồn tự nhiên tải được 0 dòng, hoặc chạy chậm bất thường). Có nó → có số liệu cụ thể cho từng nguồn mỗi lần chạy, dễ so sánh giữa các lần để phát hiện bất thường.

#### SUBTASK — Wire write_ingest_log() vào orchestrator.py  _[MỚI]_

**Labels:** backend, phase-1, sprint-1 | **Priority:** Medium

**Goal:** Sau khi loop xong 10 nguồn (thành công hoặc lỗi), ghi toàn bộ record thu được thành `ingest_log.parquet` CÙNG thư mục Bronze của run đó.
**Input Spec:** `records: list[dict]` thu thập trong `run_bronze_ingestion()` (P1.4).
**Output/Deliverable:** `orchestrator.run_bronze_ingestion()` gọi `ingest_log.write_ingest_log(records, out_dir)` ngay trước khi return.
**Tech Stack:** Python.
**File(s):** src/extract/orchestrator.py
**Technical Steps:**
1. Sau vòng loop 10 nguồn (dù có nguồn lỗi hay không), gọi `write_ingest_log(records, out_dir)`
2. Return `records` để caller (main.py/test) kiểm tra được summary
**Acceptance Criteria:** `data/bronze/<run_date>/ingest_log.parquet` tồn tại sau MỖI lần chạy `run_bronze_ingestion()`, kể cả khi có nguồn lỗi.
**💡 Vì sao cần:** Không làm → có hàm ghi log (`write_ingest_log`) nhưng không ai gọi nó thì log không bao giờ được ghi ra file thật. Có nó → cắm đúng vào cuối quy trình, chạy lần nào cũng tự động có file log, kể cả lần chạy bị lỗi giữa chừng.

---

# EPIC 2 — Phase 2: Silver Data Lake Cleansing  _[giữ nguyên]_

## EPIC — Phase 2: Silver Data Lake Cleansing

**Labels:** backend, phase-2, sprint-2 | **Priority:** Medium

# 🚀 EPIC: Phase 2 - Silver Data Lake Cleansing

### 🎯 Objective & End-to-End Scope

* **Data Flow Scope:** `data/bronze/<run_date>/` (String, thô) ➔ cast kiểu dữ liệu + chuẩn hóa text + khử trùng lặp + xử lý NULL ➔ `data/silver/<run_date>/` (typed, sạch, vẫn giữ lineage).
* **Epic AC:**

    * \[ \] `data/silver/<run_date>/` chứa đủ 10 file `.parquet`
    * \[ \] Cột `amount`/số tiền là Float, không còn dấu phẩy ngăn cách hàng nghìn
    * \[ \] Cột ngày parse đúng theo format khai báo riêng từng nguồn (xem P2.1) — không có cột ngày nào NULL hàng loạt do lệch format giữa nguồn CSV/Excel
    * \[ \] `customer_master` không còn dòng nào NULL ở `tax_code`
    * \[ \] 5 cột metadata lineage giữ nguyên từ Bronze
    * \[ \] Idempotent theo `run_date`
    * \[ \] Schema drift từ nguồn bị chặn TỪ BRONZE (P1.2), không lộ tới Silver; validate ở Silver (P2.1) chỉ còn là lớp phòng vệ thứ 2 bắt lỗi nội bộ, không phải điểm phát hiện chính
    
* **Epic DOD:** `pl.read_parquet('data/silver/<date>/SRC01_sales_transactions.parquet')` có cột `amount`/`net_amount` kiểu Float64; không còn duplicate 100% dòng; `uv run pytest tests/test_transform_silver.py` pass 100% (test cast kiểu, dedup, NULL handling — không chỉ check thủ công).

---

### 🔗 Dependencies, RACI & Timeline

* **Blocked By:** Epic 1 (Bronze Ingestion)
* **Blocks:** Epic 3 (Gold Star Schema)
* **Target Phase / Sprint:** Phase 2 / Sprint 2
* **Start Date / Due Date:** 2026-08-15 / 2026-08-17
* **Product Owner (sign-off):** Linh Nguyen
* **Required Reviewer(s):** Linh Nguyen (self-review, solo capstone)
* **On-call khi go-live:** Linh Nguyen
* **Confluence spec/decision log:** _(tạo page "Epic 2 — Silver Cleansing Spec & Decision Log" trên Confluence space mới, điền link vào đây sau khi tạo)_

---

### ⚠️ Risk Register

N/A — \[NON-PROD\]: xử lý dữ liệu local (không chạm credential/API ngoài), rủi ro ở đây là data-quality logic, không phải production infra. Xem AC/Scenario lỗi ở từng Story để kiểm soát rủi ro chất lượng dữ liệu.

---

### 🔒 Non-Functional Requirements

N/A (Production Impact: Không)

---

### 📝 Assumptions Made

* \[2026-07-26\] **Spec conflict phát hiện:** phase2_silver_cleansing.md mô tả "employee_master bị thiếu tax_code", nhưng Acceptance Criteria cùng file lại ghi "customer_master không còn tax_code NULL". Kiểm tra Data Dictionary (BRD §2.2): `employee_master` KHÔNG có cột `tax_code`; chỉ `customer_master` và `distributor_master` có `tax_code`. → Chọn `customer_master` làm target chính thức (theo AC, nguồn xác thực nghiệm thu) — Người duyệt: PO
* \[2026-07-26\] NULL `tax_code` ở `customer_master` được xử lý bằng cách fill placeholder `"UNKNOWN"` thay vì xóa dòng khách hàng — Người duyệt: PO
* \[2026-07-26\] Sprint 2 neo ngày theo README (Phase 2 bắt đầu cuối Tuần 3 = 2026-08-15, deadline đầu Tuần 4 = 2026-08-17), tính từ mốc Tuần 1 = 2026-07-26 — Người duyệt: PO

---

### STORY — P2.1 Type Casting — Numeric & Date (US-03)

**Labels:** backend, phase-2, sprint-2 | **Priority:** High

# 📋 USER STORY: Type Casting — Numeric & Date

### 👤 User Story

* **As a:** Data Analyst
* **I want to:** cột `amount`, `date` ở Silver đã đúng kiểu số/ngày
* **So that:** tính tổng doanh thu mà không cần convert tay

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** `data/bronze/<run_date>/*.parquet` (toàn bộ cột String — nhưng String hoá KHÔNG đồng nhất giữa 2 đường: 4 nguồn CSV giữ nguyên text gốc từ file; 6 nguồn Excel bị Polars tự suy luận kiểu rồi mới `.cast(pl.String)` ở Bronze, nên cùng là "cột ngày dạng String" nhưng khác format giữa 2 nhóm nguồn)
* **⚙️ Processing:** Validate đủ cột bắt buộc trước khi cast (fail sớm nếu thiếu) → `.str.replace_all(",", "")` xóa dấu phẩy ngăn cách hàng nghìn → `.cast(pl.Float64)` cho cột tiền/số lượng → `.str.strptime(pl.Date, fmt, strict=False)` cho cột ngày, `fmt` tra theo bảng mapping cột→format riêng từng nguồn (không dùng 1 format cứng chung cho cả 10 nguồn)
* **📤 Output:** DataFrame với cột tiền/số lượng kiểu Float64/Int64, cột ngày kiểu Date/Datetime; log rõ tên cột/nguồn nếu tỷ lệ parse NULL bất thường (nghi format sai) thay vì âm thầm trôi tiếp

---

### ✅ Definition of Ready

- [x] Spec rõ (phase2_silver_cleansing.md mục 2, Hint về dấu phẩy + Hint về múi giờ)
- [x] Đã xác nhận format ngày thật của từng nguồn qua sample file (không đoán) — xem Assumption bên dưới nếu chưa xác nhận được
- [x] Không cần Design
- [x] Blocked By Epic 1 (P1.4 Bronze parquet có sẵn)
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** Epic 1 (P1.4) / P2.2
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 2 / 2026-08-16

---

### 🏷️ Metadata

* **Labels:** sprint-2, phase-2, backend
* **Priority:** High
* **Story Points:** 3

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given Bronze cột `net_amount` dạng String "1,000,000", When cast, Then giá trị Silver = 1000000.0 (Float64)
* \[ \] **Scenario 2 (Error/Exception):** Given 1 dòng lẻ có giá trị ngày dị dạng (data rác thật), When `strptime` với đúng format của nguồn đó vẫn thất bại, Then dòng đó set NULL ở cột ngày thay vì crash toàn bộ pipeline
* \[ \] **Scenario 3 (Error/Exception — schema drift):** Given Bronze thiếu 1 cột bắt buộc theo Data Dictionary (nguồn đổi tên/xóa cột), When chạy Silver transform, Then pipeline dừng ngay với lỗi nêu rõ tên cột + tên nguồn thiếu, không tự map nhầm cột khác hoặc tạo cột NULL âm thầm
* \[ \] **Scenario 4 (Error/Exception — format sai cả cột):** Given format ngày khai báo cho 1 nguồn bị sai (áp nhầm format của nguồn khác), When parse cả cột, Then tỷ lệ NULL sinh ra bất thường (VD >50% dòng) phải được log cảnh báo rõ ràng — không coi là "chạy xong không lỗi" nếu gần như cả cột NULL

---

### 🔒 Non-Functional Requirements

N/A (Production Impact: Không)

---

### 📊 Observability Requirements

Log số dòng NULL phát sinh sau mỗi bước cast (theo cột) qua `src/logger.py` — phân biệt NULL do data rác thật (dự kiến, tỷ lệ thấp) với NULL do lệch format/schema drift (bất thường, tỷ lệ cao).

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

Chuẩn hóa text, dedup (P2.2), NULL business key (P2.3)

### 📝 Assumptions Made

* Format ngày thật của từng cột (VD `order_date` ở SRC01 CSV có thể là `DD/MM/YYYY` theo quy ước VN, trong khi cột ngày ở nguồn Excel bị Bronze cast từ kiểu Date gốc sang String ISO `YYYY-MM-DD`) **chưa được xác nhận bằng cách mở sample file thật** — subtask "Validate + mapping format ngày theo từng nguồn" bên dưới phải mở file mẫu xác nhận trước khi hardcode format, không đoán theo 1 format duy nhất như bản cũ.
* Cột `_ingested_at` là UTC (`datetime.now(UTC)` ở Bronze); các cột ngày nghiệp vụ (`order_date`, `effective_date`...) giả định là ngày dương lịch không có thông tin múi giờ (naive date, không phải datetime có tz) — nếu nguồn thật có giờ kèm múi giờ khác UTC, cần bổ sung xử lý riêng (ngoài phạm vi capstone hiện tại, ghi nhận làm known limitation).

### 🛠️ Technical Notes

Cột cần cast: `unit_price, gross_amount, net_amount, discount_amount, quantity, target_revenue, ...` (theo Data Dictionary từng nguồn); cột ngày: `order_date, return_date, effective_date, join_date, launch_date, start_date, end_date...`

#### SUBTASK — Validate required columns (lớp phòng vệ thứ 2) + mapping format ngày theo từng nguồn  _[SỬA — schema-drift gate CHÍNH đã dời sang Bronze P1.2]_

**Labels:** backend, phase-2, sprint-2 | **Priority:** High

**Goal:** Lớp phòng vệ thứ 2 (defense-in-depth) — gate CHÍNH chặn schema drift giờ nằm ở Bronze (`parser.validate_schema()`, P1.2), nên về lý thuyết Silver không còn nhận được file thiếu cột từ nguồn nữa. Subtask này giữ lại để bắt lỗi nội bộ (VD sửa code Bronze làm rớt cột lineage, bug trong `cast_to_string()`...), và để xác định ĐÚNG format ngày cho từng nguồn thay vì giả định 1 format chung.
**Input Spec:** `data/bronze/<run_date>/*.parquet`, Data Dictionary (BRD §2.2), sample file thật của từng nguồn (mở tay để xác nhận format ngày viết theo kiểu gì — không đoán).
**Output/Deliverable:** `DATE_FORMAT_BY_SOURCE: dict[str, dict[str, str]]` (nguồn → {tên cột ngày: format string}) trong `config/sources.py`; hàm `validate_required_columns(df, source_name)` raise lỗi rõ tên cột+nguồn nếu thiếu cột bắt buộc (tái dùng `REQUIRED_COLUMNS`/`SchemaMismatchError` đã khai báo ở P1.2, không định nghĩa 1 cấu trúc dict thứ 2 song song).
**Tech Stack:** Polars, Python dict config.
**File(s):** `config/sources.py`, `src/transform_silver.py`
**Technical Steps:**
1. Mở sample file thật từng nguồn (không phải đoán) xác nhận cột ngày viết theo format gì (VD CSV có thể `DD/MM/YYYY`, cột ngày từ Excel sau khi Bronze cast String thường ra ISO `YYYY-MM-DD` hoặc `YYYY-MM-DD HH:MM:SS`)
2. Khai báo `DATE_FORMAT_BY_SOURCE` trong `config/sources.py`, 1 format riêng cho từng cột ngày của từng nguồn
3. `validate_required_columns(df, source_name)`: import + tái dùng `REQUIRED_COLUMNS` (P1.2) — so `df.columns` với danh sách đó, raise `SchemaMismatchError` (cùng exception class Bronze, không tạo `ValueError` riêng) liệt kê cột thiếu + tên nguồn nếu lệch
4. Gọi `validate_required_columns()` NGAY ĐẦU transform mỗi nguồn, trước bất kỳ bước cast nào — nếu bắt được lỗi ở đây tức là có bug ở tầng Bronze lọt qua, log mức WARNING nhấn mạnh "lẽ ra phải bị chặn từ Bronze"
**Acceptance Criteria:** Xóa/đổi tên 1 cột bắt buộc trong file Bronze test → pipeline dừng với lỗi nêu rõ tên cột + tên nguồn, không cast tiếp; `DATE_FORMAT_BY_SOURCE` có entry cho toàn bộ cột ngày liệt kê ở Technical Notes.
**💡 Vì sao cần:** Không làm → nếu Bronze lỡ có bug làm rớt mất cột, hoặc format ngày đoán sai (VD nhầm ngày Việt Nam DD/MM/YYYY với ngày Mỹ MM/DD/YYYY), toàn bộ cột ngày parse ra sai/NULL hàng loạt mà không ai phát hiện — báo cáo doanh thu theo tháng sẽ sai âm thầm. Có nó → xác nhận đúng format thật (không đoán) cho từng nguồn, và có lớp chặn dự phòng nếu Bronze lỡ có bug lọt qua.

#### SUBTASK — Strip thousand-separator + cast money/qty cols to Float64/Int64

**Labels:** backend, phase-2, sprint-2 | **Priority:** Medium

**Goal:** Chuyển cột tiền/số lượng từ String sang số, xử lý dấu phẩy ngăn cách hàng nghìn.
**Input Spec:** Bronze DataFrame, cột String như `net_amount`, `unit_price`, `quantity`.
**Output/Deliverable:** Cột số kiểu Float64/Int64.
**Tech Stack:** Polars.
**File(s):** `src/transform_silver.py`
**Technical Steps:** `pl.col(col).str.replace_all(",", "").cast(pl.Float64)` cho từng cột tiền/số lượng ở tất cả 10 nguồn liên quan.
**Acceptance Criteria:** `df.schema["net_amount"] == pl.Float64`.
**💡 Vì sao cần:** Không làm → cột tiền còn ở dạng chữ (String "1,000,000") thì không cộng/tính tổng doanh thu được, mà cast thẳng sang số cũng lỗi vì dấu phẩy không phải ký tự số. Có nó → cột tiền/số lượng thành số thật, Data Analyst tính tổng/trung bình bình thường không cần convert tay.

#### SUBTASK — Cast date columns to pl.Date/Datetime theo format riêng từng nguồn  _[SỬA]_

**Labels:** backend, phase-2, sprint-2 | **Priority:** Medium

**Goal:** Chuyển cột ngày từ String sang Date/Datetime chuẩn Polars, dùng ĐÚNG format của từng nguồn (không hardcode 1 format chung).
**Input Spec:** Bronze DataFrame, cột String như `order_date`, `join_date`, `effective_date`; `DATE_FORMAT_BY_SOURCE` (subtask trước).
**Output/Deliverable:** Cột ngày kiểu `pl.Date`/`pl.Datetime`; log tỷ lệ NULL sinh ra sau parse (theo cột).
**Tech Stack:** Polars.
**File(s):** `src/transform_silver.py`
**Technical Steps:**
1. Tra `fmt = DATE_FORMAT_BY_SOURCE[source_name][col]` cho từng cột ngày — KHÔNG dùng 1 `"%Y-%m-%d"` cứng cho toàn bộ 10 nguồn
2. `pl.col(col).str.strptime(pl.Date, fmt, strict=False)`
3. Log `df[col].is_null().sum() / df.height` sau parse — cảnh báo nếu tỷ lệ NULL bất thường (nghi format sai, không phải data rác thật)
**Acceptance Criteria:** `df.schema["order_date"] == pl.Date` cho cả nguồn CSV lẫn Excel; đổi format sai cho 1 nguồn trong test → tỷ lệ NULL log ra rõ ràng cao bất thường, không âm thầm trôi qua.
**💡 Vì sao cần:** Không làm → dùng chung 1 format ngày cho cả 10 nguồn, trong khi nguồn CSV và Excel viết ngày khác kiểu nhau — nguồn nào lệch format sẽ bị parse sai thành NULL hàng loạt mà không báo lỗi gì (Polars âm thầm trả NULL). Có nó → mỗi nguồn dùng đúng format của nó, và có cảnh báo nếu tỷ lệ NULL bất thường để phát hiện sớm nếu format sai.

#### SUBTASK — pytest test_transform_silver.py: verify dtype + format ngày đúng  _[SỬA]_

**Labels:** backend, phase-2, sprint-2 | **Priority:** Medium

**Goal:** Test tự động thay cho check thủ công — khớp yêu cầu Epic 2 DOD (`tests/test_transform_silver.py`).
**Input Spec:** DataFrame đã cast (2 subtask trước), fixture nhỏ giả lập cả nguồn CSV-style và Excel-style date string.
**Output/Deliverable:** `tests/test_transform_silver.py` — test cast tiền/số lượng, test cast ngày cho ít nhất 1 nguồn CSV + 1 nguồn Excel (2 format khác nhau).
**Tech Stack:** pytest, Polars.
**File(s):** `tests/test_transform_silver.py`
**Technical Steps:** Tạo fixture DataFrame nhỏ mô phỏng cả 2 kiểu format ngày, gọi hàm cast, assert dtype + giá trị đúng, assert `validate_required_columns()` raise đúng khi thiếu cột.
**Acceptance Criteria:** `uv run pytest tests/test_transform_silver.py` pass 100%; toàn bộ cột tiền/số lượng là Float64/Int64, toàn bộ cột ngày là Date/Datetime, không còn String ở các cột này.
**💡 Vì sao cần:** Không làm → chỉ "check thủ công" bằng mắt 1 lần lúc code xong, ai đó sửa code sau này (kể cả chính mình) làm hỏng logic cast mà không ai biết cho tới khi ra báo cáo sai số. Có nó → test tự động chạy lại mỗi lần sửa code, phát hiện ngay nếu có gì hỏng thay vì đợi phát hiện ở báo cáo cuối.

---

### STORY — P2.2 Text Standardization & Deduplication

**Labels:** backend, phase-2, sprint-2 | **Priority:** High

# 📋 USER STORY: Text Standardization & Deduplication

### 👤 User Story

* **As a:** Data Analyst
* **I want to:** dữ liệu text chuẩn hóa (không khoảng trắng thừa, viết hoa nhất quán), không còn dòng trùng lặp 100%
* **So that:** join/group_by ở Gold không bị sai lệch vì lệch format hoặc double-count vì trùng

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** DataFrame đã cast kiểu (từ P2.1)
* **⚙️ Processing:** `.str.strip_chars()` + `.str.to_uppercase()` cho cột text; `.unique()` loại dòng trùng lặp 100% (đặc biệt `customer_master`, theo BRD: bị trùng do nhân viên up lại file cũ)
* **📤 Output:** DataFrame text chuẩn hóa, không còn duplicate 100%

---

### ✅ Definition of Ready

- [x] Spec rõ (phase2_silver_cleansing.md mục 2-3)
- [x] Không cần Design
- [x] Blocked By P2.1
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** P2.1 / P2.3
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 2 / 2026-08-16

---

### 🏷️ Metadata

* **Labels:** sprint-2, phase-2, backend
* **Priority:** High
* **Story Points:** 3

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given `customer_master` có 2 dòng giống hệt nhau (do up lại file cũ), When dedup, Then chỉ còn 1 dòng
* \[ \] **Scenario 2 (Error/Exception):** Given cột `region` có giá trị `" Miền Bắc "` và `"MIỀN BẮC"`, When chuẩn hóa, Then cả 2 quy về cùng 1 giá trị chuẩn (strip + uppercase)

---

### 🔒 Non-Functional Requirements

N/A

---

### 📊 Observability Requirements

N/A

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

NULL business key handling (P2.3)

### 🛠️ Technical Notes

`df.unique()` áp dụng full-row; cẩn thận không dedup nhầm dòng khác batch nhưng trùng giá trị nghiệp vụ (dùng full-row unique, không chỉ theo business key).

#### SUBTASK — Strip+uppercase standardize text columns

**Labels:** backend, phase-2, sprint-2 | **Priority:** Medium

**Goal:** Chuẩn hóa text tránh lệch format khi group_by/join ở Gold.
**Input Spec:** DataFrame đã cast kiểu (P2.1), cột text như `region`, `province`, `channel`, `status`.
**Output/Deliverable:** Cột text đã strip + uppercase.
**Tech Stack:** Polars.
**File(s):** `src/transform_silver.py`
**Technical Steps:** `pl.col(col).str.strip_chars().str.to_uppercase()` cho các cột text nghiệp vụ (không áp dụng cho cột ID/tên riêng nếu cần giữ nguyên case).
**Acceptance Criteria:** Không còn khoảng trắng đầu/cuối; giá trị text đồng nhất chữ hoa.
**💡 Vì sao cần:** Không làm → 2 dòng cùng ý nghĩa (`" Miền Bắc "` và `"MIỀN BẮC"`) bị coi là 2 giá trị khác nhau khi group_by/join ở Gold — báo cáo tính sai vì bị tách lẻ thay vì gộp lại. Có nó → mọi biến thể viết hoa/thường, khoảng trắng thừa đều quy về 1 dạng chuẩn, group_by/join ra đúng số.

#### SUBTASK — Drop duplicate rows in customer_master + other sources

**Labels:** backend, phase-2, sprint-2 | **Priority:** Medium

**Goal:** Loại dòng trùng lặp 100% do up nhầm file cũ.
**Input Spec:** DataFrame đã chuẩn hóa text (subtask trước).
**Output/Deliverable:** DataFrame không còn duplicate full-row.
**Tech Stack:** Polars.
**File(s):** `src/transform_silver.py`
**Technical Steps:** `df.unique()` áp dụng cho toàn bộ 10 nguồn, ưu tiên kiểm tra kỹ `customer_master` (theo BRD báo có trùng lặp thật).
**Acceptance Criteria:** `df.shape[0] == df.unique().shape[0]` sau bước này (không còn giảm thêm khi unique lại).
**💡 Vì sao cần:** Không làm → nhân viên lỡ tay up lại file cũ, khách hàng bị đếm/tính doanh thu 2 lần trong báo cáo (BRD xác nhận đây là vấn đề thật đang gặp). Có nó → dòng trùng lặp 100% chỉ còn giữ lại 1 bản, số liệu không bị thổi phồng.

#### SUBTASK — Drop/handle rows with NULL customer_id/product_id keys

**Labels:** backend, phase-2, sprint-2 | **Priority:** Medium

**Goal:** Loại bỏ dòng thiếu khóa chính (customer_id, product_id) — không thể join ở Gold nếu thiếu.
**Input Spec:** DataFrame đã dedup (subtask trước).
**Output/Deliverable:** DataFrame không còn dòng NULL ở business key.
**Tech Stack:** Polars.
**File(s):** `src/transform_silver.py`
**Technical Steps:** `df.filter(pl.col("customer_id").is_not_null())` (tương tự cho `product_id`, `employee_id` tùy nguồn); log số dòng bị loại vào console.
**Acceptance Criteria:** Không còn dòng NULL ở cột khóa chính của từng nguồn liên quan (`sales_transactions`, `return_transactions`...).
**💡 Vì sao cần:** Không làm → dòng giao dịch thiếu mã khách hàng/sản phẩm thì tới Gold không join được vào Dim nào cả, hoặc join sai lung tung. Có nó → loại bỏ sớm những dòng chắc chắn không dùng được, tránh để lỗi trôi xuống bước join phức tạp hơn ở Gold mới phát hiện.

---

### STORY — P2.3 NULL Handling — customer_master.tax_code

**Labels:** backend, phase-2, pii, sprint-2 | **Priority:** Medium

# 📋 USER STORY: NULL Handling — customer_master.tax_code

### 👤 User Story

* **As a:** Data Analyst
* **I want to:** cột `tax_code` trong `customer_master` không còn NULL
* **So that:** báo cáo/join không bị lỗi thiếu dữ liệu ở trường bắt buộc

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** `customer_master` (Silver, sau P2.2)
* **⚙️ Processing:** `.fill_null("UNKNOWN")` trên cột `tax_code`
* **📤 Output:** `customer_master` không còn NULL ở `tax_code`

---

### ✅ Definition of Ready

* \[x\] Spec rõ SAU KHI resolve spec conflict (xem mục 📝 Assumptions Made ở đầu Epic 2 phía trên): target xác nhận là `customer_master`, không phải `employee_master`
* \[x\] Không cần Design
* \[x\] Blocked By P2.2
* \[x\] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** P2.2 / P2.4
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 2 / 2026-08-17

---

### 🏷️ Metadata

* **Labels:** sprint-2, phase-2, backend, pii
* **Priority:** Medium
* **Story Points:** 1

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given `customer_master` có N dòng NULL `tax_code`, When fill_null, Then 0 dòng NULL, N dòng có giá trị `"UNKNOWN"`
* \[ \] **Scenario 2 (Error/Exception):** Given toàn bộ cột `tax_code` đã có giá trị (không NULL), When chạy fill_null, Then không có gì thay đổi (idempotent về mặt logic)

---

### 🔒 Non-Functional Requirements

N/A

---

### 📊 Observability Requirements

N/A

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

Xử lý NULL ở các cột/bảng khác (không nằm trong AC gốc của phase2_silver_cleansing.md)

### 🛠️ Technical Notes

`df.with_columns(pl.col("tax_code").fill_null("UNKNOWN"))`

#### SUBTASK — fill_null("UNKNOWN") on customer_master.tax_code

**Labels:** backend, phase-2, pii, sprint-2 | **Priority:** Medium

**Goal:** Không còn NULL ở `tax_code` trong `customer_master`.
**Input Spec:** `customer_master` DataFrame sau P2.2 (đã dedup, chuẩn hóa text).
**Output/Deliverable:** Cột `tax_code` không còn NULL.
**Tech Stack:** Polars.
**File(s):** `src/transform_silver.py`
**Technical Steps:** `df.with_columns(pl.col("tax_code").fill_null("UNKNOWN"))`.
**Acceptance Criteria:** `df.filter(pl.col("tax_code").is_null()).shape[0] == 0`.
**💡 Vì sao cần:** Không làm → báo cáo/dashboard lọc theo `tax_code` bị thiếu dữ liệu ở những dòng NULL, hoặc join/group_by hiểu nhầm NULL là "không có nhóm" thay vì 1 nhóm rõ ràng. Có nó → mọi khách hàng đều có giá trị `tax_code` xác định (kể cả khi thật sự không có thông tin, đánh dấu rõ "UNKNOWN"), không có ô trống gây lỗi khi xử lý tiếp.

---

### STORY — P2.4 Write Silver Parquet, Idempotent

**Labels:** db, migration, phase-2, sprint-2 | **Priority:** High

# 📋 USER STORY: Write Silver Parquet, Idempotent

### 👤 User Story

* **As a:** Admin
* **I want to:** ghi dữ liệu đã làm sạch ra `data/silver/<run_date>/`
* **So that:** Gold layer (Epic 3) có nguồn dữ liệu sạch, đáng tin cậy để build Star Schema

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** 10 DataFrame đã cast + chuẩn hóa + xử lý NULL (P2.1-P2.3)
* **⚙️ Processing:** `df.write_parquet()` vào `data/silver/<run_date>/`
* **📤 Output:** `data/silver/<run_date>/` chứa đủ 10 file `.parquet`

---

### ✅ Definition of Ready

- [x] Spec rõ (phase2_silver_cleansing.md mục 4)
- [x] Không cần Design
- [x] Blocked By P2.3
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** P2.3 / Epic 3 (P3.1)
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 2 / 2026-08-17

---

### 🏷️ Metadata

* **Labels:** sprint-2, phase-2, db, migration
* **Priority:** High
* **Story Points:** 2

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given 10 DataFrame sạch, When ghi Parquet, Then `data/silver/<run_date>/` có đủ 10 file, giữ nguyên 5 cột metadata lineage
* \[ \] **Scenario 2 (Error/Exception):** Given chạy lại cùng `run_date`, When so sánh row count trước/sau, Then không đổi (idempotent)

---

### 🔒 Non-Functional Requirements

N/A

---

### 📊 Observability Requirements

N/A

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

Dimensional modeling (Epic 3)

### 🛠️ Technical Notes

`data/silver/20260722/customer_master.parquet` — giữ tên file theo mã nguồn.

#### SUBTASK — write_parquet mỗi source vào data/silver/<run_date>/

**Labels:** db, migration, phase-2, sprint-2 | **Priority:** Medium

**Goal:** Ghi toàn bộ 10 DataFrame sạch ra Silver Parquet.
**Input Spec:** 10 DataFrame đã qua P2.1-P2.3.
**Output/Deliverable:** `data/silver/<run_date>/*.parquet` (10 file).
**Tech Stack:** Polars.
**File(s):** `src/transform_silver.py`
**Technical Steps:** `os.makedirs(f"data/silver/{run_date}", exist_ok=True)` → `df.write_parquet(...)` cho từng nguồn.
**Acceptance Criteria:** `data/silver/<run_date>/` có đủ 10 file `.parquet`.
**💡 Vì sao cần:** Không làm → dữ liệu đã làm sạch chỉ nằm trong bộ nhớ tạm, tắt chương trình là mất, Epic 3 (Gold) không có gì để đọc vào. Có nó → dữ liệu sạch được lưu lại thành file, Gold layer (và bất kỳ ai khác) đọc lại được bất cứ lúc nào không cần chạy lại từ đầu.

#### SUBTASK — Idempotency check: rerun same run_date, no duplication/append

**Labels:** db, migration, phase-2, sprint-2 | **Priority:** Medium

**Goal:** Verify Silver layer cũng idempotent như Bronze.
**Input Spec:** Silver pipeline đã chạy 1 lần thành công.
**Output/Deliverable:** Bằng chứng rerun 2 lần liên tiếp cùng `run_date`, row count không đổi.
**Tech Stack:** Polars, shell.
**File(s):** `data/silver/<run_date>/`
**Technical Steps:** Chạy `--layer silver --run-date X` 2 lần liên tiếp → so sánh row count trước/sau.
**Acceptance Criteria:** Row count 10 file không đổi giữa 2 lần chạy.
**💡 Vì sao cần:** Không làm → không chắc chắn Silver có bị lỗi nhân đôi dữ liệu khi chạy lại hay không (VD do quên ghi đè, chỉ append thêm) — nếu có bug thì báo cáo Gold sau này sẽ sai gấp đôi mà không biết vì sao. Có nó → có bằng chứng cụ thể xác nhận chạy lại bao nhiêu lần cũng ra đúng 1 kết quả.

---

# EPIC 3 — Phase 3: Gold Star Schema & Production Hardening  _[giữ nguyên]_

## EPIC — Phase 3: Gold Star Schema & Production Hardening

**Labels:** backend, db, phase-3, sprint-3 | **Priority:** Medium

# 🚀 EPIC: Phase 3 - Gold Star Schema & Production Hardening

### 🎯 Objective & End-to-End Scope

* **Data Flow Scope:** `data/silver/<run_date>/` ➔ Dimensional Modeling (dim\__, fact\__, SCD Type 2, mart_sales_vs_target) + Lazy Evaluation + Pytest + CLI orchestration ➔ `data/gold/<run_date>/` (Star Schema hoàn chỉnh, sẵn sàng cho DuckDB/Power BI).
* **Epic AC:**

    * \[ \] Đủ Dimension (`dim_customers`, `dim_products`, `dim_distributors`, `dim_date`, `dim_territory`, `dim_promotion`, `dim_employees` SCD2) + Fact (`fact_sales`, `fact_targets`, `fact_returns`, `fact_distributor_orders`) + `mart_sales_vs_target`
    * \[ \] `dim_employees` SCD2 trả đúng `region` hiệu lực tại `order_date` (US-06)
    * \[ \] Không FK nào NULL trên bất kỳ Fact table nào — chỉ key thật hoặc `-1` (Unknown Member)
    * \[ \] Cột PII (`phone/address/tax_code/date_of_birth`) không xuất hiện trong bất kỳ file nào ở `data/gold/<run_date>/`
    * \[ \] `uv run pytest test_pipeline.py` pass 100% (≥2 test: Data Mart logic, SCD2 logic)
    * \[ \] `uv run main.py --layer all --run-date <date>` chạy full pipeline Google Drive → Gold trong 1 lệnh
    
* **Epic DOD:** Toàn bộ bảng Gold đọc được bằng `pl.read_parquet`/DuckDB, số liệu `mart_sales_vs_target` khớp tính tay trên dữ liệu mẫu nhỏ.

---

### 🔗 Dependencies, RACI & Timeline

* **Blocked By:** Epic 2 (Silver Cleansing)
* **Blocks:** Epic 4 (Dashboard)
* **Target Phase / Sprint:** Phase 3 / Sprint 3
* **Start Date / Due Date:** 2026-08-22 / 2026-08-24
* **Product Owner (sign-off):** Linh Nguyen
* **Required Reviewer(s):** Linh Nguyen (self-review, solo capstone)
* **On-call khi go-live:** Linh Nguyen
* **Confluence spec/decision log:** _(tạo page "Epic 3 — Gold Star Schema Spec & Decision Log" trên Confluence space mới, điền link vào đây sau khi tạo)_

---

### ⚠️ Risk Register

N/A — \[NON-PROD\]: xử lý dữ liệu local (join/aggregate/test), không chạm credential/API ngoài. Rủi ro chính là đúng logic nghiệp vụ (SCD2, join key), kiểm soát qua AC + pytest ở từng Story, không phải rủi ro hạ tầng production.

---

### 🔒 Non-Functional Requirements

N/A (Production Impact: Không)

---

### 📝 Assumptions Made

* \[2026-07-26\] Sprint 3 neo ngày theo README (Phase 3 bắt đầu cuối Tuần 4 = 2026-08-22, deadline "Bế giảng"). Ngày Bế giảng chính xác chưa được cung cấp trong tài liệu → dùng 2026-08-24 làm due date tạm (buffer 2 ngày), CẦN PO xác nhận lại ngày Bế giảng thật khi biết — Người duyệt: PO (placeholder, cần xác nhận lại)
* \[2026-07-26\] Employee_key/surrogate keys cho các bảng Dim sinh bằng row index/hash đơn giản (không dùng sequence generator ngoài) vì đây là batch build lại toàn bộ Gold mỗi run, không phải incremental warehouse — Người duyệt: PO
* \[2026-08-02\] **Quyết định — KHÔNG partition bên trong `fact_sales`/`fact_returns` theo cột (VD `year`/`month`) ở phạm vi capstone này.** Lý do: mỗi `run_date` đã là 1 thư mục Parquet riêng (`data/gold/<run_date>/`), và data mẫu (FMCG 1 công ty, vài tháng) không đủ lớn để full-scan trở thành vấn đề thật — thêm sub-partition bây giờ là tối ưu hoá sớm không có số đo hiệu năng làm căn cứ. Ghi nhận đây là điểm cần làm khi data lớn dần thật (không phải bị bỏ sót/quên) — Người duyệt: PO

---

### STORY — P3.1 Dimension Tables (customers/products/distributors/date)

**Labels:** db, phase-3, sprint-3 | **Priority:** High

# 📋 USER STORY: Dimension Tables

### 👤 User Story

* **As a:** Data Analyst
* **I want to:** có sẵn `dim_customers`, `dim_products`, `dim_distributors`, `dim_date`
* **So that:** query Gold layer bằng SQL đơn giản, không cần JOIN phức tạp trên Silver

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** `data/silver/<run_date>/{customer_master,product_master,distributor_master}.parquet`, `fact_sales` date range
* **⚙️ Processing:** Select cột mô tả + sinh surrogate key (row index) cho từng Dim; `dim_date` sinh dải ngày calendar
* **📤 Output:** DataFrame `dim_customers`, `dim_products`, `dim_distributors`, `dim_date` sẵn sàng ghi Gold

---

### ✅ Definition of Ready

- [x] Spec rõ (phase3_gold_production.md Phần A #1, BRD §2.4)
- [x] Không cần Design
- [x] Blocked By Epic 2 (P2.4 Silver parquet có sẵn)
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** Epic 2 (P2.4) / P3.3
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 3 / 2026-08-23

---

### 🏷️ Metadata

* **Labels:** sprint-3, phase-3, db
* **Priority:** High
* **Story Points:** 5

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given Silver `customer_master`/`product_master`/`distributor_master`, When build Dim, Then mỗi Dim có surrogate key duy nhất, số dòng khớp entity gốc
* \[ \] **Scenario 2 (Error/Exception):** Given `product_master` có sản phẩm trùng `product_id` (data lỗi giả lập), When build `dim_products`, Then dedup theo `product_id` trước khi sinh surrogate key, không tạo 2 key cho cùng 1 sản phẩm
* \[ \] **Scenario 3 (Kiến trúc — bắt buộc quyết định trước khi code P3.3/P3.4):** Given 1 dòng Fact có business key (`customer_id`/`product_id`/...) không tồn tại trong Dim tương ứng (data trễ, Dim chưa build kịp, hoặc data rác), When join Fact→Dim, Then FK trỏ về dòng **"Unknown Member"** (surrogate key = `-1`) đã có sẵn trong Dim đó — KHÔNG để FK NULL. Lý do: NULL FK làm Power BI coi là 1 "blank" chung cho mọi lý do lỗi khác nhau (data trễ vs data rác vs dim chưa build đều gộp lẫn), trong khi `-1` là 1 key tường minh, filter/drill-down được, đúng chuẩn Kimball "Unknown Member"

---

### 🔒 Non-Functional Requirements

N/A

---

### 📊 Observability Requirements

N/A

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

`dim_employees` SCD2 (P3.2), `dim_territory`/`dim_promotion` (P3.4)

### 🛠️ Technical Notes

Surrogate key: `df.with_row_index("customer_key")` hoặc tương đương, cộng `+1` để dành `0` không dùng và bắt đầu key thật từ `1` — dòng "Unknown Member" luôn cố định `-1` (xem subtask riêng bên dưới), không lẫn với key thật.

#### SUBTASK — dim_customers + dim_products build w/ surrogate keys

**Labels:** db, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Build 2 bảng Dim chính từ Silver.
**Input Spec:** `data/silver/<run_date>/{customer_master,product_master}.parquet`.
**Output/Deliverable:** DataFrame `dim_customers`, `dim_products` với surrogate key.
**Tech Stack:** Polars.
**File(s):** `src/transform_gold.py`
**Technical Steps:** Select cột mô tả, dedup theo business key, `with_row_index()` sinh `customer_key`/`product_key` (bắt đầu từ `1`).
**Acceptance Criteria:** Mỗi Dim có key duy nhất, không trùng business key.
**💡 Vì sao cần:** Không làm → Data Analyst muốn xem doanh số theo khách hàng/sản phẩm phải tự viết JOIN phức tạp trên Silver mỗi lần truy vấn. Có nó → có sẵn bảng "danh mục" gọn gàng, join vào Fact chỉ cần 1 dòng SQL/DAX đơn giản.

#### SUBTASK — dim_distributors build w/ surrogate keys

**Labels:** db, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Build `dim_distributors` từ Silver.
**Input Spec:** `data/silver/<run_date>/distributor_master.parquet`.
**Output/Deliverable:** DataFrame `dim_distributors` với `distributor_key`.
**Tech Stack:** Polars.
**File(s):** `src/transform_gold.py`
**Technical Steps:** Select cột mô tả, dedup theo `distributor_id`, sinh surrogate key (bắt đầu từ `1`).
**Acceptance Criteria:** `dim_distributors` có key duy nhất, số dòng khớp số NPP thật.
**💡 Vì sao cần:** Không làm → không có bảng riêng cho nhà phân phối, phân tích hiệu suất NPP phải join thẳng vào Silver mỗi lần. Có nó → có bảng chiều NPP sẵn sàng, join vào `fact_distributor_orders` dễ dàng ở Gold.

#### SUBTASK — Thêm dòng "Unknown Member" (key = -1) vào mọi Dim  _[MỚI]_

**Labels:** db, phase-3, sprint-3 | **Priority:** High

**Goal:** Chốt kiến trúc xử lý FK không match (Scenario 3) — mọi Dim table trong Gold phải có sẵn 1 dòng "Unknown Member" trước khi P3.3/P3.4 join vào Fact, nếu không join sẽ không có gì để trỏ tới.
**Input Spec:** `dim_customers`, `dim_products`, `dim_distributors` (2 subtask trên), `dim_territory`, `dim_promotion` (P3.4).
**Output/Deliverable:** Mỗi Dim có thêm đúng 1 dòng: surrogate key = `-1`, business key (`customer_id`/`product_id`/...) = `"UNKNOWN"`, các cột mô tả khác = `"Unknown"`/NULL tùy loại.
**Tech Stack:** Polars `pl.concat()`.
**File(s):** `src/transform_gold.py`
**Technical Steps:**
1. Viết 1 helper `add_unknown_member(df, key_col, business_key_col)` dùng chung cho mọi Dim — tránh lặp code 5 lần
2. `pl.concat([unknown_row_df, df])` — Unknown Member luôn ở dòng đầu, key `-1` cố định
3. Áp dụng cho `dim_customers, dim_products, dim_distributors, dim_territory, dim_promotion` (P3.1/P3.4) — mọi Dim có business key tra từ nguồn ngoài đều cần
4. `dim_employees` (SCD2, P3.2) cũng thêm 1 dòng Unknown Member tĩnh: `employee_key=-1`, `employee_id="UNKNOWN"`, `valid_from=NULL`, `valid_to=NULL`, `is_current=False` — dùng làm fallback khi as-of join P3.3 Scenario 3 không match version nào (nhân viên nghỉ việc/không tồn tại), KHÔNG cố join theo range cho dòng này
5. `dim_date` KHÔNG cần Unknown Member — quyết định: mọi `order_date` sau khi qua Silver P2.1 (validate + parse đúng format) luôn là ngày hợp lệ, không có case "ngày không match dim_date"
**Acceptance Criteria:** `dim_customers.filter(pl.col("customer_key") == -1)` trả đúng 1 dòng "Unknown Member"; áp dụng đủ cho `dim_customers, dim_products, dim_distributors, dim_territory, dim_promotion, dim_employees`.
**💡 Vì sao cần:** Không làm → khi 1 đơn hàng có `customer_id` không tìm thấy trong `dim_customers` (data trễ, data rác), FK phải để trống (NULL) — Power BI gộp hết mọi lý do lỗi khác nhau vào chung 1 nhóm "blank", không phân biệt được data trễ hay data rác. Có nó → có 1 dòng "không xác định" rõ ràng với key cố định `-1`, filter/lọc riêng ra được, không lẫn với các trường hợp NULL khác trong hệ thống.

#### SUBTASK — dim_date generate calendar dimension

**Labels:** db, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Sinh bảng chiều ngày tháng phục vụ join theo `dim_date`.
**Input Spec:** Khoảng ngày min/max từ `sales_transactions.order_date` (Silver).
**Output/Deliverable:** DataFrame `dim_date` với `date_key, date, day, month, quarter, year`.
**Tech Stack:** Polars `date_range`.
**File(s):** `src/transform_gold.py`
**Technical Steps:** `pl.date_range(min_date, max_date, "1d")` → derive các cột day/month/quarter/year.
**Acceptance Criteria:** `dim_date` phủ đủ khoảng ngày xuất hiện trong `fact_sales`.
**💡 Vì sao cần:** Không làm → muốn lọc/group theo quý, tháng, thứ trong tuần phải tự tính lại mỗi lần từ cột ngày thô. Có nó → có sẵn bảng ngày tháng với đủ thông tin (ngày/tháng/quý/năm), Power BI chỉ cần kéo-thả là lọc/group theo thời gian được ngay.

#### SUBTASK — Drop cột PII khỏi Gold Dim tables (thay vì rà soát tay lúc share)  _[MỚI]_

**Labels:** db, pii, compliance-nd13, phase-3, sprint-3 | **Priority:** High

**Goal:** Kiểm soát PII bằng kiến trúc (không sinh ra dữ liệu nhạy cảm ở Gold) thay vì kiểm soát bằng quy trình tay (review `.pbix` trước khi share, P4.1). Rủi ro nếu chỉ rà soát ở P4.1: ai có quyền đọc file `data/gold/<run_date>/*.parquet` trực tiếp trên đĩa (không qua Power BI) vẫn thấy PII nguyên vẹn — review `.pbix` không bảo vệ được file Parquet gốc.
**Input Spec:** `dim_customers`, `dim_employees`, `dim_distributors` (đã build, các subtask trên + P3.2) — cột PII theo Data Dictionary: `phone, address, tax_code, date_of_birth`.
**Output/Deliverable:** 3 Dim trên KHÔNG còn cột PII thô khi ghi ra `data/gold/<run_date>/` — Silver (`data/silver/`) vẫn giữ nguyên PII cho nhu cầu nội bộ khác (nếu có), chỉ Gold (lớp phục vụ BI, dễ bị đọc/share ngoài) bị cắt.
**Tech Stack:** Polars `.drop()`.
**File(s):** `src/transform_gold.py`
**Technical Steps:**
1. Khai báo `PII_COLUMNS_TO_DROP: dict[str, list[str]]` trong `config/sources.py` (per-Dim danh sách cột PII cần drop trước khi ghi Gold)
2. Áp dụng `.drop(PII_COLUMNS_TO_DROP[dim_name])` ngay trước bước ghi `write_parquet()` cho từng Dim liên quan — không sớm hơn (Dim vẫn cần các cột này để dedup/build key ở bước trước), không muộn hơn (không để lọt ra file Parquet)
3. Nếu 1 use case Gold thật sự cần 1 cột PII cụ thể (chưa phát sinh ở BRD hiện tại), phải là quyết định tường minh thêm vào ngoại lệ có ghi chú — không mặc định giữ lại
**Acceptance Criteria:** `pl.read_parquet('data/gold/<run_date>/dim_customers.parquet').columns` không chứa `phone/address/tax_code/date_of_birth`; tương tự cho `dim_employees`/`dim_distributors`; `data/silver/` vẫn còn đủ cột gốc (không ảnh hưởng Silver).
**💡 Vì sao cần:** Không làm → thông tin cá nhân khách hàng/nhân viên (số điện thoại, địa chỉ, ngày sinh) nằm nguyên trong file Gold — ai đọc được file đó (không cần mở Power BI) đều thấy hết, kể cả khi share file `.pbix` cho người ngoài xem thì cũng không bảo vệ được. Có nó → thông tin nhạy cảm bị cắt trước khi ra khỏi Silver, dù ai đọc file Gold trực tiếp cũng không thấy được.

---

### STORY — P3.2 SCD Type 2 — dim_employees (US-06)

**Labels:** db, phase-3, sprint-3 | **Priority:** High

# 📋 USER STORY: SCD Type 2 — dim_employees

### 👤 User Story

* **As a:** Data Analyst
* **I want to:** biết nhân viên X phụ trách vùng nào tại đúng thời điểm phát sinh đơn hàng (không phải vùng hiện tại)
* **So that:** báo cáo hiệu suất nhân viên không bị sai lệch do chuyển vùng

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** `data/silver/<run_date>/employee_master.parquet` (có `version`, `effective_date`, `resign_date`, `transfer_note`)
* **⚙️ Processing:** Sort theo `employee_id`+`effective_date` → `valid_from` = `effective_date` của chính version đó → `valid_to` = `effective_date` version kế tiếp cùng nhân viên (`shift(-1).over()`), NHƯNG nếu nhân viên có `resign_date` và đây là version cuối (không có version kế tiếp), `valid_to` = `resign_date` chứ KHÔNG để NULL — nếu không, as-of join ở P3.3 sẽ coi version đã nghỉ việc là "còn hiệu lực vô thời hạn" và gán nhầm đơn hàng phát sinh sau ngày nghỉ việc vào nhân viên đó; `is_current` = `valid_to.is_null()` (sau khi đã coalesce với `resign_date`, không cần điều kiện `resign_date.is_null()` riêng nữa)
* **📤 Output:** `dim_employees` với `employee_key, employee_id, name, region, team, valid_from, valid_to, is_current`

---

### ✅ Definition of Ready

- [x] Spec rõ (phase3_gold_production.md Phần A #1 "Thử thách SCD Type 2", BRD US-06)
- [x] Không cần Design
- [x] Blocked By Epic 2 (P2.4)
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** Epic 2 (P2.4) / P3.3
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 3 / 2026-08-23

---

### 🏷️ Metadata

* **Labels:** sprint-3, phase-3, db
* **Priority:** High
* **Story Points:** 5

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given nhân viên X có 2 version (chuyển vùng giữa chừng), When build SCD2, Then version cũ có `valid_to` = ngày version mới bắt đầu, `is_current=False`; version mới `valid_to=NULL`, `is_current=True`
* \[ \] **Scenario 2 (Error/Exception):** Given nhân viên đã `resign_date` (nghỉ việc), When build SCD2, Then version cuối cùng có `valid_to = resign_date` (KHÔNG phải NULL), `is_current=False`
* \[ \] **Scenario 3 (Error/Exception):** Given nhân viên đã nghỉ việc ngày X, có đơn hàng phát sinh SAU ngày X (data rác hoặc case hợp lệ khác), When as-of join `order_date` vào `dim_employees` (P3.3), Then đơn hàng đó KHÔNG match được version đã nghỉ việc (vì `valid_to=resign_date` đã chặn đúng), `employee_key = -1` (Unknown Member, xem P3.1 Scenario 3) thay vì gán nhầm nhân viên nghỉ việc hoặc để NULL

---

### 🔒 Non-Functional Requirements

N/A

---

### 📊 Observability Requirements

N/A

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

Join `dim_employees` vào `fact_sales` theo `order_date` (xem P3.3)

### 🛠️ Technical Notes

```
df = df.sort(["employee_id", "effective_date"]).with_columns(
    pl.col("effective_date").alias("valid_from"),
    pl.col("effective_date").shift(-1).over("employee_id").alias("_next_effective_date"),
).with_columns(
    pl.coalesce(["_next_effective_date", "resign_date"]).alias("valid_to")
).with_columns(
    pl.col("valid_to").is_null().alias("is_current")
).drop("_next_effective_date")
```
Điểm mấu chốt: `valid_to` PHẢI coalesce với `resign_date` — nếu chỉ lấy `shift(-1)` suông thì version cuối của nhân viên đã nghỉ việc bị NULL (hiệu lực vô thời hạn), phá as-of join ở P3.3. Test riêng ở P3.7.

#### SUBTASK — Sort by employee_id+effective_date, compute valid_from/valid_to (coalesce resign_date)  _[SỬA]_

**Labels:** db, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Tính `valid_from`/`valid_to` cho từng version nhân viên — bao gồm đúng case nghỉ việc.
**Input Spec:** `data/silver/<run_date>/employee_master.parquet` (có `version`, `effective_date`, `resign_date`).
**Output/Deliverable:** DataFrame có cột `valid_from`, `valid_to`.
**Tech Stack:** Polars `shift().over()`, `pl.coalesce()`.
**File(s):** `src/transform_gold.py`
**Technical Steps:**
1. `valid_from = effective_date` (trực tiếp, không tính toán thêm)
2. `_next_effective_date = effective_date.shift(-1).over("employee_id")`
3. `valid_to = pl.coalesce(["_next_effective_date", "resign_date"])` — version cuối của nhân viên ĐANG làm (`resign_date` NULL) thì `valid_to` vẫn NULL đúng như kỳ vọng; version cuối của nhân viên ĐÃ nghỉ thì `valid_to = resign_date`, không NULL
**Acceptance Criteria:** Version cũ (không phải cuối) có `valid_to` = `effective_date` version kế tiếp; version cuối cùng của nhân viên đã nghỉ có `valid_to = resign_date` (không phải NULL); version cuối cùng của nhân viên đang làm có `valid_to = NULL`.
**💡 Vì sao cần:** Không làm → nếu chỉ lấy version kế tiếp mà quên tính ngày nghỉ việc, nhân viên đã nghỉ sẽ bị coi là "còn hiệu lực vô thời hạn" — đơn hàng phát sinh SAU khi người đó đã nghỉ việc thật vẫn bị tính vào doanh số của họ, báo cáo hiệu suất nhân viên sai. Có nó → biết chính xác nhân viên nào phụ trách vùng nào tại đúng thời điểm nào, kể cả sau khi họ đã nghỉ việc.

#### SUBTASK — Derive is_current flag  _[SỬA]_

**Labels:** db, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Đánh dấu version hiện hành của mỗi nhân viên.
**Input Spec:** DataFrame có `valid_to` đã coalesce với `resign_date` (subtask trước).
**Output/Deliverable:** Cột `is_current` (Boolean).
**Tech Stack:** Polars.
**File(s):** `src/transform_gold.py`
**Technical Steps:** `is_current = valid_to.is_null()` — vì `valid_to` đã coalesce với `resign_date` ở subtask trước, không cần điều kiện `resign_date.is_null()` riêng nữa (đơn giản hơn bản cũ, tránh 2 nguồn sự thật cho cùng 1 kết luận).
**Acceptance Criteria:** Nhân viên đã `resign_date` không có version nào `is_current=True`.
**💡 Vì sao cần:** Không làm → không biết version nào là "hiện tại" của mỗi nhân viên, khó lấy đúng thông tin mới nhất (vùng/team hiện tại) khi cần. Có nó → chỉ cần lọc `is_current=True` là ra đúng trạng thái mới nhất của từng người, và người đã nghỉ việc không bị nhầm là đang hoạt động.

#### SUBTASK — Generate surrogate employee_key

**Labels:** db, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Sinh khóa thay thế cho mỗi dòng lịch sử nhân viên (1 employee_id có nhiều employee_key theo version).
**Input Spec:** DataFrame đã có `valid_to`, `is_current`.
**Output/Deliverable:** Cột `employee_key` duy nhất từng dòng.
**Tech Stack:** Polars `with_row_index`.
**File(s):** `src/transform_gold.py`
**Technical Steps:** `df.with_row_index("employee_key")`.
**Acceptance Criteria:** Mỗi dòng (mỗi version nhân viên) có `employee_key` riêng biệt, không trùng.
**💡 Vì sao cần:** Không làm → 1 nhân viên có nhiều version (do đổi vùng) nhưng dùng chung `employee_id` để join thì không phân biệt được đơn hàng thuộc version nào — join lung tung, sai vùng. Có nó → mỗi version là 1 dòng độc lập với khóa riêng, join đúng chính xác version tại thời điểm cần.

#### SUBTASK — Unit test SCD2 valid_to correctness, gồm case nghỉ việc (small fixture)  _[SỬA]_

**Labels:** db, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Verify sớm logic SCD2 đúng trước khi P3.7 viết test chính thức — bắt buộc phải phủ case nghỉ việc, không chỉ case chuyển vùng.
**Input Spec:** Fixture DataFrame nhỏ: (1) 1 nhân viên đổi vùng 2 version, (2) 1 nhân viên đã nghỉ việc (`resign_date` khác NULL).
**Output/Deliverable:** Kết quả kiểm tra thủ công xác nhận `valid_from`/`valid_to`/`is_current` đúng cho cả 2 case.
**Tech Stack:** Polars, python REPL/script tạm.
**File(s):** N/A (dev verification, test chính thức ở P3.7)
**Technical Steps:** Tạo DataFrame giả lập nhỏ gồm cả nhân viên đổi vùng và nhân viên nghỉ việc, chạy hàm SCD2, in kết quả so sánh kỳ vọng — đặc biệt kiểm `valid_to` của version cuối nhân viên nghỉ việc PHẢI = `resign_date`, không phải NULL.
**Acceptance Criteria:** Kết quả khớp kỳ vọng tay cho cả 2 case trước khi coi P3.2 là Done.
**💡 Vì sao cần:** Không làm → logic SCD2 khá rối (shift, coalesce, over) — code xong tưởng đúng nhưng chạy trên data thật mới lộ sai, lúc đó đã tốn công build cả Gold layer trên nền sai. Có nó → kiểm tra bằng data giả nhỏ, biết chắc đúng trước khi build tiếp lên trên (fact_sales phụ thuộc vào cái này).

---

### STORY — P3.3 Fact Tables — fact_sales/fact_targets

**Labels:** db, phase-3, sprint-3 | **Priority:** High

# 📋 USER STORY: Fact Tables — fact_sales/fact_targets

### 👤 User Story

* **As a:** Data Analyst
* **I want to:** `fact_sales`/`fact_targets` có sẵn surrogate key từ các Dim, giữ lineage
* **So that:** query doanh số theo vùng/sản phẩm/nhân viên chỉ cần JOIN đơn giản

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** `data/silver/<run_date>/{sales_transactions,sales_target_plan}.parquet` + `dim_customers`, `dim_products`, `dim_employees` (SCD2), `dim_date` (từ P3.1, P3.2)
* **⚙️ Processing:** `.join()` tra cứu surrogate key; join `dim_employees` theo điều kiện `valid_from <= order_date < valid_to` (as-of join, không phải join theo `employee_id` thường)
* **📤 Output:** `fact_sales`, `fact_targets` với FK đúng, giữ `_run_date`, `_batch_id`

---

### ✅ Definition of Ready

- [x] Spec rõ (phase3_gold_production.md Phần A #2)
- [x] Không cần Design
- [x] Blocked By P3.1, P3.2
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** P3.1, P3.2 / P3.5
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 3 / 2026-08-23

---

### 🏷️ Metadata

* **Labels:** sprint-3, phase-3, db
* **Priority:** High
* **Story Points:** 5

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given đơn hàng của nhân viên X đổi vùng giữa chừng, When join `fact_sales` với `dim_employees` SCD2, Then FK trỏ đúng `employee_key` có `region` hiệu lực tại `order_date` của đơn hàng đó (không phải vùng hiện tại)
* \[ \] **Scenario 2 (Error/Exception):** Given 1 dòng `sales_transactions` có `customer_id` không tồn tại trong `dim_customers` (data rác), When join, Then `customer_key = -1` (Unknown Member, xem P3.1 Scenario 3) thay vì crash hoặc NULL, dòng vẫn giữ trong fact để không mất doanh thu, filter được `customer_key = -1` khi audit
* \[ \] **Scenario 3 (Error/Exception):** Given nhân viên đã nghỉ việc (P3.2 đảm bảo `valid_to = resign_date`), When có đơn hàng phát sinh sau ngày nghỉ việc, Then as-of join KHÔNG match version đã nghỉ, `employee_key = -1` (Unknown Member) thay vì gán nhầm hoặc NULL

---

### 🔒 Non-Functional Requirements

N/A

---

### 📊 Observability Requirements

N/A

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

`fact_returns`/`fact_distributor_orders` (P3.4), `mart_sales_vs_target` (P3.5)

### 🛠️ Technical Notes

As-of join SCD2: dùng `join_asof` của Polars hoặc filter điều kiện range join thủ công theo `order_date` nằm giữa `valid_from`/`valid_to`. Mọi join Fact→Dim trong story này dùng **left join** + `.fill_null(-1)` trên cột FK ngay sau join — không có FK nào được để NULL (xem P3.1 Scenario 3, "Unknown Member").

#### SUBTASK — fact_sales join dim_customers/dim_products/dim_employees(SCD2)/dim_date  _[SỬA]_

**Labels:** db, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Build `fact_sales` với đầy đủ FK, đặc biệt as-of join SCD2, không FK nào để NULL.
**Input Spec:** `data/silver/<run_date>/sales_transactions.parquet` + `dim_customers`, `dim_products`, `dim_employees`, `dim_date` (đã có dòng Unknown Member key=-1).
**Output/Deliverable:** `fact_sales` với `customer_key, product_key, employee_key, date_key` đúng — FK không match trả `-1`, không trả NULL.
**Tech Stack:** Polars `join(how="left")`/`join_asof`, `.fill_null(-1)`.
**File(s):** `src/transform_gold.py`
**Technical Steps:** Left join với `dim_customers`/`dim_products`/`dim_date`, `.fill_null(-1)` trên `customer_key`/`product_key` ngay sau join; as-of join SCD2 với `dim_employees` theo điều kiện `order_date` nằm trong `[valid_from, valid_to)`, không match (hoặc match dòng Unknown Member tĩnh) thì `employee_key = -1`.
**Acceptance Criteria:** Đơn hàng của nhân viên đổi vùng trỏ đúng `employee_key` có `region` hiệu lực tại `order_date`; không có dòng nào trong `fact_sales` có FK NULL — chỉ `-1` hoặc key thật.
**💡 Vì sao cần:** Không làm → đây là bước biến giao dịch bán hàng thô thành bảng "trung tâm" của Star Schema — không join được vào Dim thì không xem được doanh số theo khách hàng/sản phẩm/nhân viên/ngày, cả mục tiêu Phase 3 (báo cáo doanh số theo vùng) không làm được. Có nó → mỗi giao dịch biết chính xác thuộc khách hàng nào, sản phẩm nào, nhân viên nào (đúng vùng tại thời điểm bán), ngày nào.

#### SUBTASK — fact_targets join dim_employees (as-of), giữ year/month riêng — KHÔNG ép qua dim_date  _[SỬA]_

**Labels:** db, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Build `fact_targets` với FK, quyết định dứt khoát cách xử lý lệch grain thay vì để "hoặc" tùy chọn lúc code.
**Input Spec:** `data/silver/<run_date>/sales_target_plan.parquet` (grain tháng, có `year`, `month`) + `dim_employees` (SCD2, grain ngày).
**Output/Deliverable:** `fact_targets` với `employee_key` (as-of join), giữ nguyên `year`, `month` làm cột thuộc tính — KHÔNG tạo `date_key` giả để ép join vào `dim_date` (grain ngày không khớp grain tháng của target).
**Tech Stack:** Polars join.
**File(s):** `src/transform_gold.py`
**Technical Steps:**
1. As-of join `dim_employees` theo cùng cơ chế P3.3 subtask 1: dùng ngày đầu tháng (`date(year, month, 1)`) của target làm mốc so với `[valid_from, valid_to)` — nhất quán với cách `fact_sales` join `dim_employees`, không phải logic riêng thứ 2
2. Không match (hoặc match dòng Unknown Member tĩnh) → `employee_key = -1`, không để NULL — cùng chuẩn P3.3/P3.4
3. Giữ `year`, `month` (Int) làm cột thuộc tính trực tiếp trên `fact_targets` — Data Mart P3.5 group theo `region+month` dùng thẳng 2 cột này, không cần join `dim_date`
**Acceptance Criteria:** `fact_targets` có `employee_key` hợp lệ theo đúng version SCD2 tại thời điểm target được set (hoặc `-1` nếu không match); số dòng khớp `sales_target_plan` gốc; không có cột `date_key` giả mạo trên `fact_targets`; không có FK NULL.
**💡 Vì sao cần:** Không làm → không có bảng `target` (chỉ tiêu) join đúng với nhân viên, không so sánh được "thực tế vs chỉ tiêu" — mà đây chính là báo cáo chính giám đốc yêu cầu (mart_sales_vs_target). Có nó → target của mỗi nhân viên/tháng gắn đúng với version SCD2 phù hợp, không bị ép sai vào cấu trúc ngày hàng ngày không khớp với bản chất theo tháng của nó.

#### SUBTASK — Preserve _run_date,_batch_id lineage cols on fact tables

**Labels:** db, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Giữ lineage xuyên suốt tới Gold để biết batch nào nạp dữ liệu.
**Input Spec:** `fact_sales`/`fact_targets` sau join (2 subtask trước).
**Output/Deliverable:** Fact table vẫn có `_run_date`, `_batch_id`.
**Tech Stack:** Polars.
**File(s):** `src/transform_gold.py`
**Technical Steps:** Đảm bảo `select()`/`join()` không vô tình drop 2 cột metadata này.
**Acceptance Criteria:** `fact_sales.columns` chứa `_run_date`, `_batch_id`.
**💡 Vì sao cần:** Không làm → thao tác `select()`/`join()` rất dễ vô tình chỉ giữ lại cột mình cần mà bỏ quên cột lineage — tới Gold không còn biết dòng dữ liệu này đến từ lần chạy pipeline nào. Có nó → dấu vết nguồn gốc đi theo dữ liệu tới tận Gold, vẫn truy vết được khi có sự cố dù đã qua 3 lớp Bronze→Silver→Gold.

---

### STORY — P3.4 fact_returns/fact_distributor_orders + dim_territory/dim_promotion

**Labels:** db, phase-3, sprint-3 | **Priority:** Medium

# 📋 USER STORY: Supplementary Fact & Dimension Tables

### 👤 User Story

* **As a:** Marketer/Data Analyst
* **I want to:** có `fact_returns`, `fact_distributor_orders`, `dim_territory`, `dim_promotion`
* **So that:** phân tích trả hàng, hiệu suất NPP, và làm nền cho đánh giá khuyến mãi (Epic 4)

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** `data/silver/<run_date>/{return_transactions,distributor_orders,territory_mapping,promotion_program}.parquet` + Dim đã build (P3.1)
* **⚙️ Processing:** Build `dim_territory` (từ `territory_mapping`), `dim_promotion` (từ `promotion_program`); join FK vào `fact_returns`, `fact_distributor_orders`
* **📤 Output:** `dim_territory`, `dim_promotion`, `fact_returns`, `fact_distributor_orders` sẵn sàng ghi Gold

---

### ✅ Definition of Ready

- [x] Spec rõ (BRD §2.4 Star Schema diagram)
- [x] Không cần Design
- [x] Blocked By P3.1
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** P3.1 / Epic 4 (P4.3 dùng dim_promotion + fact_distributor_orders)
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 3 / 2026-08-24

---

### 🏷️ Metadata

* **Labels:** sprint-3, phase-3, db
* **Priority:** Medium
* **Story Points:** 5

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given `distributor_orders` + `dim_distributors`/`dim_products`, When join, Then `fact_distributor_orders` có đủ FK, giữ `fill_rate_pct`, `ontime_delivery`
* \[ \] **Scenario 2 (Error/Exception):** Given `promotion_program` có `applicable_products` là chuỗi nhiều mã sản phẩm phân cách bởi dấu phẩy (không phải 1 FK đơn), When build `dim_promotion`, Then giữ nguyên dạng text để Epic 4 tự xử lý join theo khoảng ngày ở tầng BI (không ép quan hệ 1-1 sai)

---

### 🔒 Non-Functional Requirements

N/A

---

### 📊 Observability Requirements

N/A

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

Tính Promotion Uplift/ROI (đó là DAX measure ở Epic 4, không phải Gold layer)

### 🛠️ Technical Notes

`dim_promotion` giữ nguyên `applicable_products`, `start_date`, `end_date` để Power BI join theo khoảng ngày ở P4.3.

#### SUBTASK — dim_territory + dim_promotion build (+ Unknown Member)  _[SỬA]_

**Labels:** db, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Build 2 Dim còn lại, đủ dòng Unknown Member (key=-1) theo quyết định chung ở P3.1.
**Input Spec:** `data/silver/<run_date>/{territory_mapping,promotion_program}.parquet`, helper `add_unknown_member()` (P3.1).
**Output/Deliverable:** `dim_territory`, `dim_promotion` với surrogate key + dòng Unknown Member.
**Tech Stack:** Polars.
**File(s):** `src/transform_gold.py`
**Technical Steps:** Select cột, sinh surrogate key cho từng bảng (bắt đầu từ `1`), gọi `add_unknown_member()` thêm dòng `key=-1`.
**Acceptance Criteria:** 2 Dim có key duy nhất, giữ nguyên `start_date`/`end_date`/`applicable_products` cho `dim_promotion`; mỗi Dim có đúng 1 dòng key=-1.
**💡 Vì sao cần:** Không làm → không có bảng riêng cho khu vực/chương trình khuyến mãi, phân tích hiệu quả khuyến mãi và khu vực phải join thẳng Silver, phức tạp và dễ sai. Có nó → có bảng chiều sẵn sàng cho khu vực và khuyến mãi, join vào Fact đơn giản, đồng bộ cách xử lý "không match" như các Dim khác.

#### SUBTASK — fact_returns join dims (left join + fill_null(-1))  _[SỬA]_

**Labels:** db, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Build `fact_returns` với FK, không FK nào để NULL.
**Input Spec:** `data/silver/<run_date>/return_transactions.parquet` + `dim_customers`, `dim_products`, `dim_employees` (đã có Unknown Member).
**Output/Deliverable:** `fact_returns` với FK hợp lệ, FK không match = `-1`.
**Tech Stack:** Polars `join(how="left")`, `.fill_null(-1)`.
**File(s):** `src/transform_gold.py`
**Technical Steps:** Left join theo `customer_id`/`product_id`/`employee_id`, `.fill_null(-1)` trên cột FK ngay sau join, giữ `_run_date`/`_batch_id`.
**Acceptance Criteria:** Số dòng `fact_returns` khớp `return_transactions` gốc; không có FK NULL, chỉ `-1` hoặc key thật.
**💡 Vì sao cần:** Không làm → không phân tích được tình trạng trả hàng theo khách hàng/sản phẩm/nhân viên nào, mất khả năng đánh giá chất lượng sản phẩm hay dịch vụ. Có nó → biết chính xác ai trả hàng gì, của nhân viên nào bán, phục vụ phân tích chất lượng/dịch vụ.

#### SUBTASK — fact_distributor_orders join dim_distributors/dim_products (left join + fill_null(-1))  _[SỬA]_

**Labels:** db, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Build `fact_distributor_orders` với FK, không FK nào để NULL.
**Input Spec:** `data/silver/<run_date>/distributor_orders.parquet` + `dim_distributors`, `dim_products` (đã có Unknown Member).
**Output/Deliverable:** `fact_distributor_orders` giữ `fill_rate_pct`, `ontime_delivery`, FK hợp lệ, FK không match = `-1`.
**Tech Stack:** Polars `join(how="left")`, `.fill_null(-1)`.
**File(s):** `src/transform_gold.py`
**Technical Steps:** Left join theo `distributor_id`/`product_id`, `.fill_null(-1)` trên cột FK ngay sau join, giữ nguyên cột đo lường fill-rate/on-time.
**Acceptance Criteria:** `fact_distributor_orders` có đủ FK + cột đo lường, số dòng khớp gốc; không có FK NULL.
**💡 Vì sao cần:** Không làm → không đánh giá được nhà phân phối nào giao hàng đúng hạn/đủ số lượng, mất công cụ để quản lý hiệu suất NPP. Có nó → có bảng đo lường hiệu suất giao hàng theo từng NPP/sản phẩm, phục vụ trang Dashboard Promotion & Distributor Performance ở Epic 4.

---

### STORY — P3.5 Data Mart — mart_sales_vs_target (US-04)

**Labels:** dashboard, phase-3, sprint-3 | **Priority:** High

# 📋 USER STORY: Data Mart — mart_sales_vs_target

### 👤 User Story

* **As a:** Marketer
* **I want to:** xem báo cáo Doanh số thực tế vs Target theo vùng & tháng
* **So that:** biết vùng nào đang lệch chỉ tiêu

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** `fact_sales`, `fact_targets` (Gold, từ P3.3)
* **⚙️ Processing:** `.group_by(["region","month"]).agg()` tổng `net_amount` (actual) và `target_revenue`; tính `variance_pct`
* **📤 Output:** `mart_sales_vs_target` với cột `region, month, actual_revenue, target_revenue, variance_pct`

---

### ✅ Definition of Ready

- [x] Spec rõ (phase3_gold_production.md Phần A #3, BRD US-04)
- [x] Không cần Design
- [x] Blocked By P3.3
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** P3.3 / P3.7 (test data mart logic), Epic 4 (P4.2 dashboard)
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 3 / 2026-08-24

---

### 🏷️ Metadata

* **Labels:** sprint-3, phase-3, dashboard
* **Priority:** High
* **Story Points:** 3

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given `fact_sales`/`fact_targets` của 1 vùng/tháng, When group_by+agg, Then `actual_revenue`/`target_revenue` khớp tổng tính tay
* \[ \] **Scenario 2 (Error/Exception):** Given 1 vùng có `fact_sales` nhưng không có `fact_targets` tương ứng (chưa set target), When agg, Then `target_revenue` = 0 hoặc NULL rõ ràng (không làm crash phép chia `variance_pct`)

---

### 🔒 Non-Functional Requirements

N/A

---

### 📊 Observability Requirements

N/A

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

Dashboard trực quan hóa (Epic 4, P4.2)

### 🛠️ Technical Notes

`variance_pct = (actual_revenue - target_revenue) / target_revenue` — cần guard chia 0.

#### SUBTASK — group_by/agg actual vs target revenue by region+month

**Labels:** dashboard, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Tổng hợp doanh số thực tế và target theo vùng+tháng.
**Input Spec:** `fact_sales`, `fact_targets` (từ P3.3).
**Output/Deliverable:** DataFrame `mart_sales_vs_target` với `region, month, actual_revenue, target_revenue`.
**Tech Stack:** Polars `group_by().agg()`.
**File(s):** `src/transform_gold.py`
**Technical Steps:** `fact_sales.group_by(["region","month"]).agg(pl.col("net_amount").sum().alias("actual_revenue"))` join với target đã agg tương tự.
**Acceptance Criteria:** Tổng khớp tính tay trên dữ liệu mẫu nhỏ.
**💡 Vì sao cần:** Không làm → đây chính là báo cáo giám đốc yêu cầu ("Doanh số thực tế so với Target theo vùng") — không có subtask này thì mục tiêu chính của cả Phase 3 không đạt được. Có nó → có sẵn 1 bảng tổng hợp gọn, Marketer xem ngay vùng nào đạt/không đạt chỉ tiêu mà không cần tính tay.

#### SUBTASK — Compute variance_pct column

**Labels:** dashboard, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Tính phần trăm chênh lệch thực tế vs target.
**Input Spec:** DataFrame có `actual_revenue`, `target_revenue` (subtask trước).
**Output/Deliverable:** Cột `variance_pct`.
**Tech Stack:** Polars.
**File(s):** `src/transform_gold.py`
**Technical Steps:** `(actual_revenue - target_revenue) / target_revenue`, guard chia 0 khi `target_revenue` = 0 hoặc NULL (trả NULL thay vì lỗi).
**Acceptance Criteria:** Không có dòng nào crash/Inf khi `target_revenue=0`.
**💡 Vì sao cần:** Không làm → vùng nào chưa được set target (`target_revenue=0`) làm phép chia lỗi (`chia cho 0`), cả pipeline hoặc cả dashboard crash chỉ vì 1 vùng thiếu dữ liệu target. Có nó → % chênh lệch tính đúng cho vùng có target, còn vùng chưa có target hiển thị rõ ràng (NULL/N-A) thay vì làm sập cả báo cáo.

#### SUBTASK — write_parquet mart_sales_vs_target to data/gold/<run_date>/

**Labels:** db, migration, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Ghi Data Mart ra Gold layer, và toàn bộ Dim/Fact khác từ P3.1-P3.4.
**Input Spec:** Toàn bộ DataFrame Dim/Fact/Mart đã build (P3.1-P3.5).
**Output/Deliverable:** `data/gold/<run_date>/*.parquet` (đủ dim\__, fact\__, mart_sales_vs_target).
**Tech Stack:** Polars.
**File(s):** `src/transform_gold.py`
**Technical Steps:** `os.makedirs(f"data/gold/{run_date}", exist_ok=True)` → `write_parquet()` cho từng bảng.
**Acceptance Criteria:** `data/gold/<run_date>/` chứa đủ dim_customers, dim_products, dim_distributors, dim_date, dim_territory, dim_promotion, dim_employees, fact_sales, fact_targets, fact_returns, fact_distributor_orders, mart_sales_vs_target.
**💡 Vì sao cần:** Không làm → toàn bộ Dim/Fact/Mart chỉ nằm trong bộ nhớ tạm, tắt chương trình mất hết, Power BI (Epic 4) không có gì để kết nối vào. Có nó → có đủ 12 bảng dưới dạng file, Power BI kết nối thẳng vào đọc, không cần chạy lại pipeline mỗi lần mở dashboard.

---

### STORY — P3.6 Lazy Evaluation Refactor

**Labels:** backend, phase-3, sprint-3 | **Priority:** Medium

# 📋 USER STORY: Lazy Evaluation Refactor

### 👤 User Story

* **As a:** Admin/Data Engineer
* **I want to:** Silver + Gold dùng `pl.scan_parquet()` (Lazy API) thay vì `pl.read_parquet()` (Eager API)
* **So that:** khai thác tối đa trình tối ưu hóa bộ nhớ của Polars, chỉ `collect()` ở bước ghi cuối cùng

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** Code Silver/Gold hiện tại (P2.1-P2.4, P3.1-P3.5) dùng `pl.read_parquet()`
* **⚙️ Processing:** Đổi `pl.read_parquet()` → `pl.scan_parquet()`; chain toàn bộ transform trên LazyFrame; chỉ `.collect()` ngay trước `write_parquet()`
* **📤 Output:** Pipeline Silver+Gold chạy bằng LazyFrame xuyên suốt, kết quả số liệu giống hệt bản Eager

---

### ✅ Definition of Ready

- [x] Spec rõ (phase3_gold_production.md Phần B #1)
- [x] Không cần Design
- [x] Blocked By P3.1-P3.5 (đã có logic Eager hoạt động đúng để refactor)
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** P3.1, P3.2, P3.3, P3.4, P3.5 / P3.8
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 3 / 2026-08-24

---

### 🏷️ Metadata

* **Labels:** sprint-3, phase-3, backend
* **Priority:** Medium
* **Story Points:** 2

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given pipeline đã refactor sang Lazy, When chạy `--layer all`, Then output Gold giống hệt số liệu bản Eager trước refactor (regression check bằng tay)
* \[ \] **Scenario 2 (Error/Exception):** Given 1 bước transform quên `.collect()` trước khi ghi, When chạy `write_parquet()` trên LazyFrame chưa collect, Then phát hiện lỗi rõ ràng (Polars raise lỗi type), không ghi ra file rác

---

### 🔒 Non-Functional Requirements

N/A

---

### 📊 Observability Requirements

N/A

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

Viết test (P3.7), CLI (P3.8)

### 🛠️ Technical Notes

`pl.scan_parquet(path).with_columns(...).filter(...).collect()` — chain toàn bộ transform trước collect cuối.

#### SUBTASK — Refactor read_parquet→scan_parquet in Silver+Gold modules

**Labels:** backend, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Đổi toàn bộ entrypoint đọc file sang Lazy API.
**Input Spec:** `src/transform_silver.py`, `src/transform_gold.py` hiện dùng `pl.read_parquet()`.
**Output/Deliverable:** Code dùng `pl.scan_parquet()` xuyên suốt, `.collect()` chỉ trước `write_parquet()`.
**Tech Stack:** Polars Lazy API.
**File(s):** `src/transform_silver.py`, `src/transform_gold.py`
**Technical Steps:** Thay từng `pl.read_parquet(path)` → `pl.scan_parquet(path)`; thêm `.collect()` ngay trước mỗi `write_parquet()` call.
**Acceptance Criteria:** Chạy lại `--layer silver` và `--layer gold`, output số liệu giống hệt bản trước refactor.
**💡 Vì sao cần:** Không làm → `pl.read_parquet()` (Eager) đọc toàn bộ file vào RAM ngay lập tức dù chỉ cần vài cột/vài dòng, tốn bộ nhớ và chậm hơn khi data lớn dần. Có nó → Polars biết trước toàn bộ các bước cần làm (Lazy), tự tối ưu chỉ đọc/xử lý đúng phần cần thiết, tiết kiệm bộ nhớ và nhanh hơn — quan trọng khi dữ liệu tăng theo thời gian.

---

### STORY — P3.7 Pytest — SCD2 + Data Mart logic

**Labels:** backend, phase-3, sprint-3 | **Priority:** High

# 📋 USER STORY: Automated Testing — pytest

### 👤 User Story

* **As a:** Admin/Data Engineer
* **I want to:** ≥2 test tự động cho logic Data Mart và SCD Type 2
* **So that:** đảm bảo logic tính toán đúng trước khi merge code, không chỉ "chạy ra số"

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** DataFrame giả lập siêu nhỏ (fixture) mô phỏng `fact_sales`/`fact_targets` và `employee_master`
* **⚙️ Processing:** Viết `test_mart_sales_vs_target()` và `test_scd2_valid_to()` trong `test_pipeline.py`
* **📤 Output:** `uv run pytest test_pipeline.py` trả về PASSED 100%

---

### ✅ Definition of Ready

- [x] Spec rõ (phase3_gold_production.md Phần B #2)
- [x] Không cần Design
- [x] Blocked By P3.2 (SCD2 logic), P3.5 (Data Mart logic) đã có code thật để test
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** P3.2, P3.5 / P3.8
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 3 / 2026-08-24

---

### 🏷️ Metadata

* **Labels:** sprint-3, phase-3, backend
* **Priority:** High
* **Story Points:** 3

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given fixture DataFrame nhỏ mô phỏng đúng số liệu, When chạy `test_mart_sales_vs_target()`, Then assert `actual_revenue`/`target_revenue`/`variance_pct` đúng giá trị kỳ vọng tính tay
* \[ \] **Scenario 2 (Error/Exception):** Given fixture nhân viên đổi vùng giữa chừng (2 version), When chạy `test_scd2_valid_to()`, Then assert `valid_to` của version cũ = `effective_date` của version mới, không phải NULL
* \[ \] **Scenario 3 (Error/Exception):** Given fixture nhân viên có `resign_date`, When chạy `test_scd2_valid_to()`, Then assert `valid_to` của version cuối = `resign_date` (không phải NULL) — đây là case hay bị bỏ sót, phải test riêng

---

### 🔒 Non-Functional Requirements

N/A

---

### 📊 Observability Requirements

N/A

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

Test integration full pipeline (chỉ unit test logic transform theo đúng yêu cầu phase3)

### 🛠️ Technical Notes

Sau khi có test thật, quay lại S0.3 (CI Pipeline Skeleton) cập nhật workflow chạy `pytest` thật thay vì `--collect-only` placeholder.

#### SUBTASK — test_mart_sales_vs_target() với fixture nhỏ giả lập

**Labels:** backend, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Test tự động logic Data Mart.
**Input Spec:** Fixture DataFrame nhỏ mô phỏng `fact_sales`/`fact_targets` (2-3 dòng, số liệu biết trước).
**Output/Deliverable:** Hàm `test_mart_sales_vs_target()` trong `test_pipeline.py`.
**Tech Stack:** pytest, Polars.
**File(s):** `tests/test_pipeline.py`
**Technical Steps:** Tạo fixture, gọi hàm build mart (P3.5), assert `actual_revenue`/`target_revenue`/`variance_pct` đúng giá trị tính tay.
**Acceptance Criteria:** `uv run pytest -k test_mart_sales_vs_target` pass.
**💡 Vì sao cần:** Không làm → công thức tính doanh số/target chỉ được kiểm bằng mắt 1 lần lúc code, ai sửa code sau này (kể cả sửa nhầm 1 dấu trừ thành cộng) không ai phát hiện, báo cáo giám đốc xem sẽ sai mà không biết. Có nó → có phép thử tự động với số liệu biết trước đáp án, sai là biết ngay.

#### SUBTASK — test_scd2_valid_to() kiểm tra valid_to đúng khi đổi vùng VÀ khi nghỉ việc  _[SỬA]_

**Labels:** backend, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Test tự động logic SCD Type 2, bắt buộc phủ cả case nghỉ việc (P3.2 Scenario 2/3) chứ không chỉ case đổi vùng.
**Input Spec:** Fixture DataFrame nhỏ mô phỏng `employee_master`: (1) 1 nhân viên 2 version đổi vùng, (2) 1 nhân viên có `resign_date`.
**Output/Deliverable:** Hàm `test_scd2_valid_to()` trong `test_pipeline.py`.
**Tech Stack:** pytest, Polars.
**File(s):** `tests/test_pipeline.py`
**Technical Steps:** Tạo fixture gồm cả 2 case, gọi hàm SCD2 (P3.2), assert `valid_to` version cũ = `effective_date` version mới; assert `valid_to` version cuối của nhân viên nghỉ việc = `resign_date` (KHÔNG phải NULL); assert `is_current` đúng cho cả 2 case.
**Acceptance Criteria:** `uv run pytest -k test_scd2_valid_to` pass, bao gồm assertion riêng cho case nghỉ việc.
**💡 Vì sao cần:** Không làm → logic SCD2 (đổi vùng, nghỉ việc) rất dễ bị ai đó vô tình sửa hỏng khi refactor code sau này, và bug loại này (như case nghỉ việc bị bỏ NULL) đã từng xảy ra ngay trong chính bản backlog gốc — nếu không test thì lỗi tương tự dễ tái diễn không ai biết. Có nó → mỗi lần sửa code, chạy test là biết ngay còn đúng hay không.

#### SUBTASK — Wire pytest vào CI pipeline skeleton (cập nhật S0.3)

**Labels:** backend, devops, phase-3, sprint-3 | **Priority:** Medium

**Goal:** CI chạy test thật thay vì `--collect-only` placeholder.
**Input Spec:** `.github/workflows/ci.yml` (từ S0.3), 2 test mới (2 subtask trước).
**Output/Deliverable:** CI workflow chạy `uv run pytest` đầy đủ (không chỉ collect-only).
**Tech Stack:** GitHub Actions, pytest.
**File(s):** `.github/workflows/ci.yml`
**Technical Steps:** Sửa step `pytest --collect-only` → `pytest` (chạy test thật).
**Acceptance Criteria:** CI job pass với 2 test thật, không còn chỉ collect-only.
**💡 Vì sao cần:** Không làm → có test thật nhưng chỉ chạy tay trên máy mình, quên chạy 1 lần là commit code lỗi lên mà không ai biết cho tới khi merge. Có nó → mỗi lần push, CI tự chạy test thật, chặn merge nếu test fail — không phụ thuộc vào việc "có nhớ chạy test tay hay không".

---

### STORY — P3.8 CLI Orchestration (main.py --layer --run-date)

**Labels:** backend, phase-3, sprint-3 | **Priority:** High

# 📋 USER STORY: CLI Orchestration

### 👤 User Story

* **As a:** Admin
* **I want to:** 1 lệnh CLI duy nhất điều phối toàn bộ Bronze/Silver/Gold
* **So that:** vận hành pipeline không cần nhớ chạy nhiều script rời rạc

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** Tham số CLI `--layer` (bronze|silver|gold|all), `--run-date`
* **⚙️ Processing:** `argparse` parse tham số → gọi đúng module (`extract.py`/`transform_silver.py`/`transform_gold.py`) theo `--layer`; `--layer all` chạy tuần tự cả 3
* **📤 Output:** `uv run main.py --layer all --run-date 2026-07-22` chạy end-to-end Google Drive → Gold trong 1 lệnh

---

### ✅ Definition of Ready

- [x] Spec rõ (phase3_gold_production.md Phần B #3)
- [x] Không cần Design
- [x] Blocked By P3.6 (Lazy refactor), P3.7 (test đã có)
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** P3.6, P3.7 / Epic 4 (toàn bộ Epic 4 cần Gold data từ CLI này)
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 3 / 2026-08-24

---

### 🏷️ Metadata

* **Labels:** sprint-3, phase-3, backend
* **Priority:** High
* **Story Points:** 3

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given `uv run main.py --layer all --run-date 2026-08-22`, When chạy, Then pipeline chạy tuần tự Bronze→Silver→Gold không lỗi, đủ output ở mỗi lớp
* \[ \] **Scenario 2 (Error/Exception):** Given `--layer` nhận giá trị không hợp lệ (vd `--layer foo`), When chạy, Then `argparse` báo lỗi rõ ràng liệt kê giá trị hợp lệ, không crash mơ hồ

---

### 🔒 Non-Functional Requirements

N/A

---

### 📊 Observability Requirements

Log toàn bộ `--layer` nào đang chạy, `run_date`, qua `src/logger.py` (S0.5)

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

Scheduler tự động chạy hàng ngày (Airflow) — ghi chú kiến trúc mở rộng trong BRD nhưng ngoài scope capstone

### 🛠️ Technical Notes

`argparse.add_argument("--layer", choices=["bronze","silver","gold","all"], required=True)`

#### SUBTASK — argparse setup với --layer,--run-date, validate input

**Labels:** backend, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Thiết lập CLI entrypoint.
**Input Spec:** Yêu cầu tham số `--layer` (bronze|silver|gold|all), `--run-date` (YYYY-MM-DD).
**Output/Deliverable:** `main.py` với `argparse.ArgumentParser`.
**Tech Stack:** argparse.
**File(s):** `main.py`
**Technical Steps:** `parser.add_argument("--layer", choices=[...], required=True)`, `parser.add_argument("--run-date", required=True)`.
**Acceptance Criteria:** `uv run main.py --help` hiển thị đủ 2 tham số với mô tả rõ.
**💡 Vì sao cần:** Không làm → không có cách nào nói cho chương trình biết "chạy layer nào, ngày nào" — phải sửa code tay mỗi lần muốn đổi. Có nó → chạy bằng tham số dòng lệnh, đổi ngày/layer không cần sửa code, gõ sai tham số cũng được báo lỗi rõ ràng.

#### SUBTASK — Wire --layer=bronze/silver/gold gọi đúng module tương ứng

**Labels:** backend, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Điều phối gọi đúng module theo `--layer`.
**Input Spec:** `args.layer`, `args.run_date` từ argparse (subtask trước).
**Output/Deliverable:** `main.py` gọi `extract.run(run_date)` / `transform_silver.run(run_date)` / `transform_gold.run(run_date)` tùy `--layer`.
**Tech Stack:** Python.
**File(s):** `main.py`
**Technical Steps:** `if args.layer == "bronze": extract.run(...)` tương tự cho silver/gold.
**Acceptance Criteria:** `--layer bronze` chỉ chạy Bronze, không chạy Silver/Gold.
**💡 Vì sao cần:** Không làm → mỗi lần chỉ muốn chạy lại 1 layer (VD Silver bị lỗi, muốn chạy lại riêng Silver) lại phải chạy hết cả pipeline từ đầu, tốn thời gian và có thể tải lại Google Drive không cần thiết. Có nó → chọn đúng layer cần chạy, tiết kiệm thời gian khi debug hoặc chạy lại từng phần.

#### SUBTASK — Wire --layer=all chạy tuần tự Bronze→Silver→Gold trong 1 lệnh

**Labels:** backend, phase-3, sprint-3 | **Priority:** Medium

**Goal:** Chạy full pipeline end-to-end bằng 1 lệnh.
**Input Spec:** `--layer all` (subtask trước đã wire từng layer riêng).
**Output/Deliverable:** `main.py` chạy tuần tự extract → transform_silver → transform_gold khi `--layer all`.
**Tech Stack:** Python.
**File(s):** `main.py`
**Technical Steps:** `if args.layer == "all": extract.run(...); transform_silver.run(...); transform_gold.run(...)`.
**Acceptance Criteria:** `uv run main.py --layer all --run-date <date>` chạy đủ Bronze→Silver→Gold không lỗi, khớp AC Epic 3.
**💡 Vì sao cần:** Không làm → phải gõ 3 lệnh riêng (bronze, silver, gold) mỗi lần muốn chạy full pipeline, dễ quên 1 bước hoặc chạy sai thứ tự. Có nó → 1 lệnh duy nhất chạy hết từ Google Drive tới Gold, đúng thứ tự, không cần nhớ 3 lệnh rời.

---

# EPIC 4 — Phase 4: Power BI Dashboard & Reporting Layer  _[giữ nguyên]_

## EPIC — Phase 4: Power BI Dashboard & Reporting Layer

**Labels:** dashboard, phase-4, sprint-3 | **Priority:** Medium

# 🚀 EPIC: Power BI Dashboard & Reporting Layer

### 🎯 Objective & End-to-End Scope

* **Data Flow Scope:** `data/gold/<run_date>/*.parquet` (Star Schema) ➔ Power BI Data Model + DAX measures ➔ Dashboard pages (.pbix) cho Marketer/DA/Admin.
* **Epic AC:**

    * \[ \] Power BI kết nối thành công vào `data/gold/<run_date>/*.parquet`, quan hệ Dim-Fact đúng
    * \[ \] Tối thiểu 2/4 trang dashboard hoàn chỉnh: **Sales vs Target** + **Promotion & Distributor Performance** (BRD checklist ưu tiên 2 trang này)
    * \[ \] 2 trang còn lại (Executive Overview, Data Ops Monitoring) là stretch, không bắt buộc MVP
    
* **Epic DOD:** Mở file `.pbix`, số liệu hiển thị đúng khớp `mart_sales_vs_target`/`fact_distributor_orders`/`ingest_log` tương ứng.

---

### 🔗 Dependencies, RACI & Timeline

* **Blocked By:** Epic 3 (Gold Star Schema)
* **Blocks:** None
* **Target Phase / Sprint:** Phase 4 / Sprint 3
* **Start Date / Due Date:** 2026-08-24 / 2026-08-25
* **Product Owner (sign-off):** Linh Nguyen
* **Required Reviewer(s):** Linh Nguyen (self-review, solo capstone)
* **On-call khi go-live:** Linh Nguyen
* **Confluence spec/decision log:** _(tạo page "Epic 4 — Power BI Dashboard Spec & Decision Log" trên Confluence space mới, điền link vào đây sau khi tạo)_

---

### ⚠️ Risk Register

N/A — \[NON-PROD\]: Power BI Desktop local, không chạm hạ tầng production/credential ngoài.

---

### 🔒 Non-Functional Requirements

N/A (Production Impact: Không)

---

### 📝 Assumptions Made

* \[2026-07-26\] Checklist nghiệm thu BRD chỉ yêu cầu tối thiểu 2/4 trang dashboard, ưu tiên trang phục vụ đúng actor Marketer/DA nêu trong đề bài (Sales vs Target, Promotion & Distributor Performance) → 2 trang này là bắt buộc (Priority High), Executive Overview + Data Ops Monitoring là stretch (Priority Medium) — Người duyệt: PO
* \[2026-07-26\] Sprint 3/Epic 4 dùng chung due date với Epic 3 (phase-3, Gold) do 2 Epic cùng nằm Sprint 3 (xem mục 📝 Assumptions Made ở Epic 3 phía trên về placeholder "Bế giảng") — Người duyệt: PO

---

### STORY — P4.1 Power BI Data Source Connection Setup

**Labels:** dashboard, infra, phase-4, sprint-3 | **Priority:** High

# 📋 USER STORY: Power BI Data Source Connection Setup

### 👤 User Story

* **As a:** Data Analyst/Marketer
* **I want to:** Power BI kết nối thẳng vào `data/gold/<run_date>/*.parquet`
* **So that:** build dashboard trực tiếp trên Gold layer, không cần ETL trung gian

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** `data/gold/<run_date>/*.parquet` (dim\__, fact\__, mart_sales_vs_target)
* **⚙️ Processing:** Power BI Desktop "Get Data" → Folder/Parquet connector, load toàn bộ bảng, khai báo relationships khớp Star Schema
* **📤 Output:** Power BI Data Model có đủ bảng, quan hệ Dim-Fact đúng, parameter `run_date` để đổi ngày dữ liệu

---

### ✅ Definition of Ready

- [x] Spec rõ (BRD §3.1 kiến trúc, §4 Dashboard)
- [x] Không cần Design (kết nối kỹ thuật)
- [x] Blocked By Epic 3 (P3.8, Gold layer đầy đủ)
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** Epic 3 (P3.8) / P4.2, P4.3, P4.4, P4.5
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 3 / 2026-08-24

---

### 🏷️ Metadata

* **Labels:** sprint-3, phase-4, dashboard, infra
* **Priority:** High
* **Story Points:** 3

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given `data/gold/<run_date>/` có đủ 12 file parquet, When Power BI Get Data từ folder, Then toàn bộ bảng load vào Data Model không lỗi
* \[ \] **Scenario 2 (Error/Exception):** Given đổi `run_date` param sang ngày khác chưa có Gold data, When refresh, Then Power BI báo lỗi rõ ràng "path not found" thay vì hiển thị dữ liệu cũ gây hiểu lầm
* \[ \] **Scenario 3 (Security):** Given Gold Parquet đã drop cột PII từ kiến trúc (P3.1, không phải rà soát tay), When Power BI load `dim_customers`/`dim_employees`/`dim_distributors`, Then Fields pane không có `phone/address/tax_code/date_of_birth` sẵn — không cần thao tác ẩn field nào thêm

---

### 🔒 Non-Functional Requirements

**Security:** PII (`phone, address, tax_code, date_of_birth`) đã bị drop từ lúc build Gold Dim tables (P3.1) — kiểm soát bằng kiến trúc, không phải quy trình rà soát tay trước khi share `.pbix`. File `.pbix` chỉ kết nối vào Gold Parquet vốn đã sạch PII, nên kể cả ai đọc thẳng file Parquet trên đĩa (không qua Power BI) cũng không thấy PII. Subtask cuối trong story này chỉ còn xác nhận (defense-in-depth), không phải điểm kiểm soát chính. (Production Impact vẫn "Không" — rủi ro rò rỉ dữ liệu khi chia sẻ ngoài, không phải rủi ro production traffic.)

---

### 📊 Observability Requirements

N/A

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

Xây dựng trang dashboard cụ thể (P4.2-P4.5)

### 🛠️ Technical Notes

Power BI Parquet connector (Get Data > Parquet) hoặc DuckDB connector nếu Parquet connector native chưa ổn định trên bản Power BI Desktop đang dùng.

#### SUBTASK — Connect Power BI to data/gold/<run_date>/ folder, load dim/fact tables

**Labels:** dashboard, infra, phase-4, sprint-3 | **Priority:** Medium

**Goal:** Kết nối Power BI Desktop vào toàn bộ bảng Gold.
**Input Spec:** `data/gold/<run_date>/*.parquet` (12 file: 7 dim + 4 fact + 1 mart).
**Output/Deliverable:** Power BI Data Model có đủ 12 bảng.
**Tech Stack:** Power BI Desktop, Get Data > Folder/Parquet.
**File(s):** `VDAP_Dashboard.pbix`
**Technical Steps:** Get Data → Folder → trỏ `data/gold/<run_date>/` → Combine & Load từng file parquet thành bảng riêng.
**Acceptance Criteria:** Power BI Fields pane hiện đủ 12 bảng đúng tên.
**💡 Vì sao cần:** Không làm → dữ liệu Gold nằm sẵn ở dạng file nhưng Power BI không tự biết để đọc — không có bước này thì không có gì để làm dashboard cả. Có nó → toàn bộ 12 bảng có mặt trong Power BI, sẵn sàng để dựng báo cáo.

#### SUBTASK — Build relationships in model matching star schema

**Labels:** dashboard, infra, phase-4, sprint-3 | **Priority:** Medium

**Goal:** Khai báo quan hệ Dim-Fact đúng theo Star Schema.
**Input Spec:** 12 bảng đã load (subtask trước), surrogate key từ mỗi Dim.
**Output/Deliverable:** Model view có đủ relationship lines Dim→Fact.
**Tech Stack:** Power BI Model view.
**File(s):** `VDAP_Dashboard.pbix`
**Technical Steps:** Kéo-thả tạo relationship theo key (`customer_key`, `product_key`, `employee_key`, `date_key`, `distributor_key`, `territory_key`, `promotion_key`) từ Dim sang Fact tương ứng.
**Acceptance Criteria:** Model view không có cảnh báo "no relationship"; measure test trên 1 visual cross-filter đúng giữa Dim và Fact.
**💡 Vì sao cần:** Không làm → 12 bảng nằm rời rạc trong Power BI, không "biết" bảng nào liên quan bảng nào — chọn lọc theo vùng ở 1 visual không tự động lọc theo visual khác. Có nó → chọn 1 khách hàng/vùng trên 1 biểu đồ, mọi biểu đồ liên quan tự động cập nhật theo (đúng bản chất Star Schema).

#### SUBTASK — Parameterize run_date so dashboard refreshes to latest gold folder

**Labels:** dashboard, infra, phase-4, sprint-3 | **Priority:** Medium

**Goal:** Cho phép đổi ngày dữ liệu mà không sửa query thủ công.
**Input Spec:** Đường dẫn `data/gold/<run_date>/` hiện đang hardcode trong query (subtask 1).
**Output/Deliverable:** Power Query Parameter `RunDate`, query dùng parameter thay vì hardcode path.
**Tech Stack:** Power Query (M language) Parameters.
**File(s):** `VDAP_Dashboard.pbix`
**Technical Steps:** Tạo Parameter `RunDate` (Text) → sửa M query nối path bằng `"data/gold/" & RunDate & "/"`.
**Acceptance Criteria:** Đổi giá trị Parameter `RunDate` → Refresh → dashboard load đúng data ngày mới.
**💡 Vì sao cần:** Không làm → mỗi lần có dữ liệu ngày mới, phải mở Power Query sửa tay đường dẫn thư mục, dễ gõ sai/quên sửa. Có nó → chỉ cần đổi 1 tham số rồi bấm Refresh, không phải sửa code/query mỗi lần đổi ngày.

#### SUBTASK — Xác nhận PII đã bị drop ở Gold (lớp phòng vệ thứ 2, không phải kiểm soát chính)  _[SỬA — kiểm soát chính đã dời sang Gold P3.1]_

**Labels:** dashboard, infra, pii, compliance-nd13, phase-4, sprint-3 | **Priority:** Medium

**Goal:** Kiểm soát PII CHÍNH giờ nằm ở kiến trúc (P3.1 drop cột PII trước khi ghi Gold Parquet) — không đợi tới lúc share `.pbix` mới rà soát bằng tay, vì Gold Parquet có thể bị đọc trực tiếp bất kỳ lúc nào không qua Power BI. Subtask này chỉ còn là bước xác nhận cuối (defense-in-depth): đảm bảo Power BI model không vô tình tự thêm lại PII qua 1 nguồn dữ liệu khác, và Fields pane sạch trước khi nộp bài/đưa vào portfolio.
**Input Spec:** `dim_customers`, `dim_employees`, `dim_distributors` đã load vào Power BI (subtask 1) — đáng lẽ đã KHÔNG còn cột PII vì Gold Parquet đã drop từ P3.1.
**Output/Deliverable:** Xác nhận Fields pane không có cột PII nào; nếu vẫn thấy PII xuất hiện (nghĩa là P3.1 có bug hoặc ai đó nối thêm nguồn dữ liệu khác vào model), dừng lại và fix ở Gold trước, không tự ý ẩn field ở tầng Power BI để che tạm.
**Tech Stack:** Power BI Model view (Fields pane review).
**File(s):** `VDAP_Dashboard.pbix`
**Technical Steps:**
1. Duyệt Fields pane của `dim_customers`/`dim_employees`/`dim_distributors`, đối chiếu KHÔNG còn `phone/address/tax_code/date_of_birth`
2. Nếu vẫn thấy PII: quay lại P3.1 kiểm tra `PII_COLUMNS_TO_DROP` có đủ chưa, hoặc kiểm tra model có nối thêm query/nguồn nào khác ngoài `data/gold/<run_date>/`
**Acceptance Criteria:** Fields pane của cả 3 Dim không có cột PII nào — vì Gold Parquet gốc đã không có, không phải vì bị ẩn thủ công ở Power BI.
**💡 Vì sao cần:** Không làm → không có bước xác nhận cuối, lỡ bước drop PII ở Gold (P3.1) có bug thì không ai phát hiện cho tới khi file `.pbix` đã lỡ share ra ngoài. Có nó → kiểm tra chéo lần cuối trước khi coi dashboard là hoàn thiện, bắt được bug sớm nếu kiểm soát chính ở Gold bị lọt.

---

### STORY — P4.2 Dashboard Page: Sales vs Target (US-04)

**Labels:** dashboard, phase-4, sprint-3 | **Priority:** High

# 📋 USER STORY: Dashboard Page — Sales vs Target

### 👤 User Story

* **As a:** Marketer
* **I want to:** xem báo cáo Doanh số thực tế vs Target theo vùng & tháng trên Power BI
* **So that:** biết vùng nào đang lệch chỉ tiêu để ra quyết định phân bổ

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** `mart_sales_vs_target` (Gold, từ P3.5), đã load vào Power BI (P4.1)
* **⚙️ Processing:** Build visual matrix/bar chart region×month; DAX measures Achievement rate, Variance
* **📤 Output:** Trang "2. Sales vs Target" trong file `.pbix`, có slicer region/month

---

### ✅ Definition of Ready

- [x] Spec rõ (BRD §4.1 trang 2, US-04)
- [x] Design: layout đơn giản matrix + slicer, không cần wireframe riêng
- [x] Blocked By P4.1
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** P4.1 / None
* **Design Link:** N/A (BRD §4.1 mô tả nội dung trang)
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 3 / 2026-08-25

---

### 🏷️ Metadata

* **Labels:** sprint-3, phase-4, dashboard
* **Priority:** High
* **Story Points:** 3

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given `mart_sales_vs_target` có dữ liệu 1 vùng/tháng, When xem trang Sales vs Target, Then số `actual_revenue`/`target_revenue` khớp đúng dữ liệu Gold
* \[ \] **Scenario 2 (Error/Exception):** Given 1 vùng có `target_revenue=0`/NULL, When xem Achievement rate, Then hiển thị "N/A" hoặc blank thay vì lỗi `#DIV/0!` trên visual

---

### 🔒 Non-Functional Requirements

N/A

---

### 📊 Observability Requirements

N/A

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

Trang Promotion & Distributor (P4.3)

### 🛠️ Technical Notes

DAX: `Achievement Rate = DIVIDE([Actual Revenue],[Target Revenue])`; `Variance = [Actual Revenue] - [Target Revenue]`.

#### SUBTASK — Matrix/bar visual: actual vs target revenue by region+month

**Labels:** dashboard, phase-4, sprint-3 | **Priority:** Medium

**Goal:** Visual chính của trang Sales vs Target.
**Input Spec:** `mart_sales_vs_target` đã load (P4.1).
**Output/Deliverable:** Matrix hoặc Clustered Bar Chart: rows=region, columns=month, values=actual_revenue/target_revenue.
**Tech Stack:** Power BI visuals.
**File(s):** `VDAP_Dashboard.pbix`
**Technical Steps:** Thêm visual Matrix, kéo `region` vào Rows, `month` vào Columns, `actual_revenue`+`target_revenue` vào Values.
**Acceptance Criteria:** Visual hiển thị đúng số khớp `mart_sales_vs_target` parquet.
**💡 Vì sao cần:** Không làm → có dữ liệu sạch sẵn trong `mart_sales_vs_target` nhưng không ai nhìn thấy được nếu không có biểu đồ. Có nó → Marketer nhìn 1 phát là thấy ngay vùng nào/tháng nào đạt hay không đạt doanh số, đúng yêu cầu chính của US-04.

#### SUBTASK — Achievement rate + Variance DAX measures

**Labels:** dashboard, phase-4, sprint-3 | **Priority:** Medium

**Goal:** Tạo 2 measure chính cho trang.
**Input Spec:** `mart_sales_vs_target[actual_revenue]`, `[target_revenue]`.
**Output/Deliverable:** DAX measures `Achievement Rate`, `Variance`.
**Tech Stack:** DAX.
**File(s):** `VDAP_Dashboard.pbix`
**Technical Steps:** `Achievement Rate = DIVIDE(SUM(mart_sales_vs_target[actual_revenue]), SUM(mart_sales_vs_target[target_revenue]))`; `Variance = SUM([actual_revenue]) - SUM([target_revenue])`.
**Acceptance Criteria:** Measure không lỗi `#DIV/0!` khi target=0 (dùng DIVIDE có guard).
**💡 Vì sao cần:** Không làm → chỉ có 2 con số thô (thực tế, target) mà không có % đạt chỉ tiêu, người xem phải tự tính nhẩm mỗi lần muốn biết "đạt bao nhiêu %". Có nó → có sẵn số % đạt chỉ tiêu và số chênh lệch, không lỗi khi 1 vùng chưa set target.

#### SUBTASK — Region/month slicers

**Labels:** dashboard, phase-4, sprint-3 | **Priority:** Medium

**Goal:** Cho phép Marketer lọc theo vùng/tháng.
**Input Spec:** Visual matrix đã có (subtask 1).
**Output/Deliverable:** 2 Slicer visual: region, month.
**Tech Stack:** Power BI Slicer visual.
**File(s):** `VDAP_Dashboard.pbix`
**Technical Steps:** Thêm Slicer visual cho `region`, 1 cho `month`, đặt trên đầu trang.
**Acceptance Criteria:** Chọn 1 vùng trên Slicer → Matrix/measure cập nhật đúng theo filter.
**💡 Vì sao cần:** Không làm → Marketer muốn xem riêng 1 vùng/1 tháng cụ thể phải nhìn cả bảng to rồi tự dò, mất công. Có nó → click chọn vùng/tháng muốn xem, toàn bộ trang tự lọc theo, xem đúng cái cần ngay.

---

### STORY — P4.3 Dashboard Page: Promotion & Distributor Performance (US-05)

**Labels:** dashboard, phase-4, sprint-3 | **Priority:** High

# 📋 USER STORY: Dashboard Page — Promotion & Distributor Performance

### 👤 User Story

* **As a:** Marketer
* **I want to:** biết chương trình khuyến mãi nào tăng doanh số rõ rệt nhất, và hiệu suất giao hàng NPP
* **So that:** đề xuất tiếp tục/dừng chương trình khuyến mãi, đánh giá NPP

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** `fact_sales` × `dim_promotion` (join theo `applicable_products` + khoảng `start_date`-`end_date`), `fact_distributor_orders` (Gold, từ P3.4)
* **⚙️ Processing:** DAX measures Promotion Uplift (`AVG(revenue trong kỳ KM) - AVG(revenue trước kỳ KM)`), Promotion ROI, Fill Rate, On-time Delivery %
* **📤 Output:** Trang "3. Promotion & Distributor Performance" trong `.pbix`

---

### ✅ Definition of Ready

- [x] Spec rõ (BRD §4.1 trang 3, §4.2 công thức KPI, US-05)
- [x] Không cần Design riêng
- [x] Blocked By P4.1
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** P4.1 / None
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 3 / 2026-08-25

---

### 🏷️ Metadata

* **Labels:** sprint-3, phase-4, dashboard
* **Priority:** High
* **Story Points:** 3

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given `dim_promotion` có 1 chương trình với `start_date`-`end_date` xác định, When tính Promotion Uplift, Then so sánh đúng doanh số trong kỳ vs trước kỳ cùng sản phẩm/vùng
* \[ \] **Scenario 2 (Error/Exception):** Given `applicable_products` chứa nhiều mã sản phẩm phân cách dấu phẩy, When join `fact_sales`, Then dùng logic tách chuỗi/CONTAINSSTRING trong DAX để match đúng, không bỏ sót sản phẩm nào trong danh sách

---

### 🔒 Non-Functional Requirements

N/A

---

### 📊 Observability Requirements

N/A

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

Trang Sales vs Target (P4.2)

### 🛠️ Technical Notes

DAX: `Fill Rate = AVERAGE(fact_distributor_orders[fill_rate_pct])`; `On-time Delivery % = DIVIDE(COUNTROWS(FILTER(fact_distributor_orders, [ontime_delivery]=TRUE)), COUNTROWS(fact_distributor_orders))`.

#### SUBTASK — Promotion Uplift/ROI DAX measures + visual

**Labels:** dashboard, phase-4, sprint-3 | **Priority:** Medium

**Goal:** Đo hiệu quả khuyến mãi.
**Input Spec:** `fact_sales`, `dim_promotion` (đã load, P4.1).
**Output/Deliverable:** DAX measures `Promotion Uplift`, `Promotion ROI` + visual bar chart theo `promotion_name`.
**Tech Stack:** DAX.
**File(s):** `VDAP_Dashboard.pbix`
**Technical Steps:** `Promotion Uplift = CALCULATE([Actual Revenue], DATESBETWEEN(...)) - CALCULATE([Actual Revenue], trước kỳ)`; `Promotion ROI = DIVIDE([Promotion Uplift] - SUM(dim_promotion[actual_cost_vnd]), SUM(dim_promotion[actual_cost_vnd]))`.
**Acceptance Criteria:** Visual hiển thị Uplift/ROI theo từng chương trình khuyến mãi, số khớp tính tay trên 1 chương trình mẫu.
**💡 Vì sao cần:** Không làm → Marketer không biết chương trình khuyến mãi nào thực sự làm tăng doanh số, có thể tiếp tục chi tiền cho chương trình không hiệu quả. Có nó → thấy rõ chương trình nào đáng tiếp tục, chương trình nào nên dừng, dựa trên số liệu chứ không phải cảm tính.

#### SUBTASK — Fill Rate + On-time Delivery % visuals

**Labels:** dashboard, phase-4, sprint-3 | **Priority:** Medium

**Goal:** Đo hiệu suất giao hàng NPP.
**Input Spec:** `fact_distributor_orders` (đã load, P4.1).
**Output/Deliverable:** DAX measures `Fill Rate`, `On-time Delivery %` + visual gauge/card theo `distributor_name`.
**Tech Stack:** DAX.
**File(s):** `VDAP_Dashboard.pbix`
**Technical Steps:** `Fill Rate = AVERAGE(fact_distributor_orders[fill_rate_pct])`; `On-time Delivery % = DIVIDE(CALCULATE(COUNTROWS(fact_distributor_orders), fact_distributor_orders[ontime_delivery]=TRUE), COUNTROWS(fact_distributor_orders))`.
**Acceptance Criteria:** Visual hiển thị đúng theo từng NPP, khớp tính tay trên dữ liệu mẫu.
**💡 Vì sao cần:** Không làm → không đánh giá được nhà phân phối nào giao hàng đúng hạn/đủ số lượng, khó có căn cứ để làm việc/đàm phán với NPP kém hiệu quả. Có nó → thấy rõ NPP nào đang làm tốt, NPP nào cần cải thiện.

#### SUBTASK — Channel/region filters

**Labels:** dashboard, phase-4, sprint-3 | **Priority:** Medium

**Goal:** Cho phép lọc theo kênh/vùng trên trang Promotion & Distributor.
**Input Spec:** Visuals đã có (2 subtask trước).
**Output/Deliverable:** Slicer `channel`, `region` áp dụng cho cả trang.
**Tech Stack:** Power BI Slicer.
**File(s):** `VDAP_Dashboard.pbix`
**Technical Steps:** Thêm Slicer `channel`, `region`, đặt đầu trang, verify sync filter đúng cả 2 visual (promotion + distributor).
**Acceptance Criteria:** Chọn 1 kênh → cả 2 visual (Promotion Uplift, Fill Rate) cùng cập nhật.
**💡 Vì sao cần:** Không làm → muốn xem riêng 1 kênh bán hàng/1 vùng phải nhìn hết cả trang rồi tự lọc bằng mắt. Có nó → chọn kênh/vùng, cả 2 visual (khuyến mãi + NPP) cùng lọc theo, xem đúng phạm vi cần trong 1 lần click.

---

### STORY — P4.4 Dashboard Page: Executive Overview [Stretch]

**Labels:** dashboard, phase-4, sprint-3 | **Priority:** Medium

# 📋 USER STORY: Dashboard Page — Executive Overview

### 👤 User Story

* **As a:** Marketer/Ban giám đốc
* **I want to:** xem tổng quan doanh thu, tăng trưởng MoM/YoY, top 5 vùng/kênh
* **So that:** nắm bức tranh tổng thể kinh doanh nhanh chóng

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** `fact_sales`, `dim_date` (Gold)
* **⚙️ Processing:** DAX measures Revenue, Growth MoM/YoY; Top N visual theo region/channel
* **📤 Output:** Trang "1. Executive Overview" trong `.pbix`

---

### ✅ Definition of Ready

- [x] Spec rõ (BRD §4.1 trang 1, §4.2 KPI)
- [x] Không cần Design riêng
- [x] Blocked By P4.1
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** P4.1 / None
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 3 / 2026-08-25

---

### 🏷️ Metadata

* **Labels:** sprint-3, phase-4, dashboard
* **Priority:** Medium (stretch, ngoài MVP 2/4 trang bắt buộc)
* **Story Points:** 2

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given `fact_sales` nhiều tháng, When xem Growth MoM, Then số đúng công thức `(revenue_kỳ_này - revenue_kỳ_trước) / revenue_kỳ_trước`
* \[ \] **Scenario 2 (Error/Exception):** Given tháng đầu tiên không có dữ liệu tháng trước để so sánh, When tính Growth MoM, Then hiển thị blank/N/A thay vì lỗi

---

### 🔒 Non-Functional Requirements

N/A

---

### 📊 Observability Requirements

N/A

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

Không bắt buộc cho MVP nghiệm thu (xem mục 📝 Assumptions Made ở Epic 4 phía trên); có thể để dở nếu hết thời gian.

### 🛠️ Technical Notes

DAX Growth MoM dùng `DATEADD` hoặc `PARALLELPERIOD` trên `dim_date`.

#### SUBTASK — Total revenue + MoM/YoY growth measures

**Labels:** dashboard, phase-4, sprint-3 | **Priority:** Medium

**Goal:** KPI tổng quan doanh thu.
**Input Spec:** `fact_sales`, `dim_date` (đã load, P4.1).
**Output/Deliverable:** DAX measures `Total Revenue`, `Growth MoM`, `Growth YoY`.
**Tech Stack:** DAX, PARALLELPERIOD/DATEADD.
**File(s):** `VDAP_Dashboard.pbix`
**Technical Steps:** `Total Revenue = SUM(fact_sales[net_amount])`; `Growth MoM = DIVIDE([Total Revenue] - CALCULATE([Total Revenue], DATEADD(dim_date[date],-1,MONTH)), CALCULATE([Total Revenue], DATEADD(dim_date[date],-1,MONTH)))`.
**Acceptance Criteria:** Card visual hiển thị Total Revenue + Growth % không lỗi.
**💡 Vì sao cần:** Không làm → Ban giám đốc muốn biết "tháng này tăng/giảm bao nhiêu % so với tháng trước, năm trước" phải tự tính tay từ số liệu thô. Có nó → mở dashboard là thấy ngay tổng doanh thu và xu hướng tăng/giảm, không cần tính toán gì thêm.

#### SUBTASK — Top 5 region/channel visual

**Labels:** dashboard, phase-4, sprint-3 | **Priority:** Medium

**Goal:** Visual xếp hạng vùng/kênh dẫn đầu doanh thu.
**Input Spec:** `Total Revenue` measure (subtask trước).
**Output/Deliverable:** Bar chart Top 5 region + Top 5 channel theo doanh thu.
**Tech Stack:** Power BI visual, Top N filter.
**File(s):** `VDAP_Dashboard.pbix`
**Technical Steps:** Thêm Bar chart, filter Top N=5 theo `Total Revenue` trên `region`; tương tự cho `channel`.
**Acceptance Criteria:** Chỉ hiển thị đúng 5 vùng/kênh cao nhất, sắp xếp giảm dần.
**💡 Vì sao cần:** Không làm → nhìn bảng đầy đủ tất cả vùng/kênh khó nhận ra ngay đâu là nơi đóng góp doanh thu lớn nhất. Có nó → thấy ngay top 5 vùng/kênh dẫn đầu trong nháy mắt, phục vụ ra quyết định nhanh của Ban giám đốc.

---

### STORY — P4.5 Dashboard Page: Data Ops Monitoring [Stretch]

**Labels:** dashboard, devops, phase-4, sprint-3 | **Priority:** Medium

# 📋 USER STORY: Dashboard Page — Data Ops Monitoring

### 👤 User Story

* **As a:** Admin
* **I want to:** xem trạng thái từng batch chạy pipeline (`ingest_log`)
* **So that:** biết batch hôm qua có lỗi không, đọc thiếu file nào không, mà không cần mở terminal

---

### 🔄 End-to-End Data Flow Definition

* **📥 Input:** `data/bronze/<run_date>/ingest_log.parquet` (mọi `run_date` đã chạy, từ Epic 1 P1.5)
* **⚙️ Processing:** Load nhiều `ingest_log.parquet` qua các ngày (union/append theo folder pattern); DAX Pipeline Success Rate
* **📤 Output:** Trang "4. Data Ops Monitoring" trong `.pbix`

---

### ✅ Definition of Ready

- [x] Spec rõ (BRD §4.1 trang 4, §4.2 KPI Pipeline Success Rate)
- [x] Không cần Design riêng
- [x] Blocked By P4.1, Epic 1 (P1.5 ingest_log có sẵn)
- [x] Story Points đã ước lượng

---

### ⚙️ Context, Dependencies & Timeline

* **Blocked By / Blocks:** P4.1, Epic 1 (P1.5) / None
* **Design Link:** N/A
* **Production Impact:** Không
* **Target Sprint / Due Date:** Sprint 3 / 2026-08-25

---

### 🏷️ Metadata

* **Labels:** sprint-3, phase-4, dashboard, devops
* **Priority:** Medium (stretch, ngoài MVP 2/4 trang bắt buộc)
* **Story Points:** 2

---

### ✅ Acceptance Criteria

* \[ \] **Scenario 1 (Happy path):** Given nhiều `ingest_log.parquet` qua các ngày, When xem trang Data Ops, Then bảng hiển thị đúng `batch_id, source_file, rows_loaded, status, duration_sec` từng batch
* \[ \] **Scenario 2 (Error/Exception):** Given 1 batch có dòng `status='failed'`, When xem Pipeline Success Rate, Then tỷ lệ tính đúng loại trừ dòng failed, và dòng failed nổi bật (conditional formatting) để Admin dễ nhận diện

---

### 🔒 Non-Functional Requirements

N/A

---

### 📊 Observability Requirements

Đây chính là trang observability cho Admin — bản thân story này implement quan sát vận hành, không có observability riêng ở tầng khác.

---

### 🔁 Rollback Plan

N/A

---

### ❌ Out of Scope

Không bắt buộc cho MVP nghiệm thu (xem mục 📝 Assumptions Made ở Epic 4 phía trên); Power BI cần load nhiều folder ngày — nếu phức tạp về kỹ thuật (Power Query combine folder), có thể giới hạn demo bằng 1-2 `run_date` mẫu thay vì full lịch sử.

### 🛠️ Technical Notes

DAX: `Pipeline Success Rate = DIVIDE(COUNTROWS(FILTER(ingest_log,[status]="success")), COUNTROWS(ingest_log))`.

#### SUBTASK — Load ingest_log across run_dates

**Labels:** dashboard, devops, phase-4, sprint-3 | **Priority:** Medium

**Goal:** Gộp `ingest_log.parquet` của nhiều ngày chạy để xem lịch sử.
**Input Spec:** `data/bronze/*/ingest_log.parquet` (nhiều thư mục ngày).
**Output/Deliverable:** 1 bảng `ingest_log_history` gộp trong Power BI.
**Tech Stack:** Power Query "Combine Files" từ folder.
**File(s):** `VDAP_Dashboard.pbix`
**Technical Steps:** Get Data > Folder trỏ `data/bronze/` → filter file `ingest_log.parquet` → Combine & Load.
**Acceptance Criteria:** Bảng gộp có dòng của tất cả các `run_date` đã chạy pipeline.
**💡 Vì sao cần:** Không làm → mỗi `run_date` có 1 file `ingest_log.parquet` riêng, muốn xem lịch sử "hôm qua chạy có lỗi không" phải mở từng file rời rạc. Có nó → gộp lại thành 1 bảng lịch sử, xem toàn bộ các lần chạy trong 1 chỗ.

#### SUBTASK — Pipeline Success Rate + batch status visual

**Labels:** dashboard, devops, phase-4, sprint-3 | **Priority:** Medium

**Goal:** Visual chính trang Data Ops Monitoring.
**Input Spec:** `ingest_log_history` (subtask trước).
**Output/Deliverable:** DAX measure `Pipeline Success Rate` + Table visual liệt kê batch với conditional formatting cho `status=failed`.
**Tech Stack:** DAX, Power BI Table visual.
**File(s):** `VDAP_Dashboard.pbix`
**Technical Steps:** `Pipeline Success Rate = DIVIDE(CALCULATE(COUNTROWS(ingest_log_history), ingest_log_history[status]="success"), COUNTROWS(ingest_log_history))`; Table visual + conditional formatting đỏ cho dòng failed.
**Acceptance Criteria:** Card hiển thị đúng % success; dòng failed nổi bật màu đỏ trong Table.
**💡 Vì sao cần:** Không làm → Admin muốn biết pipeline có ổn định không phải tự mở terminal đọc log/ingest_log từng lần. Có nó → nhìn 1 trang là biết ngay tỷ lệ thành công, và batch nào lỗi tự nổi bật màu đỏ, không cần mở terminal.

---
