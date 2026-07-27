---
name: test-runner
description: Runs the VDAP pytest suite, reports pass/fail with exact failure detail, never edits code to force a pass without explicit user confirmation. Load whenever asked to "run tests", after changing Bronze/Silver/Gold transform logic, or before claiming a task is done.
---

Vai trò: chạy test, báo cáo kết quả — không phải người quyết định sửa gì. Thấy test fail KHÔNG tự sửa source code hay sửa assertion để ép pass — báo lỗi cụ thể, đề xuất fix, chờ user xác nhận rồi mới sửa (trừ khi user đã nói trước "cứ tự sửa luôn").

## Trước khi chạy
Kiểm `STATUS.md`/`ls tests/` — nếu `tests/test_pipeline.py` chưa tồn tại, nói rõ "chưa có test suite" thay vì báo lỗi chung chung hoặc tự bịa ra là đã chạy.

## Lệnh chạy
```bash
uv run pytest test_pipeline.py -v
```
(hoặc `uv run pytest tests/ -v` nếu test đã chuyển vào thư mục `tests/` theo cấu trúc README đề xuất — kiểm tra path thật trước khi chạy, đừng đoán.)

## Yêu cầu tối thiểu của suite (theo `phase3_gold_production.md`)
- Test logic `mart_sales_vs_target` — DataFrame giả lập nhỏ, số liệu tính đúng.
- Test logic SCD Type 2 — `valid_to` cập nhật đúng khi có bản ghi mới hơn cùng `employee_id`.
Nếu suite thiếu 1 trong 2 test này khi được yêu cầu xác nhận "đủ test chưa" → flag thiếu, không tự coi là đạt.

## Báo cáo kết quả
- Pass 100%: nói ngắn gọn số test pass, không cần liệt kê từng cái.
- Có fail: với mỗi test fail, nêu tên test + dòng assertion sai + giá trị expected vs actual (lấy từ pytest traceback, không diễn giải lại chung chung).
- Không tự động retry/xóa test flaky — nếu nghi test flaky (fail không ổn định), nói rõ nghi ngờ, không âm thầm bỏ qua.

## Ranh giới không được vượt
- Không sửa `test_pipeline.py` để test pass dễ hơn (nới lỏng assertion, xóa test case) khi mục đích là fix bug ở source code.
- Không sửa source code transform logic để pass test mà chưa xác nhận cách sửa đúng nghiệp vụ (VD: SCD2 sai `valid_to` có thể do sort sai `effective_date`, không phải do assertion sai) — nêu chẩn đoán trước, chờ đồng ý.
- Idempotency KHÔNG được cover bởi pytest (đây là hành vi filesystem/integration, không phải unit logic) — nếu được hỏi "test đã đủ chưa", nhắc rõ idempotency phải verify thủ công theo checklist trong skill `pr-template` (chạy lại `--run-date` 2 lần, so số dòng), không tính là đã test qua pytest.
