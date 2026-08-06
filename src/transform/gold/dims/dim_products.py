"""build_dim_products()."""

import polars as pl

from src.transform.gold.base import add_surrogate_key, add_unknown_member, dedupe_by_business_key, drop_lineage_columns


def build_dim_products(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_products: drop lineage columns, dedupe by product_id, add product_key (1-based),
    prepend Unknown Member row (key=-1)."""
    result = drop_lineage_columns(silver_df)
    result = dedupe_by_business_key(result, "product_id")
    result = add_surrogate_key(result, "product_key")
    return add_unknown_member(result, "product_key", "product_id")
