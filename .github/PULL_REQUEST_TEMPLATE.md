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
