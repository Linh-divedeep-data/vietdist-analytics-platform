"""build_dim_employees() — SCD2: add_scd2_valid_dates, add_is_current_flag."""

import polars as pl

from src.transform.gold.base import (
    add_surrogate_key,
    add_unknown_member,
    drop_lineage_columns,
    drop_pii_columns,
)


def add_scd2_valid_dates(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Add valid_from/valid_to for SCD2 employee versioning.
    valid_to = next version's effective_date if one exists, else resign_date (NULL if still active) —
    a resigned employee's last version must NOT read as valid forever."""
    sorted_df = silver_df.sort(["employee_id", "effective_date"])
    next_effective_date = pl.col("effective_date").shift(-1).over("employee_id")

    return sorted_df.with_columns(
        pl.col("effective_date").alias("valid_from"),
        pl.coalesce([next_effective_date, pl.col("resign_date")]).alias("valid_to"),
    )


def add_is_current_flag(df: pl.DataFrame) -> pl.DataFrame:
    """Flag the current version per employee. valid_to is already coalesced with resign_date
    (see add_scd2_valid_dates), so is_current only needs valid_to.is_null() — checking
    resign_date separately would be a second source of truth for the same conclusion."""
    return df.with_columns(pl.col("valid_to").is_null().alias("is_current"))


def build_dim_employees(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_employees (SCD2): drop lineage columns, compute valid_from/valid_to + is_current,
    add employee_key (1-based), prepend Unknown Member row (key=-1, is_current=False), drop PII
    columns — 1 employee_id may have several employee_key, one per version."""
    result = drop_lineage_columns(silver_df)
    result = add_scd2_valid_dates(result)
    result = add_is_current_flag(result)
    result = add_surrogate_key(result, "employee_key")
    result = add_unknown_member(result, "employee_key", "employee_id", overrides={"is_current": False})
    return drop_pii_columns(result, "dim_employees")
