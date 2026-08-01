# src/extract/registry.py
"""Map source_file -> unit_of_work.run(), dùng cho orchestrator.py.

Nguồn liệt kê theo config/sources.py (CSV_SOURCES + EXCEL_SOURCES) — thêm/bớt
nguồn thì sửa ở đó và thêm module unit_of_work tương ứng, không sửa ở đây.
"""

from src.extract.unit_of_work import (
    src01_sales_transactions,
    src02_sales_target_plan,
    src03_customer_master,
    src04_product_master,
    src05_distributor_orders,
    src06_distributor_master,
    src07_employee_master,
    src08_territory_mapping,
    src09_return_transactions,
    src10_promotion_program,
)

UNIT_OF_WORK = {
    src01_sales_transactions.SOURCE_FILE: src01_sales_transactions.run,
    src02_sales_target_plan.SOURCE_FILE: src02_sales_target_plan.run,
    src03_customer_master.SOURCE_FILE: src03_customer_master.run,
    src04_product_master.SOURCE_FILE: src04_product_master.run,
    src05_distributor_orders.SOURCE_FILE: src05_distributor_orders.run,
    src06_distributor_master.SOURCE_FILE: src06_distributor_master.run,
    src07_employee_master.SOURCE_FILE: src07_employee_master.run,
    src08_territory_mapping.SOURCE_FILE: src08_territory_mapping.run,
    src09_return_transactions.SOURCE_FILE: src09_return_transactions.run,
    src10_promotion_program.SOURCE_FILE: src10_promotion_program.run,
}
