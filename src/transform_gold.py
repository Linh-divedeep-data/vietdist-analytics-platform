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


def build_dim_customers(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_customers: drop lineage columns, dedupe by customer_id, add customer_key (1-based),
    prepend Unknown Member row (key=-1)."""
    result = drop_lineage_columns(silver_df)
    result = dedupe_by_business_key(result, "customer_id")
    result = add_surrogate_key(result, "customer_key")
    return add_unknown_member(result, "customer_key", "customer_id")


def build_dim_products(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_products: drop lineage columns, dedupe by product_id, add product_key (1-based),
    prepend Unknown Member row (key=-1)."""
    result = drop_lineage_columns(silver_df)
    result = dedupe_by_business_key(result, "product_id")
    result = add_surrogate_key(result, "product_key")
    return add_unknown_member(result, "product_key", "product_id")


def build_dim_distributors(silver_df: pl.DataFrame) -> pl.DataFrame:
    """Build dim_distributors: drop lineage columns, dedupe by distributor_id, add distributor_key
    (1-based), prepend Unknown Member row (key=-1)."""
    result = drop_lineage_columns(silver_df)
    result = dedupe_by_business_key(result, "distributor_id")
    result = add_surrogate_key(result, "distributor_key")
    return add_unknown_member(result, "distributor_key", "distributor_id")


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
    add employee_key (1-based) — 1 employee_id may have several employee_key, one per version."""
    result = drop_lineage_columns(silver_df)
    result = add_scd2_valid_dates(result)
    result = add_is_current_flag(result)
    return add_surrogate_key(result, "employee_key")
