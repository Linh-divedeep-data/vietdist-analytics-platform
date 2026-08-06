"""build_fact_returns()."""

import polars as pl

from src.transform.gold.base import join_employee_asof


def build_fact_returns(
    returns_silver_df: pl.DataFrame,
    dim_customers_df: pl.DataFrame,
    dim_products_df: pl.DataFrame,
    dim_employees_df: pl.DataFrame,
) -> pl.DataFrame:
    """Build fact_returns: left join customer_key/product_key (fill_null -1), as-of join employee_key
    via SCD2 versions — plain left join on employee_id would fan out (dim_employees has multiple rows
    per employee_id, one per SCD2 version), so join_employee_asof() is required here, not optional."""
    result = returns_silver_df.join(
        dim_customers_df.select(["customer_id", "customer_key"]), on="customer_id", how="left"
    ).with_columns(pl.col("customer_key").fill_null(-1))
    result = result.join(
        dim_products_df.select(["product_id", "product_key"]), on="product_id", how="left"
    ).with_columns(pl.col("product_key").fill_null(-1))
    return join_employee_asof(result, dim_employees_df, "return_date")
