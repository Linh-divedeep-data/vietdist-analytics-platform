"""Lineage metadata (attach_lineage) + String casting (cast_to_string) — filled in Epic Phase 1."""

from datetime import UTC, datetime

import polars as pl


def attach_lineage(
    df: pl.DataFrame, source_file: str, run_date: str, batch_id: str
) -> pl.DataFrame:
    return df.with_columns(
        pl.lit(source_file).alias("_source_file"),
        pl.lit("google_drive").alias("_source_platform"),
        pl.lit(run_date).alias("_run_date"),
        pl.lit(datetime.now(UTC)).alias("_ingested_at"),
        pl.lit(batch_id).alias("_batch_id"),
    )
