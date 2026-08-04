"""run_bronze_ingestion(): main loop over registry.UNIT_OF_WORK + Parquet write — filled in Epic Phase 1."""

import os

import polars as pl

from config.settings import BRONZE_DIR, RAW_DIR
from src.extract.registry import UNIT_OF_WORK


def get_bronze_output_dir(run_date: str, bronze_dir: str = BRONZE_DIR) -> str:
    out_dir = os.path.join(bronze_dir, run_date.replace("-", ""))
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def write_bronze_parquet(df: pl.DataFrame | None, record: dict, out_dir: str) -> str | None:
    if record["status"] != "success":
        return None
    path = os.path.join(out_dir, f"{record['source_name']}.parquet")
    df.write_parquet(path)
    return path


def run_bronze_ingestion(
    run_date: str, batch_id: str, raw_dir: str = RAW_DIR, bronze_dir: str = BRONZE_DIR
) -> list[dict]:
    out_dir = get_bronze_output_dir(run_date, bronze_dir)
    records = []
    for run_fn in UNIT_OF_WORK.values():
        df, record = run_fn(raw_dir, run_date, batch_id)
        write_bronze_parquet(df, record, out_dir)
        records.append(record)
    return records
