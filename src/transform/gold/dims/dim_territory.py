"""build_dim_territory()."""

import polars as pl

from src.transform.gold.base import (
    LINEAGE_NULL_OVERRIDES,
    add_audit_columns,
    add_surrogate_key,
    add_unknown_member,
)


def build_dim_territory(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_territory: add territory_key (1-based), prepend Unknown Member row (key=-1,
    lineage columns NULL), stamp audit columns — no business-key dedup, each territory_mapping
    row is its own record. Lineage columns are preserved for audit/traceability."""
    result = add_surrogate_key(silver_df, "territory_key")
    result = add_unknown_member(result, "territory_key", "territory_id", overrides=LINEAGE_NULL_OVERRIDES)
    return add_audit_columns(result)
