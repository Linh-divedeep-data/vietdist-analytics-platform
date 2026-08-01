# src/extract/unit_of_work/base.py
"""Logic dùng chung cho mọi unit_of_work theo nguồn: đọc 1 file, gắn lineage,
ép String, đo duration, dựng ingest_log record — tránh lặp lại ở 10 file src0X.

Lỗi đọc file KHÔNG bắt ở đây — orchestrator quyết định fail-safe theo từng
nguồn (giống pattern download_all_sources), 1 nguồn lỗi không crash cả batch.
"""

import time
from collections.abc import Callable

import polars as pl

from src.extract.ingest_log import build_ingest_log_record
from src.extract.lineage import attach_lineage, cast_to_string

ReadFn = Callable[[str, str], pl.DataFrame]


def process_source(
    read_fn: ReadFn, source_file: str, raw_dir: str, run_date: str, batch_id: str
) -> tuple[pl.DataFrame, dict]:
    """Đọc source_file bằng read_fn(name, raw_dir), gắn lineage, ép String.

    Trả (DataFrame sẵn sàng ghi Bronze, ingest_log record status=success).
    """
    started = time.monotonic()
    df = read_fn(source_file, raw_dir)
    df = attach_lineage(df, source_file=source_file, run_date=run_date, batch_id=batch_id)
    df = cast_to_string(df)
    duration_sec = time.monotonic() - started

    record = build_ingest_log_record(
        batch_id=batch_id,
        source_file=source_file,
        rows_loaded=df.height,
        status="success",
        duration_sec=duration_sec,
    )
    return df, record
