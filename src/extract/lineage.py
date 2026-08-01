# src/extract/lineage.py
from datetime import UTC, datetime

import polars as pl


def attach_lineage(df: pl.DataFrame, source_file: str, run_date: str, batch_id: str) -> pl.DataFrame:
    """Gắn 5 cột metadata lineage bắt buộc của Bronze (xem CLAUDE.md).

    _ingested_at lấy tại thời điểm gọi hàm này — mỗi nguồn stamp thời gian
    riêng, chính xác hơn 1 timestamp dùng chung cho cả batch.
    """
    return df.with_columns(
        pl.lit(source_file).alias("_source_file"),
        pl.lit("google_drive").alias("_source_platform"),
        pl.lit(run_date).alias("_run_date"),
        pl.lit(datetime.now(UTC)).alias("_ingested_at"),
        pl.lit(batch_id).alias("_batch_id"),
    )


def cast_to_string(df: pl.DataFrame) -> pl.DataFrame:
    """Ép toàn bộ cột thành String — bắt buộc trước khi ghi Bronze (CLAUDE.md).

    attach_lineage() để lại _ingested_at kiểu Datetime; bước này đóng lại
    invariant all-String của Bronze trước khi ghi Parquet.
    """
    return df.select(pl.all().cast(pl.String))
