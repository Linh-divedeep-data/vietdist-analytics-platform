import os

import polars as pl

from src.extract.orchestrator import get_bronze_output_dir, write_bronze_parquet


def test_get_bronze_output_dir_strips_dashes_from_run_date(tmp_path):
    out_dir = get_bronze_output_dir("2026-07-22", bronze_dir=str(tmp_path))

    assert out_dir == os.path.join(str(tmp_path), "20260722")


def test_get_bronze_output_dir_creates_directory_on_disk(tmp_path):
    out_dir = get_bronze_output_dir("2026-07-22", bronze_dir=str(tmp_path))

    assert os.path.isdir(out_dir)


def test_get_bronze_output_dir_returns_same_path_on_repeated_calls(tmp_path):
    first = get_bronze_output_dir("2026-07-22", bronze_dir=str(tmp_path))
    second = get_bronze_output_dir("2026-07-22", bronze_dir=str(tmp_path))

    assert first == second


def test_get_bronze_output_dir_does_not_raise_when_directory_already_exists(tmp_path):
    get_bronze_output_dir("2026-07-22", bronze_dir=str(tmp_path))

    # must not raise on the second call even though the directory already exists
    get_bronze_output_dir("2026-07-22", bronze_dir=str(tmp_path))


def _success_record(source_name="src01_sales_transactions"):
    return {
        "batch_id": "b1",
        "source_name": source_name,
        "source_file": f"{source_name}.csv",
        "source_platform": "google_drive",
        "rows_loaded": 2,
        "status": "success",
        "duration_sec": 0.01,
    }


def test_write_bronze_parquet_creates_file_with_source_name(tmp_path):
    df = pl.DataFrame({"a": [1, 2]})
    record = _success_record()

    path = write_bronze_parquet(df, record, str(tmp_path))

    assert path == os.path.join(str(tmp_path), "src01_sales_transactions.parquet")
    assert os.path.exists(path)


def test_write_bronze_parquet_row_count_matches(tmp_path):
    df = pl.DataFrame({"a": [1, 2, 3]})
    record = _success_record()

    path = write_bronze_parquet(df, record, str(tmp_path))

    assert pl.read_parquet(path).height == 3


def test_write_bronze_parquet_skips_write_when_status_not_success(tmp_path):
    df = None
    record = _success_record()
    record["status"] = "schema_mismatch"

    result = write_bronze_parquet(df, record, str(tmp_path))

    assert result is None
    assert os.listdir(tmp_path) == []


def test_write_bronze_parquet_skips_write_when_status_failed(tmp_path):
    df = None
    record = _success_record()
    record["status"] = "failed"

    result = write_bronze_parquet(df, record, str(tmp_path))

    assert result is None
    assert os.listdir(tmp_path) == []
