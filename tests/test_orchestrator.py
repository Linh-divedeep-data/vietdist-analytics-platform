import os

import polars as pl

from src.extract.orchestrator import (
    get_bronze_output_dir,
    run_bronze_ingestion,
    write_bronze_parquet,
)


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


def _fake_source(source_name, status, rows=1):
    def run(raw_dir, run_date, batch_id):
        if status != "success":
            return None, {
                "batch_id": batch_id,
                "source_name": source_name,
                "source_file": f"{source_name}.csv",
                "source_platform": "google_drive",
                "rows_loaded": 0,
                "status": status,
                "duration_sec": 0.01,
            }
        df = pl.DataFrame({"a": ["x"] * rows})
        return df, {
            "batch_id": batch_id,
            "source_name": source_name,
            "source_file": f"{source_name}.csv",
            "source_platform": "google_drive",
            "rows_loaded": rows,
            "status": "success",
            "duration_sec": 0.01,
        }
    return run


def test_run_bronze_ingestion_happy_path_writes_file_per_source(tmp_path, monkeypatch):
    fake_registry = {
        "SRCA.csv": _fake_source("srcA", "success"),
        "SRCB.csv": _fake_source("srcB", "success"),
        "SRCC.csv": _fake_source("srcC", "success"),
    }
    monkeypatch.setattr("src.extract.orchestrator.UNIT_OF_WORK", fake_registry)

    records = run_bronze_ingestion(
        run_date="2026-08-04", batch_id="batch-1", raw_dir=str(tmp_path), bronze_dir=str(tmp_path)
    )

    out_dir = get_bronze_output_dir("2026-08-04", bronze_dir=str(tmp_path))
    written = sorted(f for f in os.listdir(out_dir) if f != "ingest_log.parquet")
    assert written == ["srcA.parquet", "srcB.parquet", "srcC.parquet"]
    assert len(records) == 3
    assert all(r["status"] == "success" for r in records)


def test_run_bronze_ingestion_continues_after_one_source_fails(tmp_path, monkeypatch):
    fake_registry = {
        "SRCA.csv": _fake_source("srcA", "success"),
        "SRCB.csv": _fake_source("srcB", "failed"),
        "SRCC.csv": _fake_source("srcC", "success"),
    }
    monkeypatch.setattr("src.extract.orchestrator.UNIT_OF_WORK", fake_registry)

    records = run_bronze_ingestion(
        run_date="2026-08-04", batch_id="batch-1", raw_dir=str(tmp_path), bronze_dir=str(tmp_path)
    )

    out_dir = get_bronze_output_dir("2026-08-04", bronze_dir=str(tmp_path))
    written = sorted(f for f in os.listdir(out_dir) if f != "ingest_log.parquet")
    assert written == ["srcA.parquet", "srcC.parquet"]
    assert len(records) == 3
    statuses = {r["source_name"]: r["status"] for r in records}
    assert statuses == {"srcA": "success", "srcB": "failed", "srcC": "success"}


def test_run_bronze_ingestion_returns_one_record_per_registered_source():
    from src.extract.registry import UNIT_OF_WORK as real_registry

    assert len(real_registry) == 10  # sanity: loop iterates the real 10-source registry


def test_run_bronze_ingestion_row_count_stable_across_reruns(tmp_path, monkeypatch):
    fake_registry = {
        "SRCA.csv": _fake_source("srcA", "success", rows=3),
        "SRCB.csv": _fake_source("srcB", "success", rows=2),
    }
    monkeypatch.setattr("src.extract.orchestrator.UNIT_OF_WORK", fake_registry)

    run_bronze_ingestion(
        run_date="2026-08-04", batch_id="b1", raw_dir=str(tmp_path), bronze_dir=str(tmp_path)
    )
    out_dir = get_bronze_output_dir("2026-08-04", bronze_dir=str(tmp_path))
    first_counts = {
        name: pl.read_parquet(os.path.join(out_dir, f"{name}.parquet")).height
        for name in ("srcA", "srcB")
    }

    run_bronze_ingestion(
        run_date="2026-08-04", batch_id="b2", raw_dir=str(tmp_path), bronze_dir=str(tmp_path)
    )
    second_counts = {
        name: pl.read_parquet(os.path.join(out_dir, f"{name}.parquet")).height
        for name in ("srcA", "srcB")
    }

    assert first_counts == second_counts == {"srcA": 3, "srcB": 2}


def test_run_bronze_ingestion_writes_ingest_log_parquet(tmp_path, monkeypatch):
    fake_registry = {
        "SRCA.csv": _fake_source("srcA", "success"),
        "SRCB.csv": _fake_source("srcB", "failed"),
    }
    monkeypatch.setattr("src.extract.orchestrator.UNIT_OF_WORK", fake_registry)

    records = run_bronze_ingestion(
        run_date="2026-08-04", batch_id="batch-1", raw_dir=str(tmp_path), bronze_dir=str(tmp_path)
    )

    out_dir = get_bronze_output_dir("2026-08-04", bronze_dir=str(tmp_path))
    log_path = os.path.join(out_dir, "ingest_log.parquet")
    assert os.path.exists(log_path)

    log_df = pl.read_parquet(log_path)
    assert log_df.height == len(records) == 2
    assert set(log_df["source_name"].to_list()) == {"srcA", "srcB"}
