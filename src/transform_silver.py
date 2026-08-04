"""Silver transform entrypoints (Epic Phase 2) — filled in incrementally by VDAP-309/310/311.

validate_required_columns() (VDAP-309) is a second defensive schema check,
reusing src.extract.parser.validate_schema() so a missing column halts the
Silver transform with the same clear error Bronze already raises, instead of
silently mis-mapping a renamed/dropped column.
"""

import logging

import polars as pl

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
