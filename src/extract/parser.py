"""CSV/Excel readers (read_csv_source, read_excel_source) + validate_schema() — filled in Epic Phase 1.

download_all_sources() (VDAP-177) is the happy-path loop over
list_files_in_folder()/download_file(); per-file error handling
(status="failed" instead of crashing the whole batch) is a separate
ticket (2p0.1.4) — not implemented here.
"""

from src.gdrive_connector import download_file, list_files_in_folder
from src.logger import get_logger


def download_all_sources(folder_id: str, batch_id: str) -> list[dict]:
    logger = get_logger(batch_id)
    files = list_files_in_folder(folder_id)

    records = []
    for file_info in files:
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

    return records
