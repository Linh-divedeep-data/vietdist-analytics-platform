"""build_dim_promotion()."""

import polars as pl

from src.transform.gold.base import (
    LINEAGE_NULL_OVERRIDES,
    add_audit_columns,
    add_surrogate_key,
    add_unknown_member,
)


def build_dim_promotion(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_promotion: add promotion_key (1-based), prepend Unknown Member row (key=-1,
    lineage columns NULL), stamp audit columns — keeps applicable_products/start_date/end_date
    as-is for a BI-side date-range/business-rule join (no direct FK from any fact table yet).
    Lineage columns are preserved for audit/traceability."""
    result = add_surrogate_key(silver_df, "promotion_key")
    result = add_unknown_member(result, "promotion_key", "promotion_id", overrides=LINEAGE_NULL_OVERRIDES)
    return add_audit_columns(result)
