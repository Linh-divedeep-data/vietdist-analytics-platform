import polars as pl

from src.extract import ingest_log


def test_build_ingest_log_record_has_exactly_seven_fields_with_correct_values():
    record = ingest_log.build_ingest_log_record(
        batch_id="batch-123",
        source_file="SRC01_sales.csv",
        rows_loaded=42,
        status="success",
        duration_sec=1.23,
    )

    assert record == {
        "batch_id": "batch-123",
        "source_name": "SRC01_sales",
        "source_file": "SRC01_sales.csv",
        "source_platform": "google_drive",
        "rows_loaded": 42,
        "status": "success",
        "duration_sec": 1.23,
    }


def test_build_ingest_log_record_source_name_strips_only_last_extension():
    record = ingest_log.build_ingest_log_record(
        batch_id="batch-123",
        source_file="SRC01.sales.v2.csv",
        rows_loaded=10,
        status="success",
        duration_sec=0.5,
    )

    assert record["source_name"] == "SRC01.sales.v2"
    assert record["source_file"] == "SRC01.sales.v2.csv"


def test_build_ingest_log_record_default_source_platform_is_google_drive():
    record = ingest_log.build_ingest_log_record(
        batch_id="batch-123",
        source_file="SRC02_target.xlsx",
        rows_loaded=5,
        status="failed",
        duration_sec=0.1,
    )

    assert record["source_platform"] == "google_drive"


def test_build_ingest_log_record_accepts_explicit_source_platform_override():
    record = ingest_log.build_ingest_log_record(
        batch_id="batch-123",
        source_file="SRC03_other.csv",
        rows_loaded=0,
        status="schema_mismatch",
        duration_sec=0.05,
        source_platform="sftp",
    )

    assert record["source_platform"] == "sftp"


def _records(*, batch_id="batch-123"):
    return [
        ingest_log.build_ingest_log_record(
            batch_id=batch_id,
            source_file="SRC01_sales.csv",
            rows_loaded=10,
            status="success",
            duration_sec=0.1,
        ),
        ingest_log.build_ingest_log_record(
            batch_id=batch_id,
            source_file="SRC02_target.xlsx",
            rows_loaded=0,
            status="schema_mismatch",
            duration_sec=0.05,
        ),
    ]


def test_write_ingest_log_creates_directory_if_missing(tmp_path):
    bronze_run_dir = str(tmp_path / "20260804")

    path = ingest_log.write_ingest_log(_records(), bronze_run_dir)

    assert path == str(tmp_path / "20260804" / "ingest_log.parquet")
    assert (tmp_path / "20260804" / "ingest_log.parquet").exists()


def test_write_ingest_log_readback_has_all_seven_columns(tmp_path):
    path = ingest_log.write_ingest_log(_records(), str(tmp_path))

    df = pl.read_parquet(path)

    assert set(df.columns) == {
        "batch_id", "source_name", "source_file", "source_platform",
        "rows_loaded", "status", "duration_sec",
    }
    assert df.height == 2


def test_write_ingest_log_rerun_overwrites_not_appends(tmp_path):
    ingest_log.write_ingest_log(_records(batch_id="b1"), str(tmp_path))
    path = ingest_log.write_ingest_log(_records(batch_id="b2"), str(tmp_path))

    df = pl.read_parquet(path)

    assert df.height == 2
    assert set(df["batch_id"].to_list()) == {"b2"}
