# src/extract/ingest_log.py
"""Ghi ingest_log.parquet — audit trail cho mỗi lần chạy Bronze (P1.5, xem phase1_bronze_ingestion.md).

Schema: batch_id, source_name, source_file, source_platform, rows_loaded, status, duration_sec.
"""

import os

import polars as pl

INGEST_LOG_COLUMNS = [
    "batch_id",
    "source_name",
    "source_file",
    "source_platform",
    "rows_loaded",
    "status",
    "duration_sec",
]


def build_ingest_log_record(
    batch_id: str,
    source_file: str,
    rows_loaded: int,
    status: str,
    duration_sec: float,
    source_platform: str = "google_drive",
) -> dict:
    """Dựng 1 dòng ingest_log — source_name là source_file bỏ phần đuôi file."""
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
    """Ghi ingest_log.parquet CÙNG thư mục Bronze của run đó.

    Ghi đè (không append) — cùng nguyên tắc idempotency của partition
    data/bronze/<run_date>/ (xem CLAUDE.md), tránh nối dài vô hạn qua nhiều lần chạy lại.
    """
    os.makedirs(bronze_run_dir, exist_ok=True)
    path = os.path.join(bronze_run_dir, "ingest_log.parquet")
    pl.DataFrame(records, schema=INGEST_LOG_COLUMNS).write_parquet(path)
    return path
