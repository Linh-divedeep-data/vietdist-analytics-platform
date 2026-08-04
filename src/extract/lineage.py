"""Lineage metadata (attach_lineage) + String casting (cast_to_string) — filled in Epic Phase 1."""

from datetime import UTC, datetime

import polars as pl


def attach_lineage(
    df: pl.DataFrame, source_file: str, run_date: str, batch_id: str
) -> pl.DataFrame:
    """Stamp df with the 5 Bronze lineage columns for one ingestion run."""
    return df.with_columns(
        pl.lit(source_file).alias("_source_file"),
        pl.lit("google_drive").alias("_source_platform"),
        pl.lit(run_date).alias("_run_date"),
        pl.lit(datetime.now(UTC)).alias("_ingested_at"),
        pl.lit(batch_id).alias("_batch_id"),
    )


def cast_to_string(df: pl.DataFrame) -> pl.DataFrame:
    """Cast every column of df to String — the fail-safe Bronze invariant."""
    return df.select(pl.all().cast(pl.String))
