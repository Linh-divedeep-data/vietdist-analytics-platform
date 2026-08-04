import logging

import polars as pl
import pytest

from config.sources import REQUIRED_COLUMNS
from src.extract.parser import SchemaMismatchError
from src.transform_silver import validate_required_columns


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
