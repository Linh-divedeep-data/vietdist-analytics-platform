"""build_dim_customers()."""

import polars as pl

from src.transform.gold.base import (
    add_surrogate_key,
    add_unknown_member,
    dedupe_by_business_key,
    drop_lineage_columns,
    drop_pii_columns,
)


def build_dim_customers(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_customers: drop lineage columns, dedupe by customer_id, add customer_key (1-based),
    prepend Unknown Member row (key=-1), drop PII columns."""
    result = drop_lineage_columns(silver_df)
    result = dedupe_by_business_key(result, "customer_id")
    result = add_surrogate_key(result, "customer_key")
    result = add_unknown_member(result, "customer_key", "customer_id")
    return drop_pii_columns(result, "dim_customers")
