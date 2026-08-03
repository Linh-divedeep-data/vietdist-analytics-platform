import logging

import pytest

from src.extract import parser


@pytest.fixture(autouse=True)
def _reset_shared_logger():
    logger = logging.getLogger("vietdist")
    logger.handlers.clear()
    yield
    logger.handlers.clear()


def _fake_files():
    return [{"id": f"file-{n:02d}", "name": f"SRC{n:02d}_source.csv", "mimeType": "text/csv"} for n in range(1, 11)]


def test_download_all_sources_returns_10_records_on_happy_path(monkeypatch):
    monkeypatch.setattr(parser, "list_files_in_folder", lambda folder_id: _fake_files())
    monkeypatch.setattr(
        parser, "download_file", lambda file_id, file_name: f"data/raw/{file_name}"
    )

    records = parser.download_all_sources("folder-abc", "batch-123")

    assert len(records) == 10
    for n, record in enumerate(records, start=1):
        assert record == {
            "source_file": f"SRC{n:02d}_source.csv",
            "status": "success",
            "path": f"data/raw/SRC{n:02d}_source.csv",
            "error": None,
        }


def test_download_all_sources_calls_download_file_once_per_file_in_order(monkeypatch):
    monkeypatch.setattr(parser, "list_files_in_folder", lambda folder_id: _fake_files())
    calls = []

    def fake_download_file(file_id, file_name):
        calls.append((file_id, file_name))
        return f"data/raw/{file_name}"

    monkeypatch.setattr(parser, "download_file", fake_download_file)

    parser.download_all_sources("folder-abc", "batch-123")

    assert calls == [(f"file-{n:02d}", f"SRC{n:02d}_source.csv") for n in range(1, 11)]


def test_download_all_sources_logs_through_batch_id(monkeypatch, capsys):
    monkeypatch.setattr(parser, "list_files_in_folder", lambda folder_id: _fake_files())
    monkeypatch.setattr(parser, "download_file", lambda file_id, file_name: f"data/raw/{file_name}")

    parser.download_all_sources("folder-abc", "batch-123")

    output = capsys.readouterr().err
    assert "batch_id=batch-123" in output
    assert output.count("\n") >= 10
