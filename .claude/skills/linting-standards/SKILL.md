---
name: linting-standards
description: Python lint/format convention for VDAP — ruff as the chosen tool (lint+format unified, same Astral family as uv). Load before adding lint config, formatting code, or answering "what linter does this project use".
---

## Trạng thái thật (kiểm trước khi tin)
Kiểm `STATUS.md`/`pyproject.toml` trước — tại thời điểm viết skill này, project **chưa có** `pyproject.toml`, chưa cài linter/formatter nào. Convention dưới đây là **quyết định đã chốt để áp dụng khi bootstrap**, không phải mô tả trạng thái đang chạy.

## Tool đã chọn: `ruff`
Lý do (không tự đổi sang black/flake8/isort/pylint khi chưa hỏi):
- Cùng hệ Astral với `uv` đã dùng cho dependency management — nhất quán toolchain, không thêm runtime khác (Rust binary, không cần venv riêng cho linter).
- Gộp lint + format + import-sort trong 1 tool, 1 config — thay thế Black+Flake8+isort+pyupgrade mà không cần 4 dependency riêng.
- Nhanh (Rust), phù hợp chạy trên máy cá nhân/CI nhẹ của 1 người, không cần cache phức tạp.

## Cài đặt (khi bootstrap, chưa tự chạy nếu chưa được yêu cầu)
```bash
uv add --dev ruff
```
Config trong `pyproject.toml`:
```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]  # pyflakes, pycodestyle, isort, pyupgrade
```
`line-length = 100` (không dùng mặc định 88 của Black) vì code Polars method-chaining (`pl.scan_parquet(...).filter(...).with_columns(...)`) thường dài hơn code thường — nới trần lên 100 đủ chứa chain hợp lý mà vẫn giữ E501 bật để bắt dòng thật sự quá dài. Không ignore hẳn E501 — ignore toàn bộ sẽ tắt luôn kiểm tra độ dài cho code không liên quan Polars chain.

## Lệnh dùng hàng ngày
```bash
uv run ruff check .        # lint
uv run ruff check --fix .  # lint + auto-fix an toàn (import thừa, unused var...)
uv run ruff format .       # format
```

## Ranh giới khi Claude tự chạy
- File đang sửa trong task hiện tại: chạy `ruff format` trên đúng file đó là an toàn, không cần hỏi.
- Chạy `ruff check --fix .` hoặc `ruff format .` trên TOÀN REPO (nhiều file chưa commit của người khác/chưa liên quan task): hỏi trước, không tự ý format hàng loạt — có thể lẫn vào diff không liên quan tới PR đang làm.
- Không tự đổi `select`/`ignore` rules trong `pyproject.toml` để né lỗi lint đang gặp — nếu rule đang chặn hợp lý, sửa code; nếu thấy rule vô lý cho project này, đề xuất đổi và hỏi trước khi sửa config.

## Liên kết `git-workflow`
Chạy `ruff check .` sạch trước khi commit — không phải điều kiện cứng skill `git-workflow` liệt kê, nhưng nên coi là bước chuẩn trước `git add` cùng lúc kiểm `credentials.json`/`.env` không bị track. Commit message vẫn theo đúng convention `git-workflow` (`<type>(VDAP-<key>): ...`); lint sạch không đổi format message.
