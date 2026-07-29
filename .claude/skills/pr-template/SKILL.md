---
name: pr-template
description: PR title/body convention for the VDAP repo — matches git-workflow's Conventional Commits + Jira key format, adds phase acceptance-criteria checklist, idempotency test plan, security checklist. Load before running `gh pr create` or drafting any PR description in this project.
---

Nguồn convention gốc: skill `git-workflow` (branch naming, commit message). PR template dưới đây chỉ mở rộng convention đó sang PR title/body — không tự bịa format khác.

## PR Title
Giống hệt commit convention: `<type>(VDAP-<key>): <imperative summary>`
Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`.
Không có Jira key (chore hiếm) → `chore: <slug>`.
Ví dụ: `feat(VDAP-36): implement download_file() via Drive API`

## PR Body (dùng đúng thứ tự này)

```markdown
## Related Issue
- Fixes VDAP-<key>
- Phase: [phase1_bronze_ingestion.md | phase2_silver_cleansing.md | phase3_gold_production.md | N/A]

## Summary
- [1-3 bullet, tập trung VÌ SAO thay đổi, không liệt kê lại từng dòng diff]

## Changes
- [ ] [bullet ngắn gọn từng thay đổi chính, theo layer nếu áp dụng: Bronze/Silver/Gold/CLI/tests]

## How to Test
1. `uv run pytest test_pipeline.py` — pass 100%
2. `uv run main.py --layer <layer> --run-date <date>` chạy không lỗi
3. **Idempotency**: chạy lại đúng `--run-date` đó 2 lần, số dòng/số file output không đổi
4. Đối chiếu Acceptance Criteria trong file phase tương ứng — tick từng mục đã pass
5. (Silver/Gold) 5 cột metadata lineage vẫn còn nguyên sau transform

## Screenshots
*(Đính kèm hình ảnh/gif nếu có thay đổi dashboard/Power BI — không thì ghi "N/A")*

## Security Checklist
*(bỏ qua nếu PR không đụng credentials/secrets/PII — ghi "N/A")*
- [ ] Không có `credentials.json`/`.env` trong diff (`git status` xác nhận trước khi push)
- [ ] Không hardcode giá trị PII thật (phone/tax_code/địa chỉ) trong code/test fixture
- [ ] Nếu thêm dependency mới: không có lỗ hổng critical/high chưa vá
```

## Quy tắc bổ sung
- Solo project (PO = Linh Nguyen mọi vai trò) — không cần reviewer bên ngoài, nhưng PR body vẫn phải đủ để tự audit lại 6 tháng sau không cần hỏi ai.
- Không tạo PR khi checklist How to Test chưa tick hết — nếu có mục chưa làm được, ghi rõ lý do ngay dưới mục đó thay vì xoá bỏ khỏi checklist.
- Trước khi `gh pr create`, chạy qua skill `security-compliance` nếu PR chạm bất kỳ nguồn PII nào (`customer_master`, `employee_master`, `distributor_master`).
- Không tự `gh pr merge`/`--auto` trừ khi được yêu cầu rõ ràng.
