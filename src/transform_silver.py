"""Silver transform entrypoints (Epic Phase 2) — filled in incrementally by VDAP-309/310/311.

validate_required_columns() (VDAP-309) is a second defensive schema check,
reusing src.extract.parser.validate_schema() so a missing column halts the
Silver transform with the same clear error Bronze already raises, instead of
silently mis-mapping a renamed/dropped column.
"""

import logging

import polars as pl

from config.sources import DATE_FORMAT_BY_SOURCE
from src.extract.parser import SchemaMismatchError, validate_schema

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


def cast_money_and_qty_columns(df: pl.DataFrame, columns: list[str]) -> pl.DataFrame:
    """Strip thousand-separator commas and cast money/quantity columns to Float64."""
    return df.with_columns(
        pl.col(col).str.replace_all(",", "").cast(pl.Float64) for col in columns
    )


def cast_date_columns(df: pl.DataFrame, columns: list[str], source_file: str) -> pl.DataFrame:
    """Cast date columns to pl.Date using DATE_FORMAT_BY_SOURCE, logging the post-parse NULL ratio per column."""
    fmt = DATE_FORMAT_BY_SOURCE[source_file]
    result = df.with_columns(
        pl.col(col).str.strptime(pl.Date, fmt, strict=False) for col in columns
    )

    for col in columns:
        null_ratio = result[col].null_count() / result.height
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


def drop_null_key_rows(df: pl.DataFrame, columns: list[str]) -> pl.DataFrame:
    """Drop rows where any of the given primary-key columns is NULL."""
    return df.filter(pl.all_horizontal(pl.col(col).is_not_null() for col in columns))
