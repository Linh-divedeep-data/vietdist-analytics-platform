# src/extract/orchestrator.py
"""Vòng lặp Bronze: chạy từng unit_of_work trong registry, ghi Parquet partition
theo run_date, ghi ingest_log.parquet cùng thư mục (P1.4 + P1.5, xem phase1_bronze_ingestion.md).

Idempotency: partition data/bronze/<run_date>/ (yyyymmdd, bỏ dấu "-"), ghi đè
file bên trong — chạy lại cùng run_date không nhân bản dữ liệu (CLAUDE.md).
"""

import os

from config.settings import BRONZE_DIR, RAW_DIR
from src.extract.ingest_log import build_ingest_log_record, write_ingest_log
from src.extract.registry import UNIT_OF_WORK
from src.logger import get_logger


def _partition_dir(run_date: str, bronze_dir: str) -> str:
    return os.path.join(bronze_dir, run_date.replace("-", ""))


def run_bronze_ingestion(
    run_date: str, batch_id: str, raw_dir: str = RAW_DIR, bronze_dir: str = BRONZE_DIR
) -> list[dict]:
    """Đọc raw_dir qua registry, ghi mỗi nguồn thành 1 file Parquet Bronze + ingest_log.parquet.

    1 nguồn lỗi (đọc/ghi) không crash cả batch — record status=failed trong
    ingest_log, các nguồn còn lại vẫn tiếp tục (cùng pattern download_all_sources).
    """
    logger = get_logger(batch_id)
    out_dir = _partition_dir(run_date, bronze_dir)
    os.makedirs(out_dir, exist_ok=True)

    records = []
    for source_file, run_unit in UNIT_OF_WORK.items():
        try:
            df, record = run_unit(raw_dir, run_date, batch_id)
            out_name = os.path.splitext(source_file)[0] + ".parquet"
            df.write_parquet(os.path.join(out_dir, out_name))
            records.append(record)
        except Exception as e:  # noqa: BLE001 - 1 nguồn lỗi không được làm crash cả batch
            logger.error(f"Bronze write failed for {source_file}: {e}")
            records.append(
                build_ingest_log_record(
                    batch_id=batch_id,
                    source_file=source_file,
                    rows_loaded=0,
                    status="failed",
                    duration_sec=0.0,
                )
            )

    write_ingest_log(records, out_dir)
    return records
