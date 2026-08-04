"""SRC09 return transactions — delegates to process_source()."""

import polars as pl

from src.extract import parser
from src.extract.unit_of_work.base import process_source

SOURCE_FILE = "SRC09_return_transactions.csv"


def run(raw_dir: str, run_date: str, batch_id: str) -> tuple[pl.DataFrame | None, dict]:
    return process_source(parser.read_csv_source, SOURCE_FILE, raw_dir, run_date, batch_id)
