"""Helpers shared across Gold dims/facts: add_surrogate_key,
dedupe_by_business_key, add_unknown_member, add_audit_columns, drop_pii_columns,
join_employee_asof."""

import logging
from datetime import UTC, datetime

import polars as pl

from config.sources import PII_COLUMNS_TO_DROP

_logger = logging.getLogger(__name__)

AUDIT_ACTOR = "gold_pipeline"

# Unknown Member row overrides for add_unknown_member(): without these, the 4 Utf8 lineage
# columns default to the string "Unknown" (easy to mistake for a real audit value); _ingested_at
# is already NULL by default since it's a Datetime column, not Utf8.
LINEAGE_NULL_OVERRIDES = {
    "_source_file": None,
    "_source_platform": None,
    "_run_date": None,
    "_batch_id": None,
}


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


def add_audit_columns(df: pl.DataFrame, now: datetime | None = None) -> pl.DataFrame:
    """Stamp created_at/created_by/updated_at/updated_by on every row. Gold fully rebuilds each
    Dim/Fact from Silver every run (no upsert/merge), so created_at and updated_at are always the
    same build-time timestamp — there's no prior state to diff against to know what "really"
    changed. created_by/updated_by are a fixed pipeline identifier, not a real per-row actor."""
    now = now or datetime.now(UTC)
    return df.with_columns(
        pl.lit(now).alias("created_at"),
        pl.lit(AUDIT_ACTOR).alias("created_by"),
        pl.lit(now).alias("updated_at"),
        pl.lit(AUDIT_ACTOR).alias("updated_by"),
    )


def drop_pii_columns(df: pl.DataFrame, dim_name: str) -> pl.DataFrame:
    """Drop this Dim's configured PII columns (phone/address/tax_code/date_of_birth) before Gold write."""
    return df.drop(PII_COLUMNS_TO_DROP[dim_name], strict=False)


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
