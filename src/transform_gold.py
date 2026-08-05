"""Gold transform entrypoints (Epic Phase 3, VDAP-368) — dim_customers/dim_products build."""

import logging

import polars as pl

_logger = logging.getLogger(__name__)

_LINEAGE_COLUMNS = ["_source_file", "_source_platform", "_run_date", "_ingested_at", "_batch_id"]


def drop_lineage_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Drop the 5 Bronze/Silver lineage columns (if present) — not needed in a Gold Dimension table."""
    return df.drop(_LINEAGE_COLUMNS, strict=False)


def add_surrogate_key(df: pl.DataFrame, key_col: str) -> pl.DataFrame:
    """Generate a 1-based surrogate key column from row position."""
    return df.with_row_index(name=key_col, offset=1)


def dedupe_by_business_key(df: pl.DataFrame, key_col: str) -> pl.DataFrame:
    """Keep the first row per business key, logging how many duplicate rows were dropped."""
    result = df.unique(subset=[key_col], keep="first", maintain_order=True)
    dropped = df.height - result.height
    if dropped > 0:
        _logger.warning("%s: loại %d dòng trùng business key", key_col, dropped)
    return result


def build_dim_customers(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_customers: drop lineage columns, dedupe by customer_id, add customer_key (1-based)."""
    result = drop_lineage_columns(silver_df)
    result = dedupe_by_business_key(result, "customer_id")
    return add_surrogate_key(result, "customer_key")


def build_dim_products(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_products: drop lineage columns, dedupe by product_id, add product_key (1-based)."""
    result = drop_lineage_columns(silver_df)
    result = dedupe_by_business_key(result, "product_id")
    return add_surrogate_key(result, "product_key")


def build_dim_distributors(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_distributors: drop lineage columns, dedupe by distributor_id, add distributor_key (1-based)."""
    result = drop_lineage_columns(silver_df)
    result = dedupe_by_business_key(result, "distributor_id")
    return add_surrogate_key(result, "distributor_key")


def build_dim_date(sales_silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_date: 1 row per calendar day spanning sales_transactions.order_date min..max.
    date_key uses the YYYYMMDD integer convention (Kimball), not a row-position surrogate key."""
    min_date = sales_silver_df["order_date"].min()
    max_date = sales_silver_df["order_date"].max()
    dates = pl.date_range(min_date, max_date, "1d", eager=True)

    return (
        pl.DataFrame({"full_date": dates})
        .with_columns(
            pl.col("full_date").dt.strftime("%Y%m%d").cast(pl.Int32).alias("date_key"),
            pl.col("full_date").dt.year().alias("year"),
            pl.col("full_date").dt.quarter().alias("quarter"),
            pl.col("full_date").dt.month().alias("month"),
            pl.col("full_date").dt.day().alias("day"),
        )
        .select(["date_key", "full_date", "year", "quarter", "month", "day"])
    )


def add_is_current_flag(df: pl.DataFrame) -> pl.DataFrame:
    """Flag the current version per employee. valid_to is already coalesced with resign_date
    (see add_scd2_valid_dates), so is_current only needs valid_to.is_null() — checking
    resign_date separately would be a second source of truth for the same conclusion."""
    return df.with_columns(pl.col("valid_to").is_null().alias("is_current"))
