import logging

import polars as pl
import pytest

from config.sources import REQUIRED_COLUMNS
from src.extract.parser import SchemaMismatchError
from src.transform_silver import cast_money_and_qty_columns, validate_required_columns


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
