"""SRC06 distributor master — delegates to process_source()."""

import polars as pl

from src.extract import parser
from src.extract.unit_of_work.base import process_source

SOURCE_FILE = "SRC06_distributor_master.csv"


def run(raw_dir: str, run_date: str, batch_id: str) -> tuple[pl.DataFrame | None, dict]:
    """Process SRC06_distributor_master.csv through process_source()."""
    return process_source(parser.read_csv_source, SOURCE_FILE, raw_dir, run_date, batch_id)
