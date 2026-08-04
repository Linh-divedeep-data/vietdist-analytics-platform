import polars as pl

from config.sources import REQUIRED_COLUMNS
from src.extract.unit_of_work import base


def _valid_df_for(source_file: str) -> pl.DataFrame:
    return pl.DataFrame({col: ["x"] for col in REQUIRED_COLUMNS[source_file]})


def test_process_source_happy_path_returns_df_with_lineage_and_success_record():
    source_file = "SRC03_customer_master.csv"

    def fake_read_fn(name, raw_dir):
        return _valid_df_for(source_file)

    df, record = base.process_source(
        fake_read_fn, source_file, raw_dir="data/raw", run_date="2026-08-04", batch_id="batch-123"
    )

    assert df is not None
    assert all(dtype == pl.String for dtype in df.dtypes)
    for col in ("_source_file", "_source_platform", "_run_date", "_ingested_at", "_batch_id"):
        assert col in df.columns

    assert record["status"] == "success"
    assert record["rows_loaded"] == df.height
    assert record["batch_id"] == "batch-123"
    assert record["source_file"] == source_file
    assert isinstance(record["duration_sec"], float)
    assert record["duration_sec"] >= 0


def test_process_source_schema_mismatch_returns_none_and_schema_mismatch_record():
    source_file = "SRC03_customer_master.csv"
    columns = REQUIRED_COLUMNS[source_file].copy()
    columns.remove("phone")

    def fake_read_fn(name, raw_dir):
        return pl.DataFrame({col: ["x"] for col in columns})

    df, record = base.process_source(
        fake_read_fn, source_file, raw_dir="data/raw", run_date="2026-08-04", batch_id="batch-123"
    )

    assert df is None
    assert record["status"] == "schema_mismatch"
    assert record["rows_loaded"] == 0
    assert record["source_file"] == source_file
    assert isinstance(record["duration_sec"], float)
    assert record["duration_sec"] >= 0


def test_process_source_read_error_returns_none_and_failed_record():
    source_file = "SRC03_customer_master.csv"

    def fake_read_fn(name, raw_dir):
        raise FileNotFoundError("does_not_exist.csv")

    df, record = base.process_source(
        fake_read_fn, source_file, raw_dir="data/raw", run_date="2026-08-04", batch_id="batch-123"
    )

    assert df is None
    assert record["status"] == "failed"
    assert record["rows_loaded"] == 0
    assert record["source_file"] == source_file
    assert isinstance(record["duration_sec"], float)
    assert record["duration_sec"] >= 0
