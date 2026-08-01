# src/extract/__init__.py
"""Bronze extract: giữ nguyên bề mặt API cũ (src.extract.<hàm>) cho code/test gọi vào,
logic thật tách theo trách nhiệm ở parser.py (đọc file) và lineage.py (gắn metadata).
"""

import polars as pl

from src import gdrive_connector
from src.extract.lineage import attach_lineage, cast_to_string
from src.extract.orchestrator import run_bronze_ingestion
from src.extract.parser import (
    download_all_sources,
    read_csv_sources,
    read_excel_sources,
)

__all__ = [
    "attach_lineage",
    "cast_to_string",
    "download_all_sources",
    "gdrive_connector",
    "pl",
    "read_csv_sources",
    "read_excel_sources",
    "run_bronze_ingestion",
]
