import ast
from pathlib import Path

from config.sources import CSV_SOURCES, EXCEL_SOURCES


def test_total_source_count_is_10():
    assert len(CSV_SOURCES) + len(EXCEL_SOURCES) == 10


def test_no_duplicate_source_names():
    all_sources = CSV_SOURCES + EXCEL_SOURCES
    assert len(all_sources) == len(set(all_sources))


def test_csv_sources_are_the_expected_4():
    assert set(CSV_SOURCES) == {
        "SRC01_sales_transactions.csv",
        "SRC03_customer_master.csv",
        "SRC06_distributor_master.csv",
        "SRC09_return_transactions.csv",
    }


def test_excel_sources_are_the_expected_6():
    assert set(EXCEL_SOURCES) == {
        "SRC02_sales_target_plan.xlsx",
        "SRC04_product_master.xlsx",
        "SRC05_distributor_orders.xlsx",
        "SRC07_employee_master.xlsx",
        "SRC08_territory_mapping.xlsx",
        "SRC10_promotion_program.xlsx",
    }


def test_sources_module_does_not_import_from_src():
    source = Path("config/sources.py").read_text()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("src"), (
                f"config/sources.py must not import from src/: found 'from {node.module} import ...'"
            )
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("src"), (
                    f"config/sources.py must not import src/: found 'import {alias.name}'"
                )
