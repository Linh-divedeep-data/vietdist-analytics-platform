from config.sources import CSV_SOURCES, EXCEL_SOURCES
from src.extract.registry import UNIT_OF_WORK
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


def test_unit_of_work_has_exactly_10_entries():
    assert len(UNIT_OF_WORK) == 10


def test_unit_of_work_keys_match_csv_and_excel_sources():
    assert set(UNIT_OF_WORK.keys()) == set(CSV_SOURCES) | set(EXCEL_SOURCES)


def test_unit_of_work_maps_each_source_file_to_its_own_run_function():
    assert UNIT_OF_WORK["SRC01_sales_transactions.csv"] is src01_sales_transactions.run
    assert UNIT_OF_WORK["SRC02_sales_target_plan.xlsx"] is src02_sales_target_plan.run
    assert UNIT_OF_WORK["SRC03_customer_master.csv"] is src03_customer_master.run
    assert UNIT_OF_WORK["SRC04_product_master.xlsx"] is src04_product_master.run
    assert UNIT_OF_WORK["SRC05_distributor_orders.xlsx"] is src05_distributor_orders.run
    assert UNIT_OF_WORK["SRC06_distributor_master.csv"] is src06_distributor_master.run
    assert UNIT_OF_WORK["SRC07_employee_master.xlsx"] is src07_employee_master.run
    assert UNIT_OF_WORK["SRC08_territory_mapping.xlsx"] is src08_territory_mapping.run
    assert UNIT_OF_WORK["SRC09_return_transactions.csv"] is src09_return_transactions.run
    assert UNIT_OF_WORK["SRC10_promotion_program.xlsx"] is src10_promotion_program.run
