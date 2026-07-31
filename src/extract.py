# src/extract.py
import os

import polars as pl

from src import gdrive_connector
from src.constants import CSV_SOURCES, EXCEL_SOURCES
from src.logger import get_logger


def read_csv_sources(raw_dir: str = "data/raw") -> dict[str, pl.DataFrame]:
    """Đọc 4 nguồn CSV từ raw_dir thành Polars DataFrame, key theo tên file.

    infer_schema_length=0: ép toàn bộ cột thành String ngay lúc đọc, tránh
    ComputeError khi dòng sau không khớp kiểu được suy luận từ vài dòng đầu
    (nguyên tắc fail-safe ingestion của Bronze — xem CLAUDE.md).
    File thiếu/hỏng không được bắt lỗi ở đây — raise tự nhiên lên caller.
    """
    return {
        name: pl.read_csv(os.path.join(raw_dir, name), infer_schema_length=0)
        for name in CSV_SOURCES
    }


def read_excel_sources(raw_dir: str = "data/raw") -> dict[str, pl.DataFrame]:
    """Đọc 6 nguồn Excel từ raw_dir thành Polars DataFrame, key theo tên file.

    pl.read_excel không có infer_schema_length=0 như read_csv, nên ép String
    bằng .cast(pl.String) sau khi đọc — cùng nguyên tắc fail-safe ingestion
    của Bronze (xem CLAUDE.md). File thiếu/hỏng không được bắt lỗi ở đây —
    raise tự nhiên lên caller.

    Thiếu engine đọc Excel (fastexcel) raise ImportError sâu bên trong Polars
    internals, khó hiểu — bắt lại và raise rõ ràng kèm hướng dẫn cài đặt.
    """
    try:
        return {
            name: pl.read_excel(os.path.join(raw_dir, name)).select(pl.all().cast(pl.String))
            for name in EXCEL_SOURCES
        }
    except ImportError as e:
        raise ImportError(
            "Thiếu engine đọc Excel. Chạy `uv add fastexcel` rồi thử lại."
        ) from e


def download_all_sources(folder_id: str, batch_id: str) -> list[dict]:
    """Tải toàn bộ file trong 1 folder Drive về data/raw.

    Trả về list record {source_file, status, path, error} — 1 file lỗi
    không làm crash cả batch, các file còn lại vẫn được tải tiếp. Lỗi
    được log qua get_logger(batch_id) để trace theo batch_id chung của
    cả lần chạy pipeline.
    """
    logger = get_logger(batch_id)
    files = gdrive_connector.list_files_in_folder(folder_id)

    results = []
    for file_info in files:
        source_file = file_info["name"]
        try:
            path = gdrive_connector.download_file(file_info["id"], source_file)
            results.append({"source_file": source_file, "status": "success", "path": path, "error": None})
        except Exception as e:  # noqa: BLE001 - 1 file lỗi (bất kỳ loại nào) không được làm crash cả batch
            logger.error(f"Download failed for {source_file}: {e}")
            results.append({"source_file": source_file, "status": "failed", "path": None, "error": str(e)})

    return results
