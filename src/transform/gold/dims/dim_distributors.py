"""build_dim_distributors()."""

import polars as pl

from src.transform.gold.base import (
    LINEAGE_NULL_OVERRIDES,
    add_audit_columns,
    add_surrogate_key,
    add_unknown_member,
    dedupe_by_business_key,
    drop_pii_columns,
)


def build_dim_distributors(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_distributors: dedupe by distributor_id, add distributor_key (1-based), prepend
    Unknown Member row (key=-1, lineage columns NULL), drop PII columns, stamp audit columns.
    Lineage columns are preserved for audit/traceability."""
    result = dedupe_by_business_key(silver_df, "distributor_id")
    result = add_surrogate_key(result, "distributor_key")
    result = add_unknown_member(
        result, "distributor_key", "distributor_id", overrides=LINEAGE_NULL_OVERRIDES
    )
    result = drop_pii_columns(result, "dim_distributors")
    return add_audit_columns(result)
