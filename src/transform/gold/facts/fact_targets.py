"""build_fact_targets()."""

import polars as pl

from src.transform.gold.base import join_employee_asof


def build_fact_targets(target_silver_df: pl.DataFrame, dim_employees_df: pl.DataFrame) -> pl.DataFrame:
    """Build fact_targets: as-of join employee_key via SCD2 versions using each target's first-of-month
    date as the reference point. Keeps year/month as plain attribute columns — target grain is monthly,
    dim_date's grain is daily, so no date_key (that would be a fake key forcing a grain mismatch)."""
    result = target_silver_df.with_columns(
        pl.date(pl.col("year"), pl.col("month"), 1).alias("_target_date")
    )
    result = join_employee_asof(result, dim_employees_df, "_target_date")
    return result.drop("_target_date")
