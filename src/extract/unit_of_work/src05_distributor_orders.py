# src/extract/unit_of_work/src05_distributor_orders.py
import polars as pl

from src.extract.parser import read_excel_source
from src.extract.unit_of_work.base import process_source

SOURCE_FILE = "SRC05_distributor_orders.xlsx"


def run(raw_dir: str, run_date: str, batch_id: str) -> tuple[pl.DataFrame, dict]:
    return process_source(read_excel_source, SOURCE_FILE, raw_dir, run_date, batch_id)
