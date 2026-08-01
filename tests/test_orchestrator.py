
import polars as pl

from src.extract import orchestrator


def _fake_unit_of_work(source_file, height=2, fail=False):
    def run(raw_dir, run_date, batch_id):
        if fail:
            raise ConnectionError("simulated read failure")
        df = pl.DataFrame({"col": [str(i) for i in range(height)]})
        record = {
            "batch_id": batch_id,
            "source_name": source_file.split(".")[0],
            "source_file": source_file,
            "source_platform": "google_drive",
            "rows_loaded": height,
            "status": "success",
            "duration_sec": 0.01,
        }
        return df, record

    return run


def test_writes_one_parquet_per_registered_source(tmp_path, monkeypatch):
    fake_registry = {
        "SRC01_sales_transactions.csv": _fake_unit_of_work("SRC01_sales_transactions.csv"),
        "SRC02_sales_target_plan.xlsx": _fake_unit_of_work("SRC02_sales_target_plan.xlsx"),
    }
    monkeypatch.setattr(orchestrator, "UNIT_OF_WORK", fake_registry)

    orchestrator.run_bronze_ingestion(
        run_date="2026-08-01", batch_id="batch-1", raw_dir=str(tmp_path), bronze_dir=str(tmp_path / "bronze")
    )

    out_dir = tmp_path / "bronze" / "20260801"
    assert (out_dir / "SRC01_sales_transactions.parquet").exists()
    assert (out_dir / "SRC02_sales_target_plan.parquet").exists()


def test_partitions_by_run_date_stripped_of_dashes(tmp_path, monkeypatch):
    monkeypatch.setattr(
        orchestrator, "UNIT_OF_WORK", {"SRC01_sales_transactions.csv": _fake_unit_of_work("SRC01_sales_transactions.csv")}
    )

    orchestrator.run_bronze_ingestion(
        run_date="2026-08-01", batch_id="batch-1", raw_dir=str(tmp_path), bronze_dir=str(tmp_path / "bronze")
    )

    assert (tmp_path / "bronze" / "20260801").is_dir()


def test_rerun_same_run_date_overwrites_not_duplicates(tmp_path, monkeypatch):
    monkeypatch.setattr(
        orchestrator, "UNIT_OF_WORK", {"SRC01_sales_transactions.csv": _fake_unit_of_work("SRC01_sales_transactions.csv", height=3)}
    )

    orchestrator.run_bronze_ingestion(
        run_date="2026-08-01", batch_id="batch-1", raw_dir=str(tmp_path), bronze_dir=str(tmp_path / "bronze")
    )
    orchestrator.run_bronze_ingestion(
        run_date="2026-08-01", batch_id="batch-2", raw_dir=str(tmp_path), bronze_dir=str(tmp_path / "bronze")
    )

    out_file = tmp_path / "bronze" / "20260801" / "SRC01_sales_transactions.parquet"
    df = pl.read_parquet(out_file)
    assert df.height == 3
    assert list((tmp_path / "bronze" / "20260801").glob("SRC01_sales_transactions*.parquet")) == [out_file]


def test_one_source_failing_does_not_crash_batch(tmp_path, monkeypatch, capsys):
    fake_registry = {
        "SRC01_sales_transactions.csv": _fake_unit_of_work("SRC01_sales_transactions.csv"),
        "SRC02_sales_target_plan.xlsx": _fake_unit_of_work("SRC02_sales_target_plan.xlsx", fail=True),
    }
    monkeypatch.setattr(orchestrator, "UNIT_OF_WORK", fake_registry)

    records = orchestrator.run_bronze_ingestion(
        run_date="2026-08-01", batch_id="batch-1", raw_dir=str(tmp_path), bronze_dir=str(tmp_path / "bronze")
    )

    statuses = {r["source_file"]: r["status"] for r in records}
    assert statuses == {"SRC01_sales_transactions.csv": "success", "SRC02_sales_target_plan.xlsx": "failed"}
    out_dir = tmp_path / "bronze" / "20260801"
    assert (out_dir / "SRC01_sales_transactions.parquet").exists()
    assert not (out_dir / "SRC02_sales_target_plan.parquet").exists()


def test_writes_ingest_log_with_one_row_per_source(tmp_path, monkeypatch):
    fake_registry = {
        "SRC01_sales_transactions.csv": _fake_unit_of_work("SRC01_sales_transactions.csv"),
        "SRC02_sales_target_plan.xlsx": _fake_unit_of_work("SRC02_sales_target_plan.xlsx"),
    }
    monkeypatch.setattr(orchestrator, "UNIT_OF_WORK", fake_registry)

    orchestrator.run_bronze_ingestion(
        run_date="2026-08-01", batch_id="batch-1", raw_dir=str(tmp_path), bronze_dir=str(tmp_path / "bronze")
    )

    log_path = tmp_path / "bronze" / "20260801" / "ingest_log.parquet"
    df = pl.read_parquet(log_path)
    assert df.height == 2
    assert set(df["source_file"].to_list()) == {"SRC01_sales_transactions.csv", "SRC02_sales_target_plan.xlsx"}


def test_returns_ingest_log_records(tmp_path, monkeypatch):
    monkeypatch.setattr(
        orchestrator, "UNIT_OF_WORK", {"SRC01_sales_transactions.csv": _fake_unit_of_work("SRC01_sales_transactions.csv")}
    )

    records = orchestrator.run_bronze_ingestion(
        run_date="2026-08-01", batch_id="batch-1", raw_dir=str(tmp_path), bronze_dir=str(tmp_path / "bronze")
    )

    assert records == [
        {
            "batch_id": "batch-1",
            "source_name": "SRC01_sales_transactions",
            "source_file": "SRC01_sales_transactions.csv",
            "source_platform": "google_drive",
            "rows_loaded": 2,
            "status": "success",
            "duration_sec": 0.01,
        }
    ]
