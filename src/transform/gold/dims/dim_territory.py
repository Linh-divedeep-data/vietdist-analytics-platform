"""build_dim_territory()."""

import polars as pl

from src.transform.gold.base import add_surrogate_key, add_unknown_member, drop_lineage_columns


def build_dim_territory(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_territory: drop lineage columns, add territory_key (1-based), prepend Unknown
    Member row (key=-1) — no business-key dedup, each territory_mapping row is its own record."""
    result = drop_lineage_columns(silver_df)
    result = add_surrogate_key(result, "territory_key")
    return add_unknown_member(result, "territory_key", "territory_id")
