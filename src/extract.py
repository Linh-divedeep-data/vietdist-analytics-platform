# src/extract.py
from src import gdrive_connector


def download_all_sources(folder_id: str) -> list[str]:
    """Tải toàn bộ file trong 1 folder Drive về data/raw, trả về list đường dẫn đã tải."""
    files = gdrive_connector.list_files_in_folder(folder_id)

    downloaded_paths = []
    for file_info in files:
        path = gdrive_connector.download_file(file_info["id"], file_info["name"])
        downloaded_paths.append(path)

    return downloaded_paths