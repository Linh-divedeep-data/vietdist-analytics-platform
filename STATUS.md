# STATUS — Trạng thái triển khai thực tế

> Cập nhật file này ngay sau khi hoàn thành mỗi Phase. Nếu thông tin ở đây có vẻ không khớp thực tế (vd: file đã tồn tại mà vẫn ghi "chưa có"), đừng tin theo — tự kiểm tra bằng `ls`/`git status` trước khi code tiếp, rồi sửa lại file này.

**Cập nhật lần cuối:** 2026-07-27 — trước khi bắt đầu Phase 1.

## Đã có
- `gdrive_connector.py` (template mẫu, hàm `download_file()` còn `TODO: pass` — chưa viết)
- `raw_data/` — dữ liệu mẫu 10 nguồn
- `docs/BRD_Solution_Architecture.md`, `docs/Solution_Architecture_Blueprint.md` — thiết kế
- `.claude/skills/` — `git-workflow`, `security-compliance`, `architecture-blueprint`

## Chưa có
- Git chưa init. Chưa có `.gitignore`, `.env`, `pyproject.toml`.
- `credentials.json` đang nằm trần ở root, **chưa có `.gitignore` che chắn** — không `git init`/`git add` cho tới khi chặn xong (xem skill `git-workflow`, `security-compliance`).
- Chưa có `main.py`, `src/`, `tests/`.
- `uv` chưa init.

## Phase hiện tại
Chưa bắt đầu Phase 1. Xem acceptance criteria: `phase1_bronze_ingestion.md`.

## Lịch sử chuyển phase
| Ngày | Sự kiện |
|---|---|
| 2026-07-27 | Khởi tạo project docs (BRD, Architecture Blueprint, skills). Chưa code. |
