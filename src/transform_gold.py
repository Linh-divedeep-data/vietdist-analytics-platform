"""Gold transform entrypoints (Epic Phase 3, VDAP-368) — dim_customers/dim_products build."""

import logging

import polars as pl

_logger = logging.getLogger(__name__)

_LINEAGE_COLUMNS = ["_source_file", "_source_platform", "_run_date", "_ingested_at", "_batch_id"]


def _drop_lineage_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Drop the 5 Bronze/Silver lineage columns (if present) — not needed in a Gold Dimension table."""
    return df.drop(_LINEAGE_COLUMNS, strict=False)


def _add_surrogate_key(df: pl.DataFrame, key_col: str) -> pl.DataFrame:
    """Generate a 1-based surrogate key column from row position."""
    return df.with_row_index(name=key_col, offset=1)


def _dedupe_by_business_key(df: pl.DataFrame, key_col: str) -> pl.DataFrame:
    """Keep the first row per business key, logging how many duplicate rows were dropped."""
    result = df.unique(subset=[key_col], keep="first", maintain_order=True)
    dropped = df.height - result.height
    if dropped > 0:
        _logger.warning("%s: loại %d dòng trùng business key", key_col, dropped)
    return result


def build_dim_customers(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_customers: drop lineage columns, dedupe by customer_id, add customer_key (1-based)."""
    result = _drop_lineage_columns(silver_df)
    result = _dedupe_by_business_key(result, "customer_id")
    return _add_surrogate_key(result, "customer_key")


def build_dim_products(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_products: drop lineage columns, dedupe by product_id, add product_key (1-based)."""
    result = _drop_lineage_columns(silver_df)
    result = _dedupe_by_business_key(result, "product_id")
    return _add_surrogate_key(result, "product_key")
