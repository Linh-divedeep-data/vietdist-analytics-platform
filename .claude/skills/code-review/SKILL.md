---
name: code-review
description: Pre-merge review checklist for VDAP — layer-boundary violations, idempotency, data lineage, lazy evaluation, code smell, security/secrets. Report-only, no silent auto-fix. Load before reviewing a diff/PR or before saying code is "ready to merge" in this repo.
---

Vai trò: reviewer, không phải người sửa code. Liệt kê finding, KHÔNG tự sửa trừ khi user xác nhận rõ ràng ("sửa luôn đi"). Nếu chỉ được hỏi "review giúp tôi" → chỉ báo cáo.

## Thứ tự kiểm tra

1. **Security/Secrets/PII** — delegate checklist chi tiết cho skill `security-compliance`. Tối thiểu tự kiểm: `credentials.json`/`.env` không xuất hiện trong diff; không PII thật hardcode trong test fixture.

2. **Layer boundary** (theo `CLAUDE.md` mục Kiến trúc 3 lớp) — vi phạm nghiêm trọng nếu:
   - Bronze có logic cast/dedup/business rule (Bronze chỉ được ép `String` + gắn metadata, không hơn).
   - Silver có `join()` dựng khóa ngoại hoặc tính Data Mart (việc đó thuộc Gold).
   - Gold thiếu `_run_date`/`_batch_id` ở fact table (mất lineage).
   - Bất kỳ lớp nào xóa/ghi đè 5 cột metadata Bronze khi đi qua Silver/Gold.

3. **Idempotency** — flag nếu code ghi file không theo partition `run_date` (`data/<layer>/yyyymmdd/...`), hoặc dùng append-mode thay vì ghi đè full file trong thư mục ngày đó, hoặc tạo tên file có timestamp/UUID trong path (phá idempotency vì mỗi lần chạy ra file mới thay vì ghi đè).

4. **Lazy Evaluation** (Silver/Gold) — flag nếu dùng `pl.read_parquet()` thay vì `pl.scan_parquet()`, hoặc gọi `.collect()` nhiều lần giữa chừng thay vì chỉ ở bước ghi cuối cùng.

5. **Code smell đặc thù dự án:**
   - 10 nguồn SRC01–SRC10 xử lý bằng 10 khối code copy-paste thay vì 1 vòng lặp tham số hóa → flag, đề xuất gộp.
   - Cast số tiền thẳng sang `Float64` không `.str.replace_all(",", "")` trước — sẽ crash với data có dấu phân cách nghìn, bug đã biết trước trong Hint Phase 2.
   - SCD Type 2 (`dim_employees`) thiếu cột bắt buộc (`employee_key, employee_id, name, region, team, valid_from, valid_to, is_current`) hoặc logic `shift()/over()` không sort theo `effective_date` trước khi tính — ra sai lịch sử.
   - Try/except nuốt lỗi im lặng ở bước ingest (nên fail rõ ràng + ghi `status='failed'` vào `ingest_log`, không nuốt exception).

6. **Style** — chỉ flag lệch rõ ràng (tên biến không nhất quán, dead code, import thừa). Convention linter/formatter chính thức xem skill `linting-standards`, không tự áp đặt rule ở đây.

## Output format
Mỗi finding: `file:line — [mức độ: blocker/major/minor] — mô tả ngắn — hệ quả cụ thể nếu không sửa`. Xếp blocker lên đầu. Không review xong rồi tự thêm khen ngợi/generic summary — chỉ liệt kê finding, hoặc nói rõ "không có finding" nếu sạch.
