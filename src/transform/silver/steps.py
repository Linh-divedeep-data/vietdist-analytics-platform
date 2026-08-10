"""6 standard Silver cleaning steps, plus the row/null-count helpers they and base.py share."""

import logging

import polars as pl

from config.sources import DATE_FORMAT_BY_SOURCE

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
