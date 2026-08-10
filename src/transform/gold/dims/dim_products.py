"""build_dim_products()."""

import polars as pl

from src.transform.gold.base import (
    LINEAGE_NULL_OVERRIDES,
    add_audit_columns,
    add_surrogate_key,
    add_unknown_member,
    dedupe_by_business_key,
)


def build_dim_products(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_products: dedupe by product_id, add product_key (1-based), prepend Unknown
    Member row (key=-1, lineage columns NULL), stamp audit columns. Lineage columns are preserved
    for audit/traceability."""
    result = dedupe_by_business_key(silver_df, "product_id")
    result = add_surrogate_key(result, "product_key")
    result = add_unknown_member(result, "product_key", "product_id", overrides=LINEAGE_NULL_OVERRIDES)
    return add_audit_columns(result)
