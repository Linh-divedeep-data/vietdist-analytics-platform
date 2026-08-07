"""build_gold_log_record(), write_gold_log() — Gold's per-table run log, mirroring
Silver's silver_log.parquet contract so all 3 layers log the same way."""

import os

import polars as pl


def build_gold_log_record(
    table_name: str,
    run_date: str,
    row_count: int,
    status: str,
    error_message: str | None = None,
) -> dict:
    """Build one Gold transform-log record for a single table build attempt."""
    return {
        "table_name": table_name,
        "run_date": run_date,
        "row_count": row_count,
        "status": status,
        "error_message": error_message,
    }


def write_gold_log(record: dict, out_dir: str) -> str:
    """Persist one Gold log record to out_dir/gold_log.parquet, appending to any
    existing rows from prior runs of the same run_date — same append-not-overwrite
    contract as write_silver_log(), including the error_message Utf8-cast fix for
    concatenating a Null-typed column (all-None so far) with a real string later."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "gold_log.parquet")
    new_row = pl.DataFrame([record], schema_overrides={"error_message": pl.Utf8})

    if os.path.exists(path):
        existing = pl.scan_parquet(path).with_columns(pl.col("error_message").cast(pl.Utf8))
        combined = pl.concat([existing, new_row.lazy()], how="vertical")
    else:
        combined = new_row.lazy()

    combined.collect().write_parquet(path)
    return path
