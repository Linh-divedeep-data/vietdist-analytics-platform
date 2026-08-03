"""CSV/Excel readers (read_csv_source, read_excel_source) + validate_schema() — filled in Epic Phase 1.

download_all_sources() (VDAP-177/VDAP-179) loops
list_files_in_folder()/download_file(); a per-file failure is caught
(status="failed") so it doesn't crash the rest of the batch.
"""

from pathlib import Path

import polars as pl

from src.gdrive_connector import download_file, list_files_in_folder
from src.logger import get_logger


def download_all_sources(folder_id: str, batch_id: str) -> list[dict]:
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


def read_csv_source(name: str, raw_dir: str = "data/raw") -> pl.DataFrame:
    path = Path(raw_dir) / name
    return pl.read_csv(path, infer_schema_length=0)
