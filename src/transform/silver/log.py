"""build_silver_log_record(), write_silver_log()."""

import os

import polars as pl


def build_silver_log_record(
    source_file: str,
    run_date: str,
    row_count_in: int,
    row_count_out: int,
    null_count: int,
    dedup_count: int,
    status: str,
    error_message: str | None = None,
) -> dict:
    """Build one Silver transform-log record summarizing how a single source was processed.

    Schema deliberately excludes batch_id (unlike Bronze's ingest_log) — Silver
    logs are keyed by source_name + run_date, not by pipeline run.
    """
    return {
        "source_name": os.path.splitext(source_file)[0],
        "run_date": run_date,
        "row_count_in": row_count_in,
        "row_count_out": row_count_out,
        "null_count": null_count,
        "dedup_count": dedup_count,
        "status": status,
        "error_message": error_message,
    }


def write_silver_log(record: dict, out_dir: str) -> str:
    """Persist one Silver log record to out_dir/silver_log.parquet, appending
    to any existing rows from prior runs of the same run_date — unlike
    Bronze's write_ingest_log(), this must NOT overwrite (VDAP-420 AC).

    error_message is force-cast to Utf8 on both sides before concatenating:
    when every record written so far has error_message=None (e.g. every
    source succeeded), Polars infers that column as dtype Null, and a later
    row with a real string then fails pl.concat() with a SchemaError. Since
    error_message is legitimately str | None across the record's lifetime,
    pin the dtype explicitly instead of leaving it to per-call inference.
    """
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "silver_log.parquet")
    new_row = pl.DataFrame([record], schema_overrides={"error_message": pl.Utf8})

    if os.path.exists(path):
        existing = pl.scan_parquet(path).with_columns(pl.col("error_message").cast(pl.Utf8))
        combined = pl.concat([existing, new_row.lazy()], how="vertical")
    else:
        combined = new_row.lazy()

    combined.collect().write_parquet(path)
    return path
