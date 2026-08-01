# src/extract/unit_of_work/src03_customer_master.py
import polars as pl

from src.extract.parser import read_csv_source
from src.extract.unit_of_work.base import process_source

SOURCE_FILE = "SRC03_customer_master.csv"


def run(raw_dir: str, run_date: str, batch_id: str) -> tuple[pl.DataFrame, dict]:
    return process_source(read_csv_source, SOURCE_FILE, raw_dir, run_date, batch_id)
