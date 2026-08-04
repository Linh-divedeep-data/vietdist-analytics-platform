"""Silver transform entrypoints (Epic Phase 2) — filled in incrementally by VDAP-309/310/311.

validate_required_columns() (VDAP-309) is a second defensive schema check,
reusing src.extract.parser.validate_schema() so a missing column halts the
Silver transform with the same clear error Bronze already raises, instead of
silently mis-mapping a renamed/dropped column.
"""

import polars as pl

from src.extract.parser import validate_schema


def validate_required_columns(df: pl.DataFrame, source_file: str) -> None:
    """Second defensive check before Silver transform: reuse Bronze's schema validation."""
    validate_schema(df, source_file)
