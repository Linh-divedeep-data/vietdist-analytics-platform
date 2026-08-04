"""build_ingest_log_record() + write_ingest_log() — filled in Epic Phase 1 (VDAP-116-118)."""

import os

import polars as pl


def build_ingest_log_record(
    batch_id: str,
    source_file: str,
    rows_loaded: int,
    status: str,
    duration_sec: float,
    source_platform: str = "google_drive",
) -> dict:
    """Build one ingest-log record summarizing how a single source was processed."""
    return {
        "batch_id": batch_id,
        "source_name": os.path.splitext(source_file)[0],
        "source_file": source_file,
        "source_platform": source_platform,
        "rows_loaded": rows_loaded,
        "status": status,
        "duration_sec": duration_sec,
    }


def write_ingest_log(records: list[dict], bronze_run_dir: str) -> str:
    """Write all ingest-log records for a run into one Parquet file, overwriting any prior run."""
    os.makedirs(bronze_run_dir, exist_ok=True)
    path = os.path.join(bronze_run_dir, "ingest_log.parquet")
    pl.DataFrame(records).write_parquet(path)
    return path
