import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.path.exists("credentials.json"),
    reason="src.extract imports src.gdrive_connector, which eagerly authenticates on import (not present in CI)",
)


def test_download_all_sources_calls_download_file_for_every_listed_file(monkeypatch):
    from src import extract

    fake_files = [
        {"id": "id-1", "name": "SRC01_sales_transactions.csv", "mimeType": "text/csv"},
        {"id": "id-2", "name": "SRC02_sales_target_plan.xlsx", "mimeType": "spreadsheetml"},
        {"id": "id-3", "name": "SRC03_customer_master.csv", "mimeType": "text/csv"},
    ]
    download_calls = []

    monkeypatch.setattr(extract.gdrive_connector, "list_files_in_folder", lambda folder_id: fake_files)
    monkeypatch.setattr(
        extract.gdrive_connector,
        "download_file",
        lambda file_id, file_name: download_calls.append((file_id, file_name)) or f"data/raw/{file_name}",
    )

    extract.download_all_sources("fake-folder-id")

    assert download_calls == [
        ("id-1", "SRC01_sales_transactions.csv"),
        ("id-2", "SRC02_sales_target_plan.xlsx"),
        ("id-3", "SRC03_customer_master.csv"),
    ]


def test_download_all_sources_returns_downloaded_paths(monkeypatch):
    from src import extract

    fake_files = [{"id": "id-1", "name": "SRC01_sales_transactions.csv"}]

    monkeypatch.setattr(extract.gdrive_connector, "list_files_in_folder", lambda folder_id: fake_files)
    monkeypatch.setattr(
        extract.gdrive_connector,
        "download_file",
        lambda file_id, file_name: f"data/raw/{file_name}",
    )

    result = extract.download_all_sources("fake-folder-id")

    assert result == ["data/raw/SRC01_sales_transactions.csv"]
