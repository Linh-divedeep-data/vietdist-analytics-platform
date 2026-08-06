"""build_mart_sales_vs_target(), add_variance_pct()."""

import polars as pl


def build_mart_sales_vs_target(fact_sales_df: pl.DataFrame, fact_targets_df: pl.DataFrame) -> pl.DataFrame:
    """Build mart_sales_vs_target: actual vs. target revenue by region+year+month. Groups by
    year+month, not month alone (deviates from the literal ticket wording) — fact_targets already
    keeps year/month as separate attrs for grain correctness (see build_fact_targets), and grouping
    by month alone would silently merge same-month-different-year revenue. Full outer join keeps
    region/month combos present on only one side (e.g. sales with no target set) instead of
    dropping them — actual_revenue/target_revenue may be NULL, guarded downstream in variance_pct."""
    actual = (
        fact_sales_df.rename({"order_year": "year", "order_month": "month"})
        .group_by(["region", "year", "month"])
        .agg(pl.col("net_amount").sum().alias("actual_revenue"))
    )
    target = fact_targets_df.group_by(["region", "year", "month"]).agg(
        pl.col("target_revenue").sum().alias("target_revenue")
    )
    return actual.join(target, on=["region", "year", "month"], how="full", coalesce=True)


def add_variance_pct(mart_df: pl.DataFrame) -> pl.DataFrame:
    """Add variance_pct = (actual_revenue - target_revenue) / target_revenue. Guards target_revenue
    NULL or 0 -> variance_pct NULL, short-circuited via pl.when so the division by zero never
    actually executes (no Inf/NaN, no crash) — a region with no target set yet must not sink the
    whole report."""
    return mart_df.with_columns(
        pl.when(pl.col("target_revenue").is_null() | (pl.col("target_revenue") == 0))
        .then(None)
        .otherwise((pl.col("actual_revenue") - pl.col("target_revenue")) / pl.col("target_revenue"))
        .alias("variance_pct")
    )
