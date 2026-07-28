# CLAUDE.md — VietDist Analytics Platform

Capstone cá nhân (fresher Data Engineer): xây Data Lakehouse Bronze → Silver → Gold cho VietDist, nhà phân phối FMCG. Nguồn sự thật đầy đủ về nghiệp vụ/kiến trúc: [`docs/BRD_Solution_Architecture.md`](docs/BRD_Solution_Architecture.md) và [`docs/Solution_Architecture_Blueprint.md`](docs/Solution_Architecture_Blueprint.md). Chi tiết acceptance criteria từng phase: [`phase1_bronze_ingestion.md`](phase1_bronze_ingestion.md), [`phase2_silver_cleansing.md`](phase2_silver_cleansing.md), [`phase3_gold_production.md`](phase3_gold_production.md).

## Trạng thái repo hiện tại

Xem [`STATUS.md`](STATUS.md) — file này đổi liên tục theo tiến độ code nên tách riêng khỏi CLAUDE.md (file quy ước tĩnh). Cập nhật `STATUS.md` ngay sau khi xong mỗi Phase. Nếu nội dung `STATUS.md` có vẻ không khớp thực tế, tự kiểm bằng `ls`/`git status` trước khi tin.

## Khi bắt đầu 1 task mới

1. Đọc `STATUS.md` để biết đang ở đâu.
2. Đọc acceptance criteria của phase tương ứng trước khi viết code (vd: `phase1_bronze_ingestion.md` cho Bronze) — đó cũng là định nghĩa "Done" của phase, không định nghĩa lại ở CLAUDE.md.
3. Task đụng git/credentials/PII → load skill tương ứng (`git-workflow`, `security-compliance`) trước khi thực thi, không làm tắt.
4. Xong phase → cập nhật `STATUS.md`.

## Bài toán & mục tiêu (tóm tắt — chi tiết xem BRD mục 1)

Dữ liệu Sales/Marketing/Kế toán rải rác Excel/CSV trên Google Drive, không single source of truth, báo cáo dựng tay. Mục tiêu: pipeline tự động Bronze/Silver/Gold, dựng Star Schema duy nhất, phục vụ DuckDB (ad-hoc SQL) + Power BI (dashboard) cho 3 actor: Marketer, Data Analyst, Admin/DE.

## 10 nguồn dữ liệu (SRC01–SRC10)

Toàn bộ nguồn = file CSV/XLSX trên Google Drive, tải qua `gdrive_connector.py` (Service Account, `list_files_in_folder()` / `download_file()`). Chi tiết cột từng nguồn: BRD mục 2.2. Bảng dưới chỉ là tóm tắt nhanh — nếu lệch với BRD mục 2.2, **BRD là nguồn đúng**, sửa lại bảng này theo BRD chứ không ngược lại.

| Mã | File | → Gold |
|---|---|---|
| SRC01 | sales_transactions.csv | `fact_sales` |
| SRC02 | sales_target_plan.xlsx | `fact_targets` |
| SRC03 | customer_master.csv | `dim_customers` |
| SRC04 | product_master.xlsx | `dim_products` |
| SRC05 | distributor_orders.xlsx | `fact_distributor_orders` |
| SRC06 | distributor_master.csv | `dim_distributors` |
| SRC07 | employee_master.xlsx | `dim_employees` (**SCD Type 2**) |
| SRC08 | territory_mapping.xlsx | `dim_territory` / bridge |
| SRC09 | return_transactions.csv | `fact_returns` |
| SRC10 | promotion_program.xlsx | `dim_promotion` |

## Kiến trúc 3 lớp (Medallion, ELT)

| Lớp | Việc làm | Kiểu dữ liệu | Bắt buộc giữ |
|---|---|---|---|
| **Bronze** (`data/bronze/yyyymmdd/`) | Landing thô, gắn metadata | Toàn bộ ép `String` | `_source_file, _source_platform, _run_date, _ingested_at, _batch_id` + `ingest_log.parquet` |
| **Silver** (`data/silver/yyyymmdd/`) | Cast kiểu, dedup, xử lý NULL khóa chính, chuẩn hóa text | `Float/Int` số tiền, `Date/Datetime` ngày, `String` strip/uppercase | Giữ nguyên 5 cột metadata Bronze (lineage — **không được xóa**) |
| **Gold** (`data/gold/yyyymmdd/`) | `join()` dựng Star Schema, SCD Type 2, `group_by/agg` Data Mart | `dim_*`, `fact_*`, `mart_*` | Fact giữ `_run_date, _batch_id` |

Lý do chọn ELT (không phải ETL) và Hybrid infra (không phải full cloud): xem `docs/Solution_Architecture_Blueprint.md` Bước 3–4 — tóm gọn: nguồn không đáng tin cậy schema nên phải giữ raw để audit/replay, volume nhỏ nên không cần cloud DW.

## Nguyên tắc bắt buộc xuyên suốt (không thương lượng khi code)

- **Idempotency**: partition theo `run_date` (`yyyymmdd`), ghi đè trong đúng thư mục ngày — không append vô hạn, không tạo file trùng khi chạy lại.
- **Data Lineage**: 5 cột metadata Bronze phải sống xuyên suốt Silver → Gold.
- **Fail-safe ingestion**: Bronze ép String toàn bộ để không sập vì lỗi kiểu ở nguồn.
- **Lazy Evaluation**: Silver/Gold đọc bằng `pl.scan_parquet()`, chỉ `.collect()` ở bước cuối trước khi ghi.
- **Số tiền dạng string** có dấu phẩy ngăn cách nghìn (`1,000,000`) — phải `.str.replace_all(",", "")` trước khi `.cast(pl.Float64)`.
- **SCD Type 2** (`dim_employees`): cột bắt buộc `employee_key, employee_id, name, region, team, valid_from, valid_to, is_current`.

## CLI (điểm vào duy nhất, khi đã code xong)

```bash
uv run main.py --layer {bronze|silver|gold|all} --run-date YYYY-MM-DD
```

## Testing

`tests/test_pipeline.py` bằng `pytest` — tối thiểu 2 test: (1) logic `mart_sales_vs_target` ra đúng số trên DataFrame giả lập nhỏ, (2) logic SCD Type 2 cập nhật đúng `valid_to`.

## Bảo mật (đọc kỹ trước khi commit — xem skill `security-compliance`)

- `credentials.json`, `.env` không bao giờ commit.
- PII nằm trong `customer_master`, `employee_master`, `distributor_master` (`phone, address, tax_code, date_of_birth`...) — sống nguyên vẹn tới Gold vì không có bước masking trong 3 phase; chỉ chấp nhận được ở phạm vi nội bộ, phải rà lại nếu share ra ngoài.

## Skills sẵn có trong repo (`.claude/skills/`)

- `git-workflow` — branch naming, commit convention, quy tắc an toàn git cho repo này (load trước mọi thao tác git).
- `security-compliance` — checklist secrets/PII/compliance (load trước khi đụng credentials, PII, hoặc share Gold data ra ngoài).
- `architecture-blueprint` — dựng lại/viết mới tài liệu kiến trúc kiểu Senior Solution Architect khi cần.

## Quy ước khác

- Ngôn ngữ giao tiếp/tài liệu dự án: tiếng Việt (theo văn phong các file `phase*.md`, `docs/*.md` hiện có).
- Chưa có PR-gate — solo project, nhưng vẫn giữ Conventional Commits để trace về Jira issue key (xem skill `git-workflow`).


<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:6cd5cc61 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Agent Context Profiles

The managed Beads block is task-tracking guidance, not permission to override repository, user, or orchestrator instructions.

- **Conservative (default)**: Use `bd` for task tracking. Do not run git commits, git pushes, or Dolt remote sync unless explicitly asked. At handoff, report changed files, validation, and suggested next commands.
- **Minimal**: Keep tool instruction files as pointers to `bd prime`; use the same conservative git policy unless active instructions say otherwise.
- **Team-maintainer**: Only when the repository explicitly opts in, agents may close beads, run quality gates, commit, and push as part of session close. A current "do not commit" or "do not push" instruction still wins.

## Session Completion

This protocol applies when ending a Beads implementation workflow. It is subordinate to explicit user, repository, and orchestrator instructions.

1. **File issues for remaining work** - Create beads for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Handle git/sync by active profile**:
   ```bash
   # Conservative/minimal/default: report status and proposed commands; wait for approval.
   git status

   # Team-maintainer opt-in only, unless current instructions forbid it:
   git pull --rebase
   git push
   git status
   ```
5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**
- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->
