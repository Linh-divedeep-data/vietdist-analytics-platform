"""SRC05 distributor orders — delegates to process_source()."""

import polars as pl

from src.extract import parser
from src.extract.unit_of_work.base import process_source

SOURCE_FILE = "SRC05_distributor_orders.xlsx"


def run(raw_dir: str, run_date: str, batch_id: str) -> tuple[pl.DataFrame | None, dict]:
    """Process SRC05_distributor_orders.xlsx through process_source()."""
    return process_source(parser.read_excel_source, SOURCE_FILE, raw_dir, run_date, batch_id)
