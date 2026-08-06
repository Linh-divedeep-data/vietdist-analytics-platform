"""Silver transform entrypoints (Epic Phase 2) — filled in incrementally by VDAP-309/310/311.

validate_required_columns() (VDAP-309) is a second defensive schema check,
reusing src.extract.parser.validate_schema() so a missing column halts the
Silver transform with the same clear error Bronze already raises, instead of
silently mis-mapping a renamed/dropped column.
"""

import logging
import os
import uuid

import polars as pl

from config.settings import BRONZE_DIR, SILVER_DIR
from config.sources import (
    CSV_SOURCES,
    DATE_COLUMNS,
    DATE_FORMAT_BY_SOURCE,
    EXCEL_SOURCES,
    KEY_COLUMNS,
    MONEY_QTY_COLUMNS,
    TEXT_COLUMNS,
)
from src.extract.parser import SchemaMismatchError, validate_schema
from src.logger import get_logger

_logger = logging.getLogger(__name__)


def _row_count(frame: pl.DataFrame | pl.LazyFrame) -> int:
    """Row count that works for both Eager and Lazy frames without forcing a full materialize."""
    if isinstance(frame, pl.LazyFrame):
        return frame.select(pl.len()).collect().item()
    return frame.height


def _null_count(frame: pl.DataFrame | pl.LazyFrame, col: str) -> int:
    """Null count for one column, Eager or Lazy."""
    if isinstance(frame, pl.LazyFrame):
        return frame.select(pl.col(col).null_count()).collect().item()
    return frame[col].null_count()


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


def validate_required_columns(df: pl.DataFrame, source_file: str) -> None:
    """Second defensive check before Silver transform: reuse Bronze's schema validation."""
    try:
        validate_schema(df, source_file)
    except SchemaMismatchError as error:
        _logger.warning(
            "%s: thiếu cột bắt buộc %s ở Silver — lẽ ra phải bị chặn từ Bronze rồi",
            source_file,
            error.missing_cols,
        )
        raise


def cast_money_and_qty_columns(df: pl.DataFrame, columns: list[str]) -> pl.DataFrame:
    """Strip thousand-separator commas and cast money/quantity columns to Float64."""
    return df.with_columns(
        pl.col(col).str.replace_all(",", "").cast(pl.Float64) for col in columns
    )


def cast_date_columns(
    df: pl.DataFrame | pl.LazyFrame, columns: list[str], source_file: str
) -> pl.DataFrame | pl.LazyFrame:
    """Cast date columns to pl.Date using DATE_FORMAT_BY_SOURCE, logging the post-parse NULL ratio per column."""
    fmt = DATE_FORMAT_BY_SOURCE[source_file]
    result = df.with_columns(
        pl.col(col).str.strptime(pl.Date, fmt, strict=False) for col in columns
    )

    total = _row_count(result)
    for col in columns:
        null_ratio = _null_count(result, col) / total
        if null_ratio > 0.5:
            _logger.warning(
                "%s.%s: %.0f%% NULL sau khi parse ngày (format=%s) — nghi lệch format, không phải data rác thật",
                source_file,
                col,
                null_ratio * 100,
                fmt,
            )
        else:
            _logger.info(
                "%s.%s: %.0f%% NULL sau khi parse ngày (format=%s)",
                source_file,
                col,
                null_ratio * 100,
                fmt,
            )

    return result


def standardize_text_columns(df: pl.DataFrame, columns: list[str]) -> pl.DataFrame:
    """Strip leading/trailing whitespace and uppercase business text columns."""
    return df.with_columns(
        pl.col(col).str.strip_chars().str.to_uppercase() for col in columns
    )


def drop_duplicate_rows(df: pl.DataFrame) -> pl.DataFrame:
    """Remove exact full-row duplicates (e.g. repeated rows in customer_master)."""
    return df.unique(maintain_order=True)


def drop_null_key_rows(
    df: pl.DataFrame | pl.LazyFrame, columns: list[str]
) -> pl.DataFrame | pl.LazyFrame:
    """Drop rows where any of the given primary-key columns is NULL, logging the dropped row count."""
    result = df.filter(pl.all_horizontal(pl.col(col).is_not_null() for col in columns))

    dropped = _row_count(df) - _row_count(result)
    if dropped > 0:
        _logger.info("Loại %d dòng NULL ở cột khóa %s", dropped, columns)

    return result


def fill_null_columns(df: pl.DataFrame, columns: list[str], value: str) -> pl.DataFrame:
    """Fill NULL values in the given columns with a fixed value (e.g. customer_master.tax_code -> "UNKNOWN")."""
    return df.with_columns(pl.col(col).fill_null(value) for col in columns)


def get_silver_output_dir(run_date: str, silver_dir: str = SILVER_DIR) -> str:
    """Return (creating if needed) the Silver output directory for a run_date."""
    out_dir = os.path.join(silver_dir, run_date.replace("-", ""))
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def write_silver_parquet(df: pl.DataFrame, source_name: str, out_dir: str) -> str:
    """Write a cleaned Silver DataFrame to out_dir/<source_name>.parquet."""
    path = os.path.join(out_dir, f"{source_name}.parquet")
    df.write_parquet(path)
    return path


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


def transform_source_with_stats(
    df: pl.DataFrame | pl.LazyFrame, source_file: str
) -> tuple[pl.DataFrame, dict]:
    """Run one source through the full 6-step Silver cleaning pipeline, also
    returning row_count_in/out, dedup_count, and null_count for logging
    (VDAP-419) — real counts computed from row-count deltas, never hardcoded.
    Runs Lazy internally regardless of input type (VDAP-384), collecting once
    at the end so the returned DataFrame is always eager, ready for
    write_silver_parquet()."""
    lazy_df = df.lazy() if isinstance(df, pl.DataFrame) else df

    row_count_in = _row_count(lazy_df)
    validate_required_columns(lazy_df, source_file)

    result = cast_money_and_qty_columns(lazy_df, MONEY_QTY_COLUMNS[source_file])
    result = cast_date_columns(result, DATE_COLUMNS[source_file], source_file)
    result = standardize_text_columns(result, TEXT_COLUMNS[source_file])

    before_dedup = _row_count(result)
    result = drop_duplicate_rows(result)
    dedup_count = before_dedup - _row_count(result)

    before_null_drop = _row_count(result)
    result = drop_null_key_rows(result, KEY_COLUMNS[source_file])
    null_count = before_null_drop - _row_count(result)

    if source_file == "SRC03_customer_master.csv":
        result = fill_null_columns(result, ["tax_code"], "UNKNOWN")

    result = result.collect() if isinstance(result, pl.LazyFrame) else result

    stats = {
        "row_count_in": row_count_in,
        "row_count_out": result.height,
        "dedup_count": dedup_count,
        "null_count": null_count,
    }
    return result, stats


def transform_source(df: pl.DataFrame, source_file: str) -> pl.DataFrame:
    """Run one source through the full 6-step Silver cleaning pipeline.

    Thin wrapper over transform_source_with_stats() — kept for backward
    compatibility with existing call sites/tests that only need the DataFrame.
    """
    result, _stats = transform_source_with_stats(df, source_file)
    return result


def run_silver_transform(
    run_date: str,
    bronze_dir: str = BRONZE_DIR,
    silver_dir: str = SILVER_DIR,
    batch_id: str | None = None,
) -> list[dict]:
    """Run every canonical source through transform_source(), writing Silver Parquet.
    One failing source is logged and skipped, not fatal to the batch.

    batch_id is optional (unlike run_bronze_ingestion, which requires it from
    main.py): main.py does not pass one for the silver layer today, so a
    fresh uuid4 is generated here when the caller doesn't supply one, purely
    to stamp get_logger()'s log lines — it is never stored in the silver log
    record itself (VDAP-419 schema deliberately excludes batch_id)."""
    bronze_date_dir = os.path.join(bronze_dir, run_date.replace("-", ""))
    out_dir = get_silver_output_dir(run_date, silver_dir)
    logger = get_logger(batch_id or str(uuid.uuid4()))

    records = []
    for source_file in CSV_SOURCES + EXCEL_SOURCES:
        source_name = source_file.rsplit(".", 1)[0]
        record = {"source_file": source_file, "status": "success", "error": None}

        row_count_in = row_count_out = null_count = dedup_count = 0
        status = "success"
        error_message = None

        try:
            df = pl.scan_parquet(os.path.join(bronze_date_dir, f"{source_name}.parquet"))
            row_count_in = _row_count(df)
            result, stats = transform_source_with_stats(df, source_file)
            row_count_out = stats["row_count_out"]
            dedup_count = stats["dedup_count"]
            null_count = stats["null_count"]
            write_silver_parquet(result, source_name, out_dir)
        except Exception as error:  # noqa: BLE001 -- deliberately broad: any error type must not crash the rest of the batch (VDAP-328 AC)
            record["status"] = "failed"
            record["error"] = str(error)
            status = "failed"
            error_message = str(error)
            _logger.error("%s: lỗi khi transform Silver — %s", source_file, error)

        silver_log_record = build_silver_log_record(
            source_file=source_file,
            run_date=run_date,
            row_count_in=row_count_in,
            row_count_out=row_count_out,
            null_count=null_count,
            dedup_count=dedup_count,
            status=status,
            error_message=error_message,
        )
        logger.info(silver_log_record)
        write_silver_log(silver_log_record, out_dir)

        records.append(record)

    return records
