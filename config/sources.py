# config/sources.py
"""Danh sách nguồn dữ liệu cố định của VDAP (SRC01-SRC10, xem BRD mục 2.2).

Tách riêng khỏi src/extract để logic đọc file (read_csv_sources,
read_excel_sources) không lẫn với danh sách "đọc file nào" — thêm/bớt
nguồn CSV thì sửa list ở đây, không đụng vào hàm đọc.
"""

CSV_SOURCES = [
    "SRC01_sales_transactions.csv",
    "SRC03_customer_master.csv",
    "SRC06_distributor_master.csv",
    "SRC09_return_transactions.csv",
]

EXCEL_SOURCES = [
    "SRC02_sales_target_plan.xlsx",
    "SRC04_product_master.xlsx",
    "SRC05_distributor_orders.xlsx",
    "SRC07_employee_master.xlsx",
    "SRC08_territory_mapping.xlsx",
    "SRC10_promotion_program.xlsx",
]
