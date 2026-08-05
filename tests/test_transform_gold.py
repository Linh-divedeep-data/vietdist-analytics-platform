from datetime import date

import polars as pl

from src.transform_gold import (
    add_is_current_flag,
    add_surrogate_key,
    build_dim_customers,
    build_dim_date,
    build_dim_distributors,
    build_dim_products,
    dedupe_by_business_key,
    drop_lineage_columns,
)


def test_drop_lineage_columns_removes_all_5_lineage_columns():
    df = pl.DataFrame(
        {
            "customer_id": ["CUS0001"],
            "_source_file": ["SRC03_customer_master.csv"],
            "_source_platform": ["gdrive"],
            "_run_date": ["2026-08-04"],
            "_ingested_at": ["2026-08-04T00:00:00"],
            "_batch_id": ["batch-1"],
        }
    )

    result = drop_lineage_columns(df)

    assert result.columns == ["customer_id"]


def test_drop_lineage_columns_is_noop_when_no_lineage_columns_present():
    df = pl.DataFrame({"customer_id": ["CUS0001"]})

    result = drop_lineage_columns(df)

    assert result.columns == ["customer_id"]


def test_add_surrogate_key_starts_at_1_not_0():
    df = pl.DataFrame({"product_id": ["PRD0001", "PRD0002", "PRD0003"]})

    result = add_surrogate_key(df, "product_key")

    assert result["product_key"].to_list() == [1, 2, 3]
    assert result.columns[0] == "product_key"


def test_dedupe_by_business_key_keeps_first_row_and_logs_dropped_count(caplog):
    import logging

    df = pl.DataFrame(
        {
            "product_id": ["PRD0001", "PRD0001", "PRD0002"],
            "product_name": ["gốc", "trùng", "khác"],
        }
    )

    with caplog.at_level(logging.WARNING):
        result = dedupe_by_business_key(df, "product_id")

    assert result.height == 2
    assert "product_id" in caplog.text
    assert "1" in caplog.text


def test_dedupe_by_business_key_does_not_log_when_no_duplicates(caplog):
    import logging

    df = pl.DataFrame({"product_id": ["PRD0001", "PRD0002"]})

    with caplog.at_level(logging.WARNING):
        result = dedupe_by_business_key(df, "product_id")

    assert result.height == 2
    assert caplog.text == ""


def test_build_dim_customers_generates_1_based_surrogate_key():
    df = pl.DataFrame(
        {
            "customer_id": ["CUS0001", "CUS0002"],
            "customer_name": ["An", "Binh"],
        }
    )

    result = build_dim_customers(df)

    assert result["customer_key"].to_list() == [1, 2]


def test_build_dim_customers_dedupes_by_customer_id_keeping_first_row():
    df = pl.DataFrame(
        {
            "customer_id": ["CUS0001", "CUS0001", "CUS0002"],
            "customer_name": ["An (bản gốc)", "An (bản trùng)", "Binh"],
        }
    )

    result = build_dim_customers(df)

    assert result.height == 2
    kept_name = result.filter(pl.col("customer_id") == "CUS0001")["customer_name"].to_list()
    assert kept_name == ["An (bản gốc)"]


def test_build_dim_customers_drops_lineage_columns():
    df = pl.DataFrame(
        {
            "customer_id": ["CUS0001"],
            "customer_name": ["An"],
            "_source_file": ["SRC03_customer_master.csv"],
            "_batch_id": ["batch-1"],
        }
    )

    result = build_dim_customers(df)

    assert "_source_file" not in result.columns
    assert "_batch_id" not in result.columns
    assert "customer_name" in result.columns


def test_build_dim_products_generates_1_based_surrogate_key_and_dedupes_by_product_id():
    df = pl.DataFrame(
        {
            "product_id": ["PRD0001", "PRD0001", "PRD0002"],
            "product_name": ["Sữa tươi (bản gốc)", "Sữa tươi (bản trùng)", "Bánh quy"],
            "_batch_id": ["batch-1", "batch-1", "batch-1"],
        }
    )

    result = build_dim_products(df)

    assert result.height == 2
    assert result["product_key"].to_list() == [1, 2]
    assert "_batch_id" not in result.columns
    kept_name = result.filter(pl.col("product_id") == "PRD0001")["product_name"].to_list()
    assert kept_name == ["Sữa tươi (bản gốc)"]


def test_build_dim_distributors_generates_1_based_surrogate_key_and_dedupes_by_distributor_id():
    df = pl.DataFrame(
        {
            "distributor_id": ["DIST0001", "DIST0001", "DIST0002"],
            "distributor_name": ["Kho A (bản gốc)", "Kho A (bản trùng)", "Kho B"],
            "_batch_id": ["batch-1", "batch-1", "batch-1"],
        }
    )

    result = build_dim_distributors(df)

    assert result.height == 2
    assert result["distributor_key"].to_list() == [1, 2]
    assert "_batch_id" not in result.columns
    kept_name = result.filter(pl.col("distributor_id") == "DIST0001")["distributor_name"].to_list()
    assert kept_name == ["Kho A (bản gốc)"]


def test_build_dim_date_covers_full_min_to_max_range_inclusive():
    df = pl.DataFrame(
        {"order_date": [date(2024, 1, 1), date(2024, 1, 3)]},
    )

    result = build_dim_date(df)

    assert result.height == 3
    assert result["full_date"].to_list() == [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)]


def test_build_dim_date_generates_yyyymmdd_integer_date_key():
    df = pl.DataFrame({"order_date": [date(2024, 1, 1), date(2024, 1, 1)]})

    result = build_dim_date(df)

    assert result["date_key"].to_list() == [20240101]


def test_build_dim_date_derives_year_quarter_month_day():
    df = pl.DataFrame({"order_date": [date(2024, 3, 15), date(2024, 3, 15)]})

    result = build_dim_date(df)

    row = result.row(0, named=True)
    assert row["year"] == 2024
    assert row["quarter"] == 1
    assert row["month"] == 3
    assert row["day"] == 15


def test_build_dim_date_column_order_matches_erd():
    df = pl.DataFrame({"order_date": [date(2024, 1, 1), date(2024, 1, 1)]})

    result = build_dim_date(df)

    assert result.columns == ["date_key", "full_date", "year", "quarter", "month", "day"]


def test_add_is_current_flag_true_when_valid_to_is_null():
    df = pl.DataFrame(
        {
            "employee_id": ["EMP001"],
            "valid_from": [date(2024, 6, 1)],
            "valid_to": [None],
        }
    )

    result = add_is_current_flag(df)

    assert result["is_current"].to_list() == [True]


def test_add_is_current_flag_false_when_valid_to_is_a_future_version_date():
    df = pl.DataFrame(
        {
            "employee_id": ["EMP001"],
            "valid_from": [date(2024, 1, 1)],
            "valid_to": [date(2024, 6, 1)],
        }
    )

    result = add_is_current_flag(df)

    assert result["is_current"].to_list() == [False]


def test_add_is_current_flag_false_for_last_version_of_resigned_employee():
    # AC quan trọng nhất: nhân viên đã nghỉ (valid_to = resign_date, KHÔNG NULL)
    # không được có version nào is_current=True.
    df = pl.DataFrame(
        {
            "employee_id": ["EMP002"],
            "valid_from": [date(2024, 1, 1)],
            "valid_to": [date(2024, 9, 30)],
        }
    )

    result = add_is_current_flag(df)

    assert result["is_current"].to_list() == [False]
