import ast
from pathlib import Path

from config.sources import (
    CSV_SOURCES,
    DATE_COLUMNS,
    DATE_FORMAT_BY_SOURCE,
    EXCEL_SOURCES,
    KEY_COLUMNS,
    MONEY_QTY_COLUMNS,
    REQUIRED_COLUMNS,
    TEXT_COLUMNS,
)


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


def test_required_columns_has_entry_for_every_source():
    assert set(REQUIRED_COLUMNS.keys()) == set(CSV_SOURCES) | set(EXCEL_SOURCES)


def test_required_columns_values_are_non_empty_lists():
    for source_file, columns in REQUIRED_COLUMNS.items():
        assert isinstance(columns, list)
        assert len(columns) > 0
        assert len(columns) == len(set(columns)), f"{source_file} has duplicate columns"


def test_date_format_by_source_has_entry_for_every_source():
    assert set(DATE_FORMAT_BY_SOURCE.keys()) == set(CSV_SOURCES) | set(EXCEL_SOURCES)


def test_date_format_by_source_values_are_non_empty_strptime_strings():
    for source_file, fmt in DATE_FORMAT_BY_SOURCE.items():
        assert isinstance(fmt, str)
        assert fmt.startswith("%"), f"{source_file}: {fmt!r} doesn't look like a strptime format"


def test_money_qty_columns_has_entry_for_every_source():
    assert set(MONEY_QTY_COLUMNS.keys()) == set(CSV_SOURCES) | set(EXCEL_SOURCES)


def test_date_columns_has_entry_for_every_source():
    assert set(DATE_COLUMNS.keys()) == set(CSV_SOURCES) | set(EXCEL_SOURCES)


def test_text_columns_has_entry_for_every_source():
    assert set(TEXT_COLUMNS.keys()) == set(CSV_SOURCES) | set(EXCEL_SOURCES)


def test_key_columns_has_entry_for_every_source():
    assert set(KEY_COLUMNS.keys()) == set(CSV_SOURCES) | set(EXCEL_SOURCES)


def test_key_columns_values_are_non_empty_lists():
    for source_file, columns in KEY_COLUMNS.items():
        assert isinstance(columns, list)
        assert len(columns) > 0, f"{source_file} has no key columns"


def test_every_role_column_exists_in_required_columns():
    for role_dict in (MONEY_QTY_COLUMNS, DATE_COLUMNS, TEXT_COLUMNS, KEY_COLUMNS):
        for source_file, columns in role_dict.items():
            for col in columns:
                assert col in REQUIRED_COLUMNS[source_file], (
                    f"{source_file}: {col!r} not in REQUIRED_COLUMNS"
                )


def test_customer_master_tax_code_not_in_any_role_dict():
    # tax_code is filled via fill_null_columns() inside transform_source(),
    # not cast/standardized/used-as-key — it must not appear in any role dict.
    for role_dict in (MONEY_QTY_COLUMNS, DATE_COLUMNS, TEXT_COLUMNS, KEY_COLUMNS):
        assert "tax_code" not in role_dict.get("SRC03_customer_master.csv", [])


def test_key_columns_include_customer_id_and_product_id_where_present():
    # Spot-check against VDAP-316's own example (customer_id/product_id NULL keys)
    assert "customer_id" in KEY_COLUMNS["SRC01_sales_transactions.csv"]
    assert "product_id" in KEY_COLUMNS["SRC01_sales_transactions.csv"]


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
