import os

import polars as pl

from src.extract.ingest_log import build_ingest_log_record, write_ingest_log


def test_build_ingest_log_record_strips_extension_for_source_name():
    record = build_ingest_log_record(
        batch_id="batch-1",
        source_file="SRC01_sales_transactions.csv",
        rows_loaded=10,
        status="success",
        duration_sec=0.5,
    )

    assert record == {
        "batch_id": "batch-1",
        "source_name": "SRC01_sales_transactions",
        "source_file": "SRC01_sales_transactions.csv",
        "source_platform": "google_drive",
        "rows_loaded": 10,
        "status": "success",
        "duration_sec": 0.5,
    }


def test_write_ingest_log_creates_parquet_with_all_columns(tmp_path):
    records = [
        build_ingest_log_record("batch-1", "SRC01_sales_transactions.csv", 10, "success", 0.1),
        build_ingest_log_record("batch-1", "SRC02_sales_target_plan.xlsx", 0, "failed", 0.0),
    ]

    path = write_ingest_log(records, str(tmp_path))

    assert path == os.path.join(str(tmp_path), "ingest_log.parquet")
    df = pl.read_parquet(path)
    assert df.columns == [
        "batch_id",
        "source_name",
        "source_file",
        "source_platform",
        "rows_loaded",
        "status",
        "duration_sec",
    ]
    assert df.height == 2
    assert df["status"].to_list() == ["success", "failed"]


def test_write_ingest_log_overwrites_on_rerun_same_dir(tmp_path):
    first = [build_ingest_log_record("batch-1", "SRC01_sales_transactions.csv", 10, "success", 0.1)]
    second = [build_ingest_log_record("batch-2", "SRC01_sales_transactions.csv", 20, "success", 0.2)]

    write_ingest_log(first, str(tmp_path))
    path = write_ingest_log(second, str(tmp_path))

    df = pl.read_parquet(path)
    assert df.height == 1
    assert df["batch_id"].to_list() == ["batch-2"]


def test_write_ingest_log_creates_missing_directory(tmp_path):
    target_dir = tmp_path / "20260801"
    records = [build_ingest_log_record("batch-1", "SRC01_sales_transactions.csv", 10, "success", 0.1)]

    path = write_ingest_log(records, str(target_dir))

    assert os.path.exists(path)
