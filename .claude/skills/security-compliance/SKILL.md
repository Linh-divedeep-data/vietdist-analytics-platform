---
name: security-compliance
description: Security & Compliance checklist for the VDAP data platform — secrets handling, PII columns across Bronze/Silver/Gold, Vietnam PDPD (Nghị định 13/2023) applicability, access control on data/ and credentials. Load before handling credentials.json/.env, touching customer/employee/distributor PII fields, sharing Gold/Power BI data externally, or reviewing security of this repo.
---

Role: Security & Compliance reviewer cho VDAP data platform (nhà phân phối FMCG, dữ liệu nội bộ, không xử lý thẻ thanh toán/y tế). Dùng skill này để review hoặc thiết kế kiểm soát bảo mật — không phải để viết architecture doc tổng quát (dùng `architecture-blueprint` cho việc đó).

## Phạm vi rủi ro thực tế của dự án (không suy diễn thêm)
- Không có dữ liệu thẻ thanh toán (PCI-DSS không áp dụng), không có dữ liệu y tế (HIPAA không áp dụng), không phục vụ người dùng EU theo hợp đồng (GDPR không áp dụng trực tiếp).
- Luật áp dụng thực tế: **Nghị định 13/2023/NĐ-CP** (bảo vệ dữ liệu cá nhân tại Việt Nam) — vì hệ thống lưu trữ, xử lý PII của khách hàng/nhân viên/NPP là thể nhân cư trú VN.
- Không viện dẫn GDPR/HIPAA/SOC2/PCI-DSS như checklist mặc định — chỉ nêu khi có cấu phần dữ liệu thật sự thuộc phạm vi đó.

## PII inventory theo nguồn (tra `docs/BRD_Solution_Architecture.md` mục 2.2 nếu cần đối chiếu lại)
| Nguồn | Cột PII | Mức nhạy cảm |
|---|---|---|
| `customer_master` (SRC03) | `customer_name, address, phone, tax_code` | Trung bình — định danh cá nhân/hộ kinh doanh |
| `employee_master` (SRC07) | `full_name, gender, date_of_birth, email, phone` | Trung bình-cao — DOB + liên hệ cá nhân nhân viên |
| `distributor_master` (SRC06) | `contact_person, phone, email, tax_code` | Trung bình |

Các cột này tồn tại nguyên vẹn qua Bronze → Silver → Gold (`dim_customers`, `dim_employees`, `dim_distributors`) — không có bước masking/tokenization nào trong 3 phase hiện tại. Đây là **risk đã biết, chấp nhận có điều kiện** ở quy mô nội bộ/portfolio; PHẢI được nêu lại nếu phạm vi mở rộng ra chia sẻ ngoài công ty.

## Checklist bắt buộc trước khi commit/push (cross-check với skill `git-workflow`)
1. `credentials.json` (Service Account key) và `.env` KHÔNG được track trong Git. Chạy `git status` trước mọi `git add`; nếu 2 file này xuất hiện tracked/staged → dừng, sửa `.gitignore`, không commit.
2. `data/{raw,bronze,silver,gold}/*` KHÔNG được commit — chứa PII thật ở dạng plaintext Parquet/CSV. Chỉ giữ `.gitkeep`.
3. Không `git add -A`/`git add .` mù trong repo này — luôn stage path cụ thể.
4. Không hardcode giá trị PII mẫu (số điện thoại thật, tax_code thật) trong test fixture hay comment code — dùng dữ liệu giả lập rõ ràng (VD `090xxxxxxx`, `TAX-TEST-001`).

## Kiểm soát truy cập & lưu trữ
- `credentials.json` là chìa khóa duy nhất mở toàn bộ Drive nguồn — coi như secret cấp cao nhất. Không log nội dung file này ra console/log, không đính kèm vào issue/PR description.
- Lakehouse hiện chạy local filesystem (`data/`) — không có access control cấp OS ngoài quyền thư mục mặc định. Nếu máy chạy pipeline dùng chung với người khác, khuyến nghị giới hạn quyền đọc thư mục `data/` chỉ cho user vận hành.
- Khi Gold layer được kết nối Power BI/DuckDB để chia sẻ ra ngoài nhóm vận hành (VD: gửi báo cáo cho đối tác ngoài công ty), bắt buộc rà soát: có cột PII nào (`phone`, `address`, `tax_code`, `date_of_birth`) lọt vào report/export không — nếu có, phải loại bỏ hoặc mask trước khi chia sẻ ngoài phạm vi nội bộ.

## Điều kiện leo thang compliance (trigger để đầu tư thêm)
- Chuyển hạ tầng lên cloud (theo ADR-02 trong Solution Architecture Blueprint) → bắt buộc thêm: encryption at rest (KMS/SSE), IAM least-privilege cho bucket/warehouse, audit log truy cập.
- Có yêu cầu chia sẻ dữ liệu cho bên thứ ba/đối tác ngoài VietDist → cần bước masking/anonymization PII trước khi export, và xác nhận cơ sở pháp lý xử lý dữ liệu theo Nghị định 13/2023 (mục đích, sự đồng ý, thời hạn lưu trữ).
- Có yêu cầu retention/xóa dữ liệu theo yêu cầu chủ thể dữ liệu → hiện chưa có cơ chế xóa theo `customer_id`/`employee_id` xuyên suốt Bronze/Silver/Gold, cần thiết kế bổ sung khi phát sinh yêu cầu thật.

## Output khi dùng skill này để review
Trả lời dạng checklist pass/fail theo từng mục trên + liệt kê cụ thể file/dòng vi phạm (nếu có) — không viết lại toàn bộ thành văn bản luận giải dài dòng như `architecture-blueprint`.
