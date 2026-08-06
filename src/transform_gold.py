"""Gold transform entrypoints (Epic Phase 3, VDAP-368) — dim_customers/dim_products build."""

import logging

import polars as pl

from config.sources import PII_COLUMNS_TO_DROP

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
