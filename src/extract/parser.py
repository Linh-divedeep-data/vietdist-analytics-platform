"""CSV/Excel readers (read_csv_source, read_excel_source) + validate_schema() — filled in Epic Phase 1.

download_all_sources() (VDAP-177/VDAP-179) loops
list_files_in_folder()/download_file(); a per-file failure is caught
(status="failed") so it doesn't crash the rest of the batch.
"""

import logging
from pathlib import Path

import polars as pl

from config.settings import RAW_DIR
from config.sources import REQUIRED_COLUMNS
from src.gdrive_connector import download_file, list_files_in_folder
from src.logger import get_logger

_logger = logging.getLogger(__name__)


def download_all_sources(folder_id: str, batch_id: str) -> list[dict]:
    """Download every file in a Drive folder, recording success/failure per file."""
    logger = get_logger(batch_id)
    files = list_files_in_folder(folder_id)

    records = []
    for file_info in files:
        try:
            path = download_file(file_info["id"], file_info["name"])
            logger.info("downloaded %s", file_info["name"])
            records.append(
                {
                    "source_file": file_info["name"],
                    "status": "success",
                    "path": path,
                    "error": None,
                }
            )
        except Exception as error:  # noqa: BLE001 -- deliberately broad: any error type must not crash the rest of the batch (VDAP-179 AC)
            logger.error("failed to download %s: %s", file_info["name"], error)
            records.append(
                {
                    "source_file": file_info["name"],
                    "status": "failed",
                    "path": None,
                    "error": str(error),
                }
            )

    return records


def read_csv_source(name: str, raw_dir: str = RAW_DIR) -> pl.DataFrame:
    """Read a CSV source file, keeping every column as raw string."""
    path = Path(raw_dir) / name
    return pl.read_csv(path, infer_schema_length=0)


def read_excel_source(name: str, raw_dir: str = RAW_DIR) -> pl.DataFrame:
    """Read an Excel source file, casting every column to string."""
    path = Path(raw_dir) / name
    try:
        df = pl.read_excel(path)
    except ImportError as error:
        raise ImportError(
            f"Missing Excel engine to read {path} — run `uv add fastexcel`"
        ) from error
    return df.select(pl.all().cast(pl.String))


class SchemaMismatchError(Exception):
    def __init__(self, source_file: str, missing_cols: list[str], extra_cols: list[str]):
        """Store the offending source_file and its missing/extra columns for the error message."""
        self.source_file = source_file
        self.missing_cols = missing_cols
        self.extra_cols = extra_cols
        super().__init__(
            f"{source_file}: missing required column(s) {missing_cols}"
        )


def validate_schema(df: pl.DataFrame, source_file: str) -> None:
    """Raise SchemaMismatchError if df is missing any of source_file's required columns."""
    required = set(REQUIRED_COLUMNS[source_file])
    actual = set(df.columns)

    missing_cols = sorted(required - actual)
    extra_cols = sorted(actual - required)

    if extra_cols:
        _logger.warning(
            "%s: unexpected extra column(s) %s (not in REQUIRED_COLUMNS)",
            source_file,
            extra_cols,
        )

    if missing_cols:
        raise SchemaMismatchError(source_file, missing_cols, extra_cols)
