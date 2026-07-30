# src/extract.py
from src import gdrive_connector
from src.logger import get_logger


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
