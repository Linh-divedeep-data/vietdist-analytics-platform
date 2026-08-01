import polars as pl
import pytest

from src.extract.registry import UNIT_OF_WORK
from src.extract.unit_of_work import (
    src01_sales_transactions,
    src02_sales_target_plan,
)


@pytest.fixture
def csv_raw_dir(tmp_path):
    (tmp_path / "SRC01_sales_transactions.csv").write_text("order_id,amount\n1,100\n2,200\n")
    return tmp_path


@pytest.fixture
def excel_raw_dir(tmp_path):
    pl.DataFrame({"target_id": [1, 2], "amount": [100, 200]}).write_excel(
        tmp_path / "SRC02_sales_target_plan.xlsx"
    )
    return tmp_path


def test_csv_unit_of_work_returns_lineage_tagged_all_string_dataframe(csv_raw_dir):
    df, record = src01_sales_transactions.run(str(csv_raw_dir), run_date="2026-08-01", batch_id="batch-1")

    assert all(dtype == pl.String for dtype in df.dtypes)
    assert df["_source_file"].to_list() == ["SRC01_sales_transactions.csv", "SRC01_sales_transactions.csv"]
    assert df["_batch_id"].to_list() == ["batch-1", "batch-1"]
    assert record["status"] == "success"
    assert record["rows_loaded"] == 2
    assert record["source_name"] == "SRC01_sales_transactions"


def test_excel_unit_of_work_returns_lineage_tagged_all_string_dataframe(excel_raw_dir):
    df, record = src02_sales_target_plan.run(str(excel_raw_dir), run_date="2026-08-01", batch_id="batch-1")

    assert all(dtype == pl.String for dtype in df.dtypes)
    assert record["status"] == "success"
    assert record["rows_loaded"] == 2


def test_unit_of_work_raises_on_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        src01_sales_transactions.run(str(tmp_path), run_date="2026-08-01", batch_id="batch-1")


def test_every_registry_entry_produces_matching_source_file_in_record(csv_raw_dir, excel_raw_dir):
    tmp_dir = csv_raw_dir
    for excel_file in excel_raw_dir.glob("*.xlsx"):
        (tmp_dir / excel_file.name).write_bytes(excel_file.read_bytes())

    for source_file in ("SRC01_sales_transactions.csv", "SRC02_sales_target_plan.xlsx"):
        run_fn = UNIT_OF_WORK[source_file]
        _, record = run_fn(str(tmp_dir), run_date="2026-08-01", batch_id="batch-1")
        assert record["source_file"] == source_file
