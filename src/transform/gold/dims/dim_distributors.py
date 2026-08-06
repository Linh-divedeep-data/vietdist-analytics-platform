"""build_dim_distributors()."""

import polars as pl

from src.transform.gold.base import (
    add_surrogate_key,
    add_unknown_member,
    dedupe_by_business_key,
    drop_lineage_columns,
    drop_pii_columns,
)


def build_dim_distributors(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_distributors: drop lineage columns, dedupe by distributor_id, add distributor_key
    (1-based), prepend Unknown Member row (key=-1), drop PII columns."""
    result = drop_lineage_columns(silver_df)
    result = dedupe_by_business_key(result, "distributor_id")
    result = add_surrogate_key(result, "distributor_key")
    result = add_unknown_member(result, "distributor_key", "distributor_id")
    return drop_pii_columns(result, "dim_distributors")
