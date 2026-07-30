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

    extract.download_all_sources("fake-folder-id", batch_id="test-batch")

    assert download_calls == [
        ("id-1", "SRC01_sales_transactions.csv"),
        ("id-2", "SRC02_sales_target_plan.xlsx"),
        ("id-3", "SRC03_customer_master.csv"),
    ]


def test_download_all_sources_returns_status_record_on_success(monkeypatch):
    from src import extract

    fake_files = [{"id": "id-1", "name": "SRC01_sales_transactions.csv"}]

    monkeypatch.setattr(extract.gdrive_connector, "list_files_in_folder", lambda folder_id: fake_files)
    monkeypatch.setattr(
        extract.gdrive_connector,
        "download_file",
        lambda file_id, file_name: f"data/raw/{file_name}",
    )

    result = extract.download_all_sources("fake-folder-id", batch_id="test-batch")

    assert result == [
        {
            "source_file": "SRC01_sales_transactions.csv",
            "status": "success",
            "path": "data/raw/SRC01_sales_transactions.csv",
            "error": None,
        }
    ]


def test_download_all_sources_continues_after_one_file_fails(monkeypatch):
    from src import extract

    fake_files = [
        {"id": "id-1", "name": "SRC01_sales_transactions.csv"},
        {"id": "id-2", "name": "SRC02_sales_target_plan.xlsx"},
        {"id": "id-3", "name": "SRC03_customer_master.csv"},
    ]

    def fake_download_file(file_id, file_name):
        if file_id == "id-2":
            raise ConnectionError("simulated download failure")
        return f"data/raw/{file_name}"

    monkeypatch.setattr(extract.gdrive_connector, "list_files_in_folder", lambda folder_id: fake_files)
    monkeypatch.setattr(extract.gdrive_connector, "download_file", fake_download_file)

    result = extract.download_all_sources("fake-folder-id", batch_id="test-batch")

    assert [r["source_file"] for r in result] == [
        "SRC01_sales_transactions.csv",
        "SRC02_sales_target_plan.xlsx",
        "SRC03_customer_master.csv",
    ]
    assert [r["status"] for r in result] == ["success", "failed", "success"]


def test_download_all_sources_records_error_message_for_failed_file(monkeypatch):
    from src import extract

    fake_files = [{"id": "bad-id", "name": "SRC02_sales_target_plan.xlsx"}]

    def fake_download_file(file_id, file_name):
        raise ConnectionError("simulated download failure")

    monkeypatch.setattr(extract.gdrive_connector, "list_files_in_folder", lambda folder_id: fake_files)
    monkeypatch.setattr(extract.gdrive_connector, "download_file", fake_download_file)

    result = extract.download_all_sources("fake-folder-id", batch_id="test-batch")

    assert result == [
        {
            "source_file": "SRC02_sales_target_plan.xlsx",
            "status": "failed",
            "path": None,
            "error": "simulated download failure",
        }
    ]


def test_download_all_sources_logs_error_via_get_logger_on_failure(monkeypatch, capsys):
    from src import extract

    fake_files = [{"id": "bad-id", "name": "SRC02_sales_target_plan.xlsx"}]

    def fake_download_file(file_id, file_name):
        raise ConnectionError("simulated download failure")

    monkeypatch.setattr(extract.gdrive_connector, "list_files_in_folder", lambda folder_id: fake_files)
    monkeypatch.setattr(extract.gdrive_connector, "download_file", fake_download_file)

    extract.download_all_sources("fake-folder-id", batch_id="test-batch-123")

    out = capsys.readouterr().out
    assert "[batch_id=test-batch-123]" in out
    assert "SRC02_sales_target_plan.xlsx" in out
    assert "simulated download failure" in out


def test_download_all_sources_does_not_log_on_success(monkeypatch, capsys):
    from src import extract

    fake_files = [{"id": "id-1", "name": "SRC01_sales_transactions.csv"}]

    monkeypatch.setattr(extract.gdrive_connector, "list_files_in_folder", lambda folder_id: fake_files)
    monkeypatch.setattr(
        extract.gdrive_connector,
        "download_file",
        lambda file_id, file_name: f"data/raw/{file_name}",
    )

    extract.download_all_sources("fake-folder-id", batch_id="test-batch")

    out = capsys.readouterr().out
    assert out == ""
