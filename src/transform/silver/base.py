"""transform_source_with_stats() — engine shared by every source, equivalent to
process_source() on the Bronze side.

validate_required_columns() (VDAP-309) is a second defensive schema check,
reusing src.extract.parser.validate_schema() so a missing column halts the
Silver transform with the same clear error Bronze already raises, instead of
silently mis-mapping a renamed/dropped column.
"""

import logging

import polars as pl

from config.sources import DATE_COLUMNS, KEY_COLUMNS, MONEY_QTY_COLUMNS, TEXT_COLUMNS
from src.extract.parser import SchemaMismatchError, validate_schema
from src.transform.silver.registry import SOURCE_OVERRIDES
from src.transform.silver.steps import (
    _row_count,
    cast_date_columns,
    cast_money_and_qty_columns,
    drop_duplicate_rows,
    drop_null_key_rows,
    standardize_text_columns,
)

_logger = logging.getLogger(__name__)


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

    for extra_step in SOURCE_OVERRIDES.get(source_file, []):
        result = extra_step(result)

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
