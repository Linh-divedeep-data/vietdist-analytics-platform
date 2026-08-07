"""build_dim_promotion()."""

import polars as pl

from src.transform.gold.base import add_surrogate_key, add_unknown_member, drop_lineage_columns


def build_dim_promotion(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_promotion: drop lineage columns, add promotion_key (1-based), prepend Unknown
    Member row (key=-1) — keeps applicable_products/start_date/end_date as-is for a BI-side
    date-range/business-rule join (no direct FK from any fact table yet)."""
    result = drop_lineage_columns(silver_df)
    result = add_surrogate_key(result, "promotion_key")
    return add_unknown_member(result, "promotion_key", "promotion_id")
