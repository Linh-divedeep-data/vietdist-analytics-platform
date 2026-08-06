"""run_silver_transform(): loop CSV_SOURCES+EXCEL_SOURCES, read data/bronze/<date>/,
call base, write data/silver/<date>/."""

import logging
import os
import uuid

import polars as pl

from config.settings import BRONZE_DIR, SILVER_DIR
from config.sources import CSV_SOURCES, EXCEL_SOURCES
from src.logger import get_logger
from src.transform.silver.base import transform_source_with_stats
from src.transform.silver.steps import _row_count
from src.transform.silver.log import build_silver_log_record, write_silver_log

_logger = logging.getLogger(__name__)


def get_silver_output_dir(run_date: str, silver_dir: str = SILVER_DIR) -> str:
    """Return (creating if needed) the Silver output directory for a run_date."""
    out_dir = os.path.join(silver_dir, run_date.replace("-", ""))
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def write_silver_parquet(df: pl.DataFrame, source_name: str, out_dir: str) -> str:
    """Write a cleaned Silver DataFrame to out_dir/<source_name>.parquet."""
    path = os.path.join(out_dir, f"{source_name}.parquet")
    df.write_parquet(path)
    return path


def run_silver_transform(
    run_date: str,
    bronze_dir: str = BRONZE_DIR,
    silver_dir: str = SILVER_DIR,
    batch_id: str | None = None,
) -> list[dict]:
    """Run every canonical source through transform_source(), writing Silver Parquet.
    One failing source is logged and skipped, not fatal to the batch.

    batch_id is optional (unlike run_bronze_ingestion, which requires it from
    main.py): main.py does not pass one for the silver layer today, so a
    fresh uuid4 is generated here when the caller doesn't supply one, purely
    to stamp get_logger()'s log lines — it is never stored in the silver log
    record itself (VDAP-419 schema deliberately excludes batch_id)."""
    bronze_date_dir = os.path.join(bronze_dir, run_date.replace("-", ""))
    out_dir = get_silver_output_dir(run_date, silver_dir)
    logger = get_logger(batch_id or str(uuid.uuid4()))

    records = []
    for source_file in CSV_SOURCES + EXCEL_SOURCES:
        source_name = source_file.rsplit(".", 1)[0]
        record = {"source_file": source_file, "status": "success", "error": None}

        row_count_in = row_count_out = null_count = dedup_count = 0
        status = "success"
        error_message = None

        try:
            df = pl.scan_parquet(os.path.join(bronze_date_dir, f"{source_name}.parquet"))
            row_count_in = _row_count(df)
            result, stats = transform_source_with_stats(df, source_file)
            row_count_out = stats["row_count_out"]
            dedup_count = stats["dedup_count"]
            null_count = stats["null_count"]
            write_silver_parquet(result, source_name, out_dir)
        except Exception as error:  # noqa: BLE001 -- deliberately broad: any error type must not crash the rest of the batch (VDAP-328 AC)
            record["status"] = "failed"
            record["error"] = str(error)
            status = "failed"
            error_message = str(error)
            _logger.error("%s: lỗi khi transform Silver — %s", source_file, error)

        silver_log_record = build_silver_log_record(
            source_file=source_file,
            run_date=run_date,
            row_count_in=row_count_in,
            row_count_out=row_count_out,
            null_count=null_count,
            dedup_count=dedup_count,
            status=status,
            error_message=error_message,
        )
        logger.info(silver_log_record)
        write_silver_log(silver_log_record, out_dir)

        records.append(record)

    return records
