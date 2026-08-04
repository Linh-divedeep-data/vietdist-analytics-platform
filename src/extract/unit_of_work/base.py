"""process_source(): shared per-source read+lineage+write flow used by every unit_of_work/srcXX_*.py — filled in Epic Phase 1."""

import time

import polars as pl

from src.extract.ingest_log import build_ingest_log_record
from src.extract.lineage import attach_lineage, cast_to_string
from src.extract.parser import SchemaMismatchError, validate_schema


def process_source(
    read_fn,
    source_file: str,
    raw_dir: str,
    run_date: str,
    batch_id: str,
) -> tuple[pl.DataFrame | None, dict]:
    start = time.perf_counter()
    try:
        df = read_fn(source_file, raw_dir)
        duration_sec = time.perf_counter() - start
    except Exception:  # noqa: BLE001 -- any read/parse failure must classify as "failed", not crash the batch
        duration_sec = time.perf_counter() - start
        record = build_ingest_log_record(
            batch_id, source_file, rows_loaded=0, status="failed", duration_sec=duration_sec
        )
        return None, record

    try:
        validate_schema(df, source_file)
    except SchemaMismatchError:
        record = build_ingest_log_record(
            batch_id, source_file, rows_loaded=0, status="schema_mismatch", duration_sec=duration_sec
        )
        return None, record

    df = attach_lineage(df, source_file, run_date, batch_id)
    df = cast_to_string(df)

    record = build_ingest_log_record(
        batch_id, source_file, rows_loaded=df.height, status="success", duration_sec=duration_sec
    )
    return df, record
