"""build_fact_distributor_orders()."""

import polars as pl


def build_fact_distributor_orders(
    distributor_orders_silver_df: pl.DataFrame,
    dim_distributors_df: pl.DataFrame,
    dim_products_df: pl.DataFrame,
) -> pl.DataFrame:
    """Build fact_distributor_orders: left join distributor_key/product_key (fill_null -1) —
    both dims are simple (non-SCD2) business keys, so a plain left join can't fan out and no
    as-of join is needed. Measures (fill_rate_pct, ontime_delivery) and lineage cols pass through."""
    result = distributor_orders_silver_df.join(
        dim_distributors_df.select(["distributor_id", "distributor_key"]), on="distributor_id", how="left"
    ).with_columns(pl.col("distributor_key").fill_null(-1))
    result = result.join(
        dim_products_df.select(["product_id", "product_key"]), on="product_id", how="left"
    ).with_columns(pl.col("product_key").fill_null(-1))
    return result
