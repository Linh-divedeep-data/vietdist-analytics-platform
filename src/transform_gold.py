"""Gold transform entrypoints (Epic Phase 3, VDAP-368) — dim_customers/dim_products build."""

import logging
import os
import uuid

import polars as pl

from config.settings import GOLD_DIR, SILVER_DIR
from config.sources import PII_COLUMNS_TO_DROP
from src.logger import get_logger
from src.transform_silver import get_silver_output_dir

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


def add_unknown_member(
    df: pl.DataFrame, key_col: str, business_key_col: str, overrides: dict | None = None
) -> pl.DataFrame:
    """Prepend a static 'Unknown Member' row (key_col=-1) so a Fact FK that can't resolve a
    real business key still points at a real Dim row instead of NULL."""
    overrides = overrides or {}
    df = df.with_columns(pl.col(key_col).cast(pl.Int64))

    unknown_values = {}
    for col_name, dtype in df.schema.items():
        if col_name == key_col:
            unknown_values[col_name] = -1
        elif col_name == business_key_col:
            unknown_values[col_name] = "UNKNOWN"
        elif col_name in overrides:
            unknown_values[col_name] = overrides[col_name]
        elif dtype == pl.Utf8:
            unknown_values[col_name] = "Unknown"
        else:
            unknown_values[col_name] = None

    unknown_row = pl.DataFrame([unknown_values], schema=df.schema)
    return pl.concat([unknown_row, df])


def drop_pii_columns(df: pl.DataFrame, dim_name: str) -> pl.DataFrame:
    """Drop this Dim's configured PII columns (phone/address/tax_code/date_of_birth) before Gold write."""
    return df.drop(PII_COLUMNS_TO_DROP[dim_name], strict=False)


def build_dim_customers(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_customers: drop lineage columns, dedupe by customer_id, add customer_key (1-based),
    prepend Unknown Member row (key=-1), drop PII columns."""
    result = drop_lineage_columns(silver_df)
    result = dedupe_by_business_key(result, "customer_id")
    result = add_surrogate_key(result, "customer_key")
    result = add_unknown_member(result, "customer_key", "customer_id")
    return drop_pii_columns(result, "dim_customers")


def build_dim_products(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_products: drop lineage columns, dedupe by product_id, add product_key (1-based),
    prepend Unknown Member row (key=-1)."""
    result = drop_lineage_columns(silver_df)
    result = dedupe_by_business_key(result, "product_id")
    result = add_surrogate_key(result, "product_key")
    return add_unknown_member(result, "product_key", "product_id")


def build_dim_distributors(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_distributors: drop lineage columns, dedupe by distributor_id, add distributor_key
    (1-based), prepend Unknown Member row (key=-1), drop PII columns."""
    result = drop_lineage_columns(silver_df)
    result = dedupe_by_business_key(result, "distributor_id")
    result = add_surrogate_key(result, "distributor_key")
    result = add_unknown_member(result, "distributor_key", "distributor_id")
    return drop_pii_columns(result, "dim_distributors")


def join_employee_asof(df: pl.DataFrame, dim_employees_df: pl.DataFrame, date_col: str) -> pl.DataFrame:
    """As-of join to dim_employees's SCD2 versions: for each employee_id, match the version whose
    [valid_from, valid_to) window contains date_col. No match (wrong employee_id, or date falls on/after
    a resigned version's valid_to) -> employee_key = -1, not NULL."""
    real_versions = (
        dim_employees_df.filter(pl.col("employee_key") != -1)
        .select(["employee_id", "employee_key", "valid_from", "valid_to"])
        .sort("valid_from")
    )
    result = df.sort(date_col).join_asof(
        real_versions, left_on=date_col, right_on="valid_from", by="employee_id", strategy="backward"
    )
    result = result.with_columns(
        pl.when(pl.col("valid_to").is_not_null() & (pl.col(date_col) >= pl.col("valid_to")))
        .then(None)
        .otherwise(pl.col("employee_key"))
        .alias("employee_key")
    )
    return result.with_columns(pl.col("employee_key").fill_null(-1)).drop(["valid_from", "valid_to"])


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


def add_scd2_valid_dates(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Add valid_from/valid_to for SCD2 employee versioning.
    valid_to = next version's effective_date if one exists, else resign_date (NULL if still active) —
    a resigned employee's last version must NOT read as valid forever."""
    sorted_df = silver_df.sort(["employee_id", "effective_date"])
    next_effective_date = pl.col("effective_date").shift(-1).over("employee_id")

    return sorted_df.with_columns(
        pl.col("effective_date").alias("valid_from"),
        pl.coalesce([next_effective_date, pl.col("resign_date")]).alias("valid_to"),
    )


def add_is_current_flag(df: pl.DataFrame) -> pl.DataFrame:
    """Flag the current version per employee. valid_to is already coalesced with resign_date
    (see add_scd2_valid_dates), so is_current only needs valid_to.is_null() — checking
    resign_date separately would be a second source of truth for the same conclusion."""
    return df.with_columns(pl.col("valid_to").is_null().alias("is_current"))


def build_dim_employees(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_employees (SCD2): drop lineage columns, compute valid_from/valid_to + is_current,
    add employee_key (1-based), prepend Unknown Member row (key=-1, is_current=False), drop PII
    columns — 1 employee_id may have several employee_key, one per version."""
    result = drop_lineage_columns(silver_df)
    result = add_scd2_valid_dates(result)
    result = add_is_current_flag(result)
    result = add_surrogate_key(result, "employee_key")
    result = add_unknown_member(result, "employee_key", "employee_id", overrides={"is_current": False})
    return drop_pii_columns(result, "dim_employees")


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


def build_fact_targets(target_silver_df: pl.DataFrame, dim_employees_df: pl.DataFrame) -> pl.DataFrame:
    """Build fact_targets: as-of join employee_key via SCD2 versions using each target's first-of-month
    date as the reference point. Keeps year/month as plain attribute columns — target grain is monthly,
    dim_date's grain is daily, so no date_key (that would be a fake key forcing a grain mismatch)."""
    result = target_silver_df.with_columns(
        pl.date(pl.col("year"), pl.col("month"), 1).alias("_target_date")
    )
    result = join_employee_asof(result, dim_employees_df, "_target_date")
    return result.drop("_target_date")


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


def build_dim_territory(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_territory: drop lineage columns, add territory_key (1-based), prepend Unknown
    Member row (key=-1) — no business-key dedup, each territory_mapping row is its own record."""
    result = drop_lineage_columns(silver_df)
    result = add_surrogate_key(result, "territory_key")
    return add_unknown_member(result, "territory_key", "territory_id")


def build_dim_promotion(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_promotion: drop lineage columns, add promotion_key (1-based), prepend Unknown
    Member row (key=-1) — keeps applicable_products/start_date/end_date as-is for a BI-side
    date-range/business-rule join (no direct FK from any fact table yet)."""
    result = drop_lineage_columns(silver_df)
    result = add_surrogate_key(result, "promotion_key")
    return add_unknown_member(result, "promotion_key", "promotion_id")


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


def get_gold_output_dir(run_date: str, gold_dir: str = GOLD_DIR) -> str:
    """Return (creating if needed) the Gold output directory for a run_date."""
    out_dir = os.path.join(gold_dir, run_date.replace("-", ""))
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def write_gold_parquet(df: pl.DataFrame, table_name: str, out_dir: str) -> str:
    """Write a built Gold table (Dim/Fact/Mart) to out_dir/<table_name>.parquet."""
    path = os.path.join(out_dir, f"{table_name}.parquet")
    df.write_parquet(path)
    return path


def run_gold_transform(
    run_date: str, silver_dir: str = SILVER_DIR, gold_dir: str = GOLD_DIR, batch_id: str | None = None
) -> list[dict]:
    """Build every Dim/Fact/Mart table from Silver output and write them to Gold.
    Unlike Bronze/Silver (independent per-source loops), Gold's 12 tables form one
    dependency chain (dims -> facts -> mart) — a failure anywhere aborts the whole
    batch instead of skipping just one source, reported as a single failed record.
    batch_id is optional (mirrors run_silver_transform) — a fresh uuid4 is generated
    here when the caller doesn't supply one, purely to stamp the error log line."""
    silver_source_dir = get_silver_output_dir(run_date, silver_dir)
    out_dir = get_gold_output_dir(run_date, gold_dir)

    def read(source_name: str) -> pl.DataFrame:
        return pl.read_parquet(os.path.join(silver_source_dir, f"{source_name}.parquet"))

    try:
        dim_customers = build_dim_customers(read("SRC03_customer_master"))
        dim_products = build_dim_products(read("SRC04_product_master"))
        dim_distributors = build_dim_distributors(read("SRC06_distributor_master"))
        dim_territory = build_dim_territory(read("SRC08_territory_mapping"))
        dim_promotion = build_dim_promotion(read("SRC10_promotion_program"))
        dim_employees = build_dim_employees(read("SRC07_employee_master"))

        sales_silver = read("SRC01_sales_transactions")
        dim_date = build_dim_date(sales_silver)

        fact_sales = build_fact_sales(sales_silver, dim_customers, dim_products, dim_employees, dim_date)
        fact_targets = build_fact_targets(read("SRC02_sales_target_plan"), dim_employees)
        fact_returns = build_fact_returns(read("SRC09_return_transactions"), dim_customers, dim_products, dim_employees)
        fact_distributor_orders = build_fact_distributor_orders(
            read("SRC05_distributor_orders"), dim_distributors, dim_products
        )

        mart_sales_vs_target = add_variance_pct(build_mart_sales_vs_target(fact_sales, fact_targets))

        tables = {
            "dim_customers": dim_customers,
            "dim_products": dim_products,
            "dim_distributors": dim_distributors,
            "dim_date": dim_date,
            "dim_territory": dim_territory,
            "dim_promotion": dim_promotion,
            "dim_employees": dim_employees,
            "fact_sales": fact_sales,
            "fact_targets": fact_targets,
            "fact_returns": fact_returns,
            "fact_distributor_orders": fact_distributor_orders,
            "mart_sales_vs_target": mart_sales_vs_target,
        }
        for table_name, df in tables.items():
            write_gold_parquet(df, table_name, out_dir)

        return [{"table_name": name, "status": "success"} for name in tables]
    except Exception as error:  # noqa: BLE001 -- any failure anywhere in this interdependent chain aborts the whole Gold batch
        get_logger(batch_id or str(uuid.uuid4())).error("Gold layer transform thất bại: %s", error)
        return [{"table_name": "gold_layer", "status": "failed", "error": str(error)}]
