"""SRC03 customer master — Silver override: tax_code has no reliable source value, fill with UNKNOWN."""

import polars as pl

from src.transform.silver.steps import fill_null_columns


def apply_customer_master_overrides(df: pl.DataFrame | pl.LazyFrame) -> pl.DataFrame | pl.LazyFrame:
    """SRC03-only Silver step, applied after the 6 standard steps: fill tax_code NULLs with UNKNOWN."""
    return fill_null_columns(df, ["tax_code"], "UNKNOWN")
