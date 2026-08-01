# src/extract/unit_of_work/src07_employee_master.py
import polars as pl

from src.extract.parser import read_excel_source
from src.extract.unit_of_work.base import process_source

SOURCE_FILE = "SRC07_employee_master.xlsx"


def run(raw_dir: str, run_date: str, batch_id: str) -> tuple[pl.DataFrame, dict]:
    return process_source(read_excel_source, SOURCE_FILE, raw_dir, run_date, batch_id)
