"""build_fact_sales()."""

import polars as pl

from src.transform.gold.base import join_employee_asof


def build_fact_sales(
    sales_silver_df: pl.DataFrame,
    dim_customers_df: pl.DataFrame,
    dim_products_df: pl.DataFrame,
    dim_employees_df: pl.DataFrame,
    dim_date_df: pl.DataFrame,
) -> pl.DataFrame:
    """Build fact_sales: left join customer_key/product_key (fill_null -1), left join date_key
    (dim_date always matches, no fallback needed), as-of join employee_key via SCD2 versions."""
    result = sales_silver_df.join(
        dim_customers_df.select(["customer_id", "customer_key"]), on="customer_id", how="left"
    ).with_columns(pl.col("customer_key").fill_null(-1))
    result = result.join(
        dim_products_df.select(["product_id", "product_key"]), on="product_id", how="left"
    ).with_columns(pl.col("product_key").fill_null(-1))
    result = result.join(
        dim_date_df.select(["full_date", "date_key"]), left_on="order_date", right_on="full_date", how="left"
    )
    return join_employee_asof(result, dim_employees_df, "order_date")
