from datetime import UTC, datetime

import polars as pl

from src.extract import lineage


def _sample_df() -> pl.DataFrame:
    return pl.DataFrame({"id": ["1", "2", "3"], "amount": ["100", "200", "300"]})


def test_attach_lineage_adds_five_columns_with_correct_values():
    df = _sample_df()

    result = lineage.attach_lineage(
        df, source_file="SRC01_sales.csv", run_date="2026-08-04", batch_id="batch-123"
    )

    assert result["_source_file"].to_list() == ["SRC01_sales.csv"] * 3
    assert result["_source_platform"].to_list() == ["google_drive"] * 3
    assert result["_run_date"].to_list() == ["2026-08-04"] * 3
    assert result["_batch_id"].to_list() == ["batch-123"] * 3
    assert all(isinstance(v, datetime) for v in result["_ingested_at"].to_list())


def test_attach_lineage_preserves_original_columns_and_row_count():
    df = _sample_df()

    result = lineage.attach_lineage(
        df, source_file="SRC01_sales.csv", run_date="2026-08-04", batch_id="batch-123"
    )

    assert result.height == df.height
    assert result["id"].to_list() == df["id"].to_list()
    assert result["amount"].to_list() == df["amount"].to_list()
    assert set(df.columns).issubset(set(result.columns))
    assert result.width == df.width + 5


def test_attach_lineage_stamps_ingested_at_fresh_per_call():
    df = _sample_df()

    result_1 = lineage.attach_lineage(
        df, source_file="SRC01_sales.csv", run_date="2026-08-04", batch_id="batch-123"
    )
    result_2 = lineage.attach_lineage(
        df, source_file="SRC01_sales.csv", run_date="2026-08-04", batch_id="batch-123"
    )

    assert result_1["_ingested_at"][0] != result_2["_ingested_at"][0]


def test_attach_lineage_ingested_at_is_close_to_now_utc():
    df = _sample_df()
    before = datetime.now(UTC)

    result = lineage.attach_lineage(
        df, source_file="SRC01_sales.csv", run_date="2026-08-04", batch_id="batch-123"
    )

    after = datetime.now(UTC)
    stamped = result["_ingested_at"][0]
    assert before <= stamped <= after
