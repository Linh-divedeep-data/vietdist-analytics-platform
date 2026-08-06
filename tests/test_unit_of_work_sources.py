import polars as pl
import pytest

from config.sources import REQUIRED_COLUMNS
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

_EXPECTED = [
    (src01_sales_transactions, "SRC01_sales_transactions.csv"),
    (src02_sales_target_plan, "SRC02_sales_target_plan.xlsx"),
    (src03_customer_master, "SRC03_customer_master.csv"),
    (src04_product_master, "SRC04_product_master.xlsx"),
    (src05_distributor_orders, "SRC05_distributor_orders.xlsx"),
    (src06_distributor_master, "SRC06_distributor_master.csv"),
    (src07_employee_master, "SRC07_employee_master.xlsx"),
    (src08_territory_mapping, "SRC08_territory_mapping.xlsx"),
    (src09_return_transactions, "SRC09_return_transactions.csv"),
    (src10_promotion_program, "SRC10_promotion_program.xlsx"),
]


@pytest.mark.parametrize("module,expected_source_file", _EXPECTED)
def test_module_source_file_matches_expected(module, expected_source_file):
    assert module.SOURCE_FILE == expected_source_file


@pytest.mark.parametrize("module,_", _EXPECTED)
def test_module_exposes_run_function(module, _):
    assert callable(module.run)


def test_src01_run_returns_full_lineage_all_string_success_record(tmp_path):
    columns = REQUIRED_COLUMNS["SRC01_sales_transactions.csv"]
    header = ",".join(columns)
    row = ",".join(["x"] * len(columns))
    (tmp_path / "SRC01_sales_transactions.csv").write_text(f"{header}\n{row}\n")

    df, record = src01_sales_transactions.run(
        raw_dir=str(tmp_path), run_date="2026-08-04", batch_id="batch-123"
    )

    assert df is not None
    assert all(dtype == pl.String for dtype in df.dtypes)
    for col in ("_source_file", "_source_platform", "_run_date", "_ingested_at", "_batch_id"):
        assert col in df.columns
    assert record["status"] == "success"
    assert record["rows_loaded"] == df.height == 1


def test_src02_run_returns_full_lineage_all_string_success_record(monkeypatch, tmp_path):
    columns = REQUIRED_COLUMNS["SRC02_sales_target_plan.xlsx"]
    fake_df = pl.DataFrame({col: ["x"] for col in columns})
    monkeypatch.setattr(src02_sales_target_plan.parser.pl, "read_excel", lambda path: fake_df)

    df, record = src02_sales_target_plan.run(
        raw_dir=str(tmp_path), run_date="2026-08-04", batch_id="batch-123"
    )

    assert df is not None
    assert all(dtype == pl.String for dtype in df.dtypes)
    for col in ("_source_file", "_source_platform", "_run_date", "_ingested_at", "_batch_id"):
        assert col in df.columns
    assert record["status"] == "success"
    assert record["rows_loaded"] == df.height == 1
