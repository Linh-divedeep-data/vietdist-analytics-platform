# 🌟 VietDist Gold Layer: Star Schema Design (Kimball) — Grain Statements

**Ticket:** VDAP-392 (bd `vietdist-analytics-platform-a9l.9.1`)
**Nguồn dữ liệu xác nhận:** `data/silver/20260804/*.parquet` (đọc trực tiếp bằng Polars, không đoán)

## 🎯 Mục đích

Trước khi code Gold layer (Phase 3), xác định rõ ràng grain (đơn vị 1 dòng)
của từng Fact table dựa trên dữ liệu Silver thật. Grain sai sẽ khiến mọi
phép `JOIN`/`group_by` sau này (đặc biệt `mart_sales_vs_target`) tính sai
mà không biết tại sao.

## fact_sales

- **Nguồn Silver:** `sales_transactions` (`SRC01_sales_transactions.parquet`)
- **Business key:** `(order_id, product_id)`
- **Grain statement:** 1 dòng = 1 sản phẩm (line item) trong 1 đơn hàng bán.
  Một đơn hàng (`order_id`) có thể chứa nhiều sản phẩm khác nhau, mỗi sản
  phẩm là 1 dòng riêng.
- **Xác nhận bằng data:** 119,101 dòng, 50,000 `order_id` distinct
  (trung bình ~2.4 sản phẩm/đơn), cặp `(order_id, product_id)` có 119,101
  giá trị distinct — khớp đúng số dòng, xác nhận unique.

## fact_targets

- **Nguồn Silver:** `sales_target_plan` (`SRC02_sales_target_plan.parquet`)
- **Business key:** `(employee_id, year, month)`
- **Grain statement:** 1 dòng = chỉ tiêu doanh số của 1 nhân viên trong 1
  tháng.
- **Xác nhận bằng data:** 1,332 dòng = 111 `employee_id` distinct × 12
  tháng. Cặp `(employee_id, year, month)` có 1,332 giá trị distinct —
  khớp đúng số dòng, xác nhận unique, không có trùng.
- **⚠️ Quan trọng — xác nhận lại giả định P3.3:** Target được set **theo
  nhân viên (`employee_id`)**, KHÔNG phải theo `region` hay `team`. Dữ
  liệu có cột `region`/`team` nhưng chúng là thuộc tính mô tả đi kèm
  nhân viên đó tại thời điểm lập kế hoạch, không phải business key. Nếu
  P3.3 code `join`/`group_by` theo `region` sẽ SAI vì nhiều nhân viên
  cùng region sẽ bị cộng dồn target sai lệch. Khi build `fact_targets`,
  surrogate key tra cứu Dimension phải đi qua `employee_id`.

## fact_returns

- **Nguồn Silver:** `return_transactions` (`SRC09_return_transactions.parquet`)
- **Business key:** `return_id`
- **Grain statement:** 1 dòng = 1 lần trả hàng (1 sản phẩm bị trả trong 1
  giao dịch trả hàng).
- **Xác nhận bằng data:** 3,665 dòng, 3,665 `return_id` distinct — unique
  1-1, không có trường hợp 1 `return_id` gồm nhiều sản phẩm (multi-line)
  như `fact_sales`.

## fact_distributor_orders

- **Nguồn Silver:** `distributor_orders` (`SRC05_distributor_orders.parquet`)
- **Business key:** `(order_id, product_id)`
- **Grain statement:** 1 dòng = 1 sản phẩm (line item) trong 1 đơn đặt
  hàng của nhà phân phối. Cùng pattern với `fact_sales`: 1 đơn đặt hàng
  NPP có thể gồm nhiều sản phẩm.
- **Xác nhận bằng data:** 35,945 dòng, 8,000 `order_id` distinct (trung
  bình ~4.5 sản phẩm/đơn), cặp `(order_id, product_id)` có 35,945 giá
  trị distinct — khớp đúng số dòng, xác nhận unique.

## Tóm tắt

| Fact | Business key | Grain |
|---|---|---|
| `fact_sales` | `(order_id, product_id)` | 1 dòng = 1 sản phẩm / 1 đơn hàng bán |
| `fact_targets` | `(employee_id, year, month)` | 1 dòng = chỉ tiêu 1 nhân viên / 1 tháng |
| `fact_returns` | `return_id` | 1 dòng = 1 lần trả hàng |
| `fact_distributor_orders` | `(order_id, product_id)` | 1 dòng = 1 sản phẩm / 1 đơn đặt hàng NPP |
