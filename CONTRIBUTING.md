# Contributing — VietDist Analytics Platform

Quy ước branch + commit cho repo này. Dự án solo (PO = Nhat Linh cho mọi vai trò) nên không có bước approve PR bắt buộc, nhưng vẫn giữ quy ước này để lịch sử git sạch và trace được về Jira issue.

## Branch naming

| Loại | Format | Ví dụ |
|---|---|---|
| Feature/task thường | `feature/VDAP-<key>-<slug>` | `feature/VDAP-27-wire-logger-main-batch-id` |
| Fix khẩn cấp | `hotfix/VDAP-<key>-<slug>` | `hotfix/VDAP-58-dedup-customer-master` |
| Không có Jira key (hiếm, chore thuần) | `chore/<slug>` | `chore/update-gitignore` |

Nhánh mới tạo từ `develop` (không tạo từ `main` trực tiếp, trừ hotfix khẩn thật sự).

## Commit message (Conventional Commits + Jira key)

Format: `<type>(VDAP-<key>): <tóm tắt ở dạng mệnh lệnh>`

| Type | Dùng khi | Ví dụ |
|---|---|---|
| `feat` | Thêm tính năng/module mới | `feat(VDAP-26): add src/logger.py shared logging module` ✅ commit thật |
| `fix` | Sửa bug | `fix(VDAP-24): fix set -e swallowing exit-code capture in CI` ✅ commit thật |
| `docs` | Chỉ đổi tài liệu | `docs(VDAP-28): add "Getting Started" section to README` ✅ commit thật |
| `chore` | Việc vặt, không phải feature/fix/docs | `chore(VDAP-25): add pip-audit security baseline` ✅ commit thật |
| `ci` | Đổi CI/CD workflow | `ci(VDAP-24): make pytest --collect-only step fail-safe` ✅ commit thật |
| `refactor` | Đổi cấu trúc code, không đổi hành vi | `refactor(VDAP-40): extract retry logic into helper` (minh họa format, chưa có commit loại này trong repo) |
| `test` | Chỉ thêm/sửa test | `test(VDAP-33): add SCD Type 2 valid_to regression test` (minh họa format, chưa có commit loại này trong repo) |

Không có Jira key khớp (hiếm) → bỏ scope: `chore: add .gitkeep to empty dirs`.

## Pull Request

- Base: `develop`. Title/body theo skill `pr-template` (`.claude/skills/pr-template/SKILL.md`).
- Không tự merge/squash khi chưa có xác nhận — xem `finishing-a-development-branch`.

## An toàn

- Không bao giờ commit `credentials.json`, `.env` (đã chặn trong `.gitignore`, nhưng luôn `git status` xác nhận lại trước khi push).
- Không dùng `git add -A`/`git add .` — stage rõ từng path.
- Không `--amend` commit đã push, không `--force` push lên nhánh chia sẻ.

Chi tiết đầy đủ + rationale: xem skill `git-workflow` (`.claude/skills/git-workflow/SKILL.md`).
