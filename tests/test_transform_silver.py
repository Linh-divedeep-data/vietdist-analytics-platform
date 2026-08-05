import logging
import os
from datetime import date

import polars as pl
import pytest

from config.sources import (
    CSV_SOURCES,
    DATE_COLUMNS,
    EXCEL_SOURCES,
    MONEY_QTY_COLUMNS,
    REQUIRED_COLUMNS,
)
from src.extract.parser import SchemaMismatchError
from src.transform_silver import (
    cast_date_columns,
    cast_money_and_qty_columns,
    drop_duplicate_rows,
    drop_null_key_rows,
    fill_null_columns,
    get_silver_output_dir,
    run_silver_transform,
    standardize_text_columns,
    transform_source,
    validate_required_columns,
    write_silver_parquet,
)


def test_validate_required_columns_passes_when_all_required_columns_present():
    df = pl.DataFrame({col: ["x"] for col in REQUIRED_COLUMNS["SRC03_customer_master.csv"]})

    validate_required_columns(df, "SRC03_customer_master.csv")  # must not raise


def test_validate_required_columns_raises_when_one_required_column_missing():
    columns = REQUIRED_COLUMNS["SRC03_customer_master.csv"].copy()
    columns.remove("phone")
    df = pl.DataFrame({col: ["x"] for col in columns})

    with pytest.raises(SchemaMismatchError) as exc_info:
        validate_required_columns(df, "SRC03_customer_master.csv")

    error = exc_info.value
    assert error.source_file == "SRC03_customer_master.csv"
    assert error.missing_cols == ["phone"]
    assert "phone" in str(error)
    assert "SRC03_customer_master.csv" in str(error)


def test_validate_required_columns_logs_warning_before_raising_on_missing_column(caplog):
    columns = REQUIRED_COLUMNS["SRC03_customer_master.csv"].copy()
    columns.remove("phone")
    df = pl.DataFrame({col: ["x"] for col in columns})

    with caplog.at_level(logging.WARNING), pytest.raises(SchemaMismatchError):
        validate_required_columns(df, "SRC03_customer_master.csv")

    assert "SRC03_customer_master.csv" in caplog.text
    assert "phone" in caplog.text
    assert "Bronze" in caplog.text


def test_cast_money_and_qty_columns_casts_plain_numeric_string_to_float64():
    df = pl.DataFrame({"net_amount": ["908000.0", "2950000.0"]})

    result = cast_money_and_qty_columns(df, ["net_amount"])

    assert result.schema["net_amount"] == pl.Float64
    assert result["net_amount"].to_list() == [908000.0, 2950000.0]


def test_cast_money_and_qty_columns_strips_thousand_separator_commas():
    df = pl.DataFrame({"budget_vnd": ["1,000,000", "278,000,000"]})

    result = cast_money_and_qty_columns(df, ["budget_vnd"])

    assert result.schema["budget_vnd"] == pl.Float64
    assert result["budget_vnd"].to_list() == [1000000.0, 278000000.0]


def test_cast_money_and_qty_columns_only_touches_listed_columns():
    df = pl.DataFrame({"net_amount": ["1000"], "status": ["success"]})

    result = cast_money_and_qty_columns(df, ["net_amount"])

    assert result.schema["net_amount"] == pl.Float64
    assert result.schema["status"] == pl.String
    assert result["status"].to_list() == ["success"]


def test_cast_money_and_qty_columns_casts_multiple_columns_in_one_call():
    df = pl.DataFrame({"quantity": ["109"], "unit_price": ["8,500"]})

    result = cast_money_and_qty_columns(df, ["quantity", "unit_price"])

    assert result.schema["quantity"] == pl.Float64
    assert result.schema["unit_price"] == pl.Float64
    assert result["quantity"].to_list() == [109.0]
    assert result["unit_price"].to_list() == [8500.0]


def test_cast_date_columns_casts_csv_source_order_date_to_pl_date():
    df = pl.DataFrame({"order_date": ["2024-08-22", "2024-12-28"]})

    result = cast_date_columns(df, ["order_date"], "SRC01_sales_transactions.csv")

    assert result.schema["order_date"] == pl.Date
    assert result["order_date"].to_list() == [date(2024, 8, 22), date(2024, 12, 28)]


def test_cast_date_columns_casts_excel_source_order_date_to_pl_date():
    df = pl.DataFrame({"order_date": ["2024-01-13", "2024-01-14"]})

    result = cast_date_columns(df, ["order_date"], "SRC05_distributor_orders.xlsx")

    assert result.schema["order_date"] == pl.Date
    assert result["order_date"].to_list() == [date(2024, 1, 13), date(2024, 1, 14)]


def test_cast_date_columns_sets_null_for_unparseable_row_instead_of_raising():
    df = pl.DataFrame({"order_date": ["2024-08-22", "not-a-date", "2024-12-28"]})

    result = cast_date_columns(df, ["order_date"], "SRC01_sales_transactions.csv")

    assert result["order_date"].to_list() == [date(2024, 8, 22), None, date(2024, 12, 28)]


def test_cast_date_columns_only_touches_listed_columns():
    df = pl.DataFrame({"order_date": ["2024-08-22"], "status": ["success"]})

    result = cast_date_columns(df, ["order_date"], "SRC01_sales_transactions.csv")

    assert result.schema["order_date"] == pl.Date
    assert result.schema["status"] == pl.String


def test_cast_date_columns_logs_warning_when_null_ratio_above_50_percent(caplog):
    df = pl.DataFrame({"order_date": ["not-a-date", "still-not-a-date", "2024-08-22"]})

    with caplog.at_level(logging.WARNING):
        cast_date_columns(df, ["order_date"], "SRC01_sales_transactions.csv")

    assert "order_date" in caplog.text
    assert "SRC01_sales_transactions.csv" in caplog.text


def test_cast_date_columns_does_not_log_warning_when_null_ratio_normal(caplog):
    df = pl.DataFrame({"order_date": ["2024-08-22", "2024-12-28", "2024-01-01"]})

    with caplog.at_level(logging.WARNING):
        cast_date_columns(df, ["order_date"], "SRC01_sales_transactions.csv")

    assert caplog.text == ""


def test_full_cast_pipeline_on_csv_source_leaves_no_string_on_cast_columns():
    money_qty_cols = ["quantity", "unit_price", "discount_pct", "discount_amount", "gross_amount", "net_amount"]
    date_cols = ["order_date"]

    df = pl.DataFrame(
        {
            "order_id": ["ORD0010001"],
            "order_date": ["2024-08-22"],
            "order_month": ["8"],
            "order_quarter": ["3"],
            "order_year": ["2024"],
            "customer_id": ["CUS01590"],
            "region": ["Miền Nam"],
            "province": ["TP.HCM"],
            "channel": ["Modern Trade"],
            "employee_id": ["EMP1079"],
            "product_id": ["PRD0055"],
            "product_category": ["Thực phẩm"],
            "quantity": ["109"],
            "unit_price": ["8,500"],
            "discount_pct": ["2"],
            "discount_amount": ["18,500.0"],
            "gross_amount": ["926,500"],
            "net_amount": ["908,000.0"],
            "delivery_status": ["Delivered"],
            "payment_method": ["Công nợ"],
            "payment_status": ["Paid"],
        }
    )

    validate_required_columns(df, "SRC01_sales_transactions.csv")  # must not raise
    result = cast_money_and_qty_columns(df, money_qty_cols)
    result = cast_date_columns(result, date_cols, "SRC01_sales_transactions.csv")

    for col in money_qty_cols:
        assert result.schema[col] == pl.Float64, f"{col} still not Float64: {result.schema[col]}"
    for col in date_cols:
        assert result.schema[col] == pl.Date, f"{col} still not Date: {result.schema[col]}"

    assert result["net_amount"].to_list() == [908000.0]
    assert result["order_date"].to_list() == [date(2024, 8, 22)]


def test_full_cast_pipeline_on_excel_source_leaves_no_string_on_cast_columns():
    money_qty_cols = [
        "qty_ordered", "qty_delivered", "fill_rate_pct",
        "unit_price_list", "distributor_price", "gross_amount", "delivered_amount",
    ]
    date_cols = ["order_date", "expected_delivery_date", "actual_delivery_date"]

    df = pl.DataFrame(
        {
            "order_id": ["ORD-D001"],
            "order_date": ["2024-01-13"],
            "order_month": ["1"],
            "order_quarter": ["1"],
            "distributor_id": ["DIST0001"],
            "region": ["Miền Bắc"],
            "channel": ["Traditional Trade"],
            "product_id": ["PRD0010"],
            "product_category": ["Đồ uống"],
            "qty_ordered": ["1,000"],
            "qty_delivered": ["950"],
            "fill_rate_pct": ["95"],
            "unit_price_list": ["12,000"],
            "distributor_price": ["10,500"],
            "gross_amount": ["11,400,000"],
            "delivered_amount": ["9,975,000"],
            "expected_delivery_date": ["2024-01-15"],
            "actual_delivery_date": ["2024-01-16"],
            "ontime_delivery": ["false"],
            "delivery_status": ["Delivered"],
            "payment_terms": ["Net 30"],
        }
    )

    validate_required_columns(df, "SRC05_distributor_orders.xlsx")  # must not raise
    result = cast_money_and_qty_columns(df, money_qty_cols)
    result = cast_date_columns(result, date_cols, "SRC05_distributor_orders.xlsx")

    for col in money_qty_cols:
        assert result.schema[col] == pl.Float64, f"{col} still not Float64: {result.schema[col]}"
    for col in date_cols:
        assert result.schema[col] == pl.Date, f"{col} still not Date: {result.schema[col]}"

    assert result["gross_amount"].to_list() == [11400000.0]
    assert result["order_date"].to_list() == [date(2024, 1, 13)]
    assert result["expected_delivery_date"].to_list() == [date(2024, 1, 15)]


def test_standardize_text_columns_strips_leading_and_trailing_whitespace():
    df = pl.DataFrame({"region": ["  Miền Nam  ", "Miền Bắc"]})

    result = standardize_text_columns(df, ["region"])

    assert result["region"].to_list() == ["MIỀN NAM", "MIỀN BẮC"]


def test_standardize_text_columns_uppercases_vietnamese_diacritics():
    df = pl.DataFrame({"channel": ["modern trade", "e-commerce"]})

    result = standardize_text_columns(df, ["channel"])

    assert result["channel"].to_list() == ["MODERN TRADE", "E-COMMERCE"]


def test_standardize_text_columns_only_touches_listed_columns():
    df = pl.DataFrame({"region": [" mien nam "], "customer_id": ["cus00001"]})

    result = standardize_text_columns(df, ["region"])

    assert result["region"].to_list() == ["MIEN NAM"]
    assert result["customer_id"].to_list() == ["cus00001"]


def test_standardize_text_columns_casts_multiple_columns_in_one_call():
    df = pl.DataFrame({"region": [" mien nam "], "status": [" active "]})

    result = standardize_text_columns(df, ["region", "status"])

    assert result["region"].to_list() == ["MIEN NAM"]
    assert result["status"].to_list() == ["ACTIVE"]


def test_drop_duplicate_rows_removes_exact_duplicate_rows():
    df = pl.DataFrame({"customer_id": ["CUS001", "CUS001", "CUS002"], "name": ["A", "A", "B"]})

    result = drop_duplicate_rows(df)

    assert result.shape[0] == 2
    assert result.shape[0] == result.unique().shape[0]


def test_drop_duplicate_rows_leaves_dataframe_unchanged_when_no_duplicates():
    df = pl.DataFrame({"customer_id": ["CUS001", "CUS002"], "name": ["A", "B"]})

    result = drop_duplicate_rows(df)

    assert result.shape[0] == 2
    assert set(result["customer_id"].to_list()) == {"CUS001", "CUS002"}


def test_drop_duplicate_rows_keeps_rows_that_differ_in_only_one_column():
    df = pl.DataFrame({"customer_id": ["CUS001", "CUS001"], "name": ["A", "B"]})

    result = drop_duplicate_rows(df)

    assert result.shape[0] == 2


def test_drop_null_key_rows_drops_row_with_null_in_single_key_column():
    df = pl.DataFrame({"customer_id": ["CUS001", None, "CUS003"], "name": ["A", "B", "C"]})

    result = drop_null_key_rows(df, ["customer_id"])

    assert result["customer_id"].to_list() == ["CUS001", "CUS003"]


def test_drop_null_key_rows_drops_row_with_null_in_any_of_multiple_key_columns():
    df = pl.DataFrame(
        {
            "customer_id": ["CUS001", "CUS002", "CUS003"],
            "product_id": ["PRD001", None, "PRD003"],
        }
    )

    result = drop_null_key_rows(df, ["customer_id", "product_id"])

    assert result["customer_id"].to_list() == ["CUS001", "CUS003"]
    assert result["product_id"].to_list() == ["PRD001", "PRD003"]


def test_drop_null_key_rows_keeps_rows_where_all_key_columns_non_null():
    df = pl.DataFrame({"customer_id": ["CUS001", "CUS002"], "product_id": ["PRD001", "PRD002"]})

    result = drop_null_key_rows(df, ["customer_id", "product_id"])

    assert result.shape[0] == 2


def test_drop_null_key_rows_ignores_null_in_unlisted_column():
    df = pl.DataFrame({"customer_id": ["CUS001", "CUS002"], "notes": [None, "some note"]})

    result = drop_null_key_rows(df, ["customer_id"])

    assert result.shape[0] == 2
    assert result["notes"].to_list() == [None, "some note"]


def test_drop_null_key_rows_matches_parent_acceptance_criteria():
    df = pl.DataFrame({"customer_id": ["CUS001", None, "CUS003"], "product_id": ["PRD001", "PRD002", None]})

    result = drop_null_key_rows(df, ["customer_id", "product_id"])

    assert result["customer_id"].null_count() == 0
    assert result["product_id"].null_count() == 0


def test_drop_null_key_rows_logs_count_of_dropped_rows(caplog):
    df = pl.DataFrame({"customer_id": ["CUS001", None, "CUS003", None]})

    with caplog.at_level(logging.INFO):
        drop_null_key_rows(df, ["customer_id"])

    assert "2" in caplog.text


def test_drop_null_key_rows_does_not_log_when_no_rows_dropped(caplog):
    df = pl.DataFrame({"customer_id": ["CUS001", "CUS002"]})

    with caplog.at_level(logging.INFO):
        drop_null_key_rows(df, ["customer_id"])

    assert caplog.text == ""


def test_drop_duplicate_rows_matches_parent_acceptance_criteria():
    df = pl.DataFrame({"customer_id": ["CUS001", "CUS001", "CUS001"], "name": ["A", "A", "A"]})

    result = drop_duplicate_rows(df)

    assert result.shape[0] == result.unique().shape[0]


def test_fill_null_columns_fills_null_in_single_column_with_given_value():
    df = pl.DataFrame({"tax_code": ["TAX001", None, "TAX003"]})

    result = fill_null_columns(df, ["tax_code"], "UNKNOWN")

    assert result["tax_code"].to_list() == ["TAX001", "UNKNOWN", "TAX003"]


def test_fill_null_columns_only_touches_listed_columns():
    df = pl.DataFrame({"tax_code": [None], "notes": [None]})

    result = fill_null_columns(df, ["tax_code"], "UNKNOWN")

    assert result["tax_code"].to_list() == ["UNKNOWN"]
    assert result["notes"].to_list() == [None]


def test_fill_null_columns_is_idempotent_when_no_null_present():
    df = pl.DataFrame({"tax_code": ["TAX001", "TAX002"]})

    result = fill_null_columns(df, ["tax_code"], "UNKNOWN")

    assert result["tax_code"].to_list() == ["TAX001", "TAX002"]


def test_fill_null_columns_matches_parent_acceptance_criteria():
    df = pl.DataFrame({"tax_code": ["TAX001", None, None, "TAX004"]})

    result = fill_null_columns(df, ["tax_code"], "UNKNOWN")

    assert result.filter(pl.col("tax_code").is_null()).shape[0] == 0


def test_get_silver_output_dir_strips_dashes_from_run_date(tmp_path):
    out_dir = get_silver_output_dir("2026-07-22", silver_dir=str(tmp_path))

    assert out_dir == os.path.join(str(tmp_path), "20260722")


def test_get_silver_output_dir_creates_directory_on_disk(tmp_path):
    out_dir = get_silver_output_dir("2026-07-22", silver_dir=str(tmp_path))

    assert os.path.isdir(out_dir)


def test_get_silver_output_dir_does_not_raise_when_directory_already_exists(tmp_path):
    get_silver_output_dir("2026-07-22", silver_dir=str(tmp_path))

    # must not raise on the second call even though the directory already exists
    get_silver_output_dir("2026-07-22", silver_dir=str(tmp_path))


def test_write_silver_parquet_creates_file_named_after_source(tmp_path):
    df = pl.DataFrame({"customer_id": ["CUS001", "CUS002"]})

    path = write_silver_parquet(df, "SRC03_customer_master", str(tmp_path))

    assert path == os.path.join(str(tmp_path), "SRC03_customer_master.parquet")
    assert os.path.exists(path)


def test_write_silver_parquet_row_count_matches(tmp_path):
    df = pl.DataFrame({"customer_id": ["CUS001", "CUS002", "CUS003"]})

    path = write_silver_parquet(df, "SRC03_customer_master", str(tmp_path))

    assert pl.read_parquet(path).height == 3


def test_write_silver_parquet_ten_sources_produce_ten_files_in_same_dir(tmp_path):
    source_names = [f"SRC0{i}_source" if i < 10 else f"SRC{i}_source" for i in range(1, 11)]
    for name in source_names:
        write_silver_parquet(pl.DataFrame({"x": [1]}), name, str(tmp_path))

    written = os.listdir(tmp_path)
    assert len(written) == 10
    assert set(written) == {f"{name}.parquet" for name in source_names}


def test_transform_source_casts_and_cleans_src01_shaped_fixture():
    df = pl.DataFrame(
        {
            "order_id": ["ORD001", "ORD001", "ORD002"],
            "order_date": ["2024-08-22", "2024-08-22", "2024-08-23"],
            "order_month": ["8", "8", "8"],
            "order_quarter": ["3", "3", "3"],
            "order_year": ["2024", "2024", "2024"],
            "customer_id": ["CUS001", "CUS001", "CUS002"],
            "region": [" mien nam ", " mien nam ", "mien bac"],
            "province": ["TP.HCM", "TP.HCM", "Ha Noi"],
            "channel": ["Modern Trade", "Modern Trade", "Traditional Trade"],
            "employee_id": ["EMP001", "EMP001", "EMP002"],
            "product_id": ["PRD001", "PRD001", "PRD002"],
            "product_category": ["Thuc pham", "Thuc pham", "Do uong"],
            "quantity": ["10", "10", "5"],
            "unit_price": ["1,000", "1,000", "2,000"],
            "discount_pct": ["0", "0", "0"],
            "discount_amount": ["0", "0", "0"],
            "gross_amount": ["10,000", "10,000", "10,000"],
            "net_amount": ["10,000", "10,000", "10,000"],
            "delivery_status": ["Delivered", "Delivered", "Delivered"],
            "payment_method": ["Cash", "Cash", "Cash"],
            "payment_status": ["Paid", "Paid", "Paid"],
        }
    )

    result = transform_source(df, "SRC01_sales_transactions.csv")

    assert result.schema["net_amount"] == pl.Float64
    assert result.schema["order_date"] == pl.Date
    assert result["region"].to_list() == ["MIEN NAM", "MIEN BAC"]
    assert result.shape[0] == 2  # exact duplicate row removed


def test_transform_source_fills_tax_code_for_customer_master():
    df = pl.DataFrame(
        {
            "customer_id": ["CUS001", "CUS002"],
            "customer_name": ["Nguyen Van A", "Tran Thi B"],
            "customer_type": ["retail", "wholesale"],
            "channel": ["Modern Trade", "Traditional Trade"],
            "province": ["TP.HCM", "Ha Noi"],
            "region": ["mien nam", "mien bac"],
            "address": ["123 Le Loi", "456 Tran Phu"],
            "phone": ["0900000001", "0900000002"],
            "tax_code": [None, "TAX002"],
            "join_date": ["2020-01-01", "2020-02-01"],
            "credit_limit": ["1,000,000", "2,000,000"],
            "status": ["active", "active"],
        }
    )

    result = transform_source(df, "SRC03_customer_master.csv")

    assert result["tax_code"].to_list() == ["UNKNOWN", "TAX002"]


def test_transform_source_does_not_apply_tax_code_fill_to_other_sources():
    df = pl.DataFrame({col: ["x"] for col in REQUIRED_COLUMNS["SRC04_product_master.xlsx"]})
    df = df.with_columns(
        pl.lit("1000").alias("unit_price"),
        pl.lit("1000").alias("cost_price"),
        pl.lit("100").alias("weight_gram"),
        pl.lit("2024-01-01").alias("launch_date"),
    )

    result = transform_source(df, "SRC04_product_master.xlsx")

    assert "tax_code" not in result.columns


def test_transform_source_handles_source_with_no_money_qty_columns():
    df = pl.DataFrame(
        {
            "employee_id": ["EMP001"],
            "full_name": ["Nguyen Van A"],
            "gender": ["male"],
            "date_of_birth": ["1990-01-01"],
            "join_date": ["2020-01-01"],
            "position": ["staff"],
            "region": ["mien nam"],
            "team": ["sales"],
            "email": ["a@example.com"],
            "phone": ["0900000001"],
            "status": ["active"],
            "version": ["1"],
            "effective_date": ["2020-01-01"],
            "resign_date": pl.Series([None], dtype=pl.String),
            "transfer_note": pl.Series([None], dtype=pl.String),
        }
    )

    result = transform_source(df, "SRC07_employee_master.xlsx")  # must not raise

    assert result.schema["join_date"] == pl.Date
    assert result["position"].to_list() == ["STAFF"]


def _minimal_valid_bronze_fixture(source_file, *, drop_column=None):
    """Build a 1-row DataFrame satisfying REQUIRED_COLUMNS[source_file], with
    role-appropriate placeholder values so transform_source() doesn't raise."""
    columns = [c for c in REQUIRED_COLUMNS[source_file] if c != drop_column]
    row = {}
    for col in columns:
        if col in MONEY_QTY_COLUMNS.get(source_file, []):
            row[col] = "100"
        elif col in DATE_COLUMNS.get(source_file, []):
            row[col] = "2024-01-01"
        else:
            row[col] = "x"
    return pl.DataFrame({col: [val] for col, val in row.items()})


def test_run_silver_transform_writes_ten_files_for_all_valid_sources(tmp_path):
    bronze_dir = tmp_path / "bronze"
    silver_dir = tmp_path / "silver"
    bronze_date_dir = bronze_dir / "20260804"
    bronze_date_dir.mkdir(parents=True)

    for source_file in CSV_SOURCES + EXCEL_SOURCES:
        source_name = source_file.rsplit(".", 1)[0]
        df = _minimal_valid_bronze_fixture(source_file)
        df.write_parquet(bronze_date_dir / f"{source_name}.parquet")

    records = run_silver_transform("2026-08-04", bronze_dir=str(bronze_dir), silver_dir=str(silver_dir))

    silver_date_dir = silver_dir / "20260804"
    written = [f for f in os.listdir(silver_date_dir) if f.endswith(".parquet")]
    assert len(written) == 10
    assert len(records) == 10
    assert all(r["status"] == "success" for r in records)


def test_run_silver_transform_continues_after_one_source_fails(tmp_path):
    bronze_dir = tmp_path / "bronze"
    silver_dir = tmp_path / "silver"
    bronze_date_dir = bronze_dir / "20260804"
    bronze_date_dir.mkdir(parents=True)

    failing_source = "SRC04_product_master.xlsx"
    for source_file in CSV_SOURCES + EXCEL_SOURCES:
        source_name = source_file.rsplit(".", 1)[0]
        drop_column = "product_id" if source_file == failing_source else None
        df = _minimal_valid_bronze_fixture(source_file, drop_column=drop_column)
        df.write_parquet(bronze_date_dir / f"{source_name}.parquet")

    records = run_silver_transform("2026-08-04", bronze_dir=str(bronze_dir), silver_dir=str(silver_dir))

    silver_date_dir = silver_dir / "20260804"
    written = [f for f in os.listdir(silver_date_dir) if f.endswith(".parquet")]
    assert len(written) == 9  # the 9 valid sources still got written

    statuses = {r["source_file"]: r["status"] for r in records}
    assert statuses[failing_source] == "failed"
    assert sum(1 for s in statuses.values() if s == "success") == 9


def test_run_silver_transform_records_error_message_for_failed_source(tmp_path):
    bronze_dir = tmp_path / "bronze"
    silver_dir = tmp_path / "silver"
    bronze_date_dir = bronze_dir / "20260804"
    bronze_date_dir.mkdir(parents=True)

    failing_source = "SRC04_product_master.xlsx"
    df = _minimal_valid_bronze_fixture(failing_source, drop_column="product_id")
    df.write_parquet(bronze_date_dir / "SRC04_product_master.parquet")

    records = run_silver_transform("2026-08-04", bronze_dir=str(bronze_dir), silver_dir=str(silver_dir))

    failed_record = next(r for r in records if r["source_file"] == failing_source)
    assert failed_record["status"] == "failed"
    assert failed_record["error"] is not None
