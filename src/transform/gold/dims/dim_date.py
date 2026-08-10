"""build_dim_date()."""

import polars as pl

from src.transform.gold.base import add_audit_columns


def build_dim_date(sales_silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_date: 1 row per calendar day spanning sales_transactions.order_date min..max,
    stamp audit columns. date_key uses the YYYYMMDD integer convention (Kimball), not a
    row-position surrogate key."""
    min_date = sales_silver_df["order_date"].min()
    max_date = sales_silver_df["order_date"].max()
    dates = pl.date_range(min_date, max_date, "1d", eager=True)

    result = (
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
    return add_audit_columns(result)
