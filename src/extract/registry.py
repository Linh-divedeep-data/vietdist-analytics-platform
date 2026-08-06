"""UNIT_OF_WORK: maps each of the 10 sources to its unit_of_work module — filled in Epic Phase 1."""

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

_MODULES = [
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
]

UNIT_OF_WORK = {module.SOURCE_FILE: module.run for module in _MODULES}
