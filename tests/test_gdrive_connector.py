import importlib
import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.path.exists("credentials.json"),
    reason="requires a Google Service Account credentials.json (not present in CI)",
)


class FakeFilesResource:
    def __init__(self):
        self.get_media_calls = []

    def get_media(self, fileId):
        self.get_media_calls.append(fileId)
        return "fake-request"


class FakeDriveService:
    def __init__(self):
        self.files_resource = FakeFilesResource()

    def files(self):
        return self.files_resource


class FakeDownloader:
    def __init__(self, fh, request):
        self.fh = fh
        self._chunks = iter([b"col1,col2\n", b"1,2\n"])

    def next_chunk(self):
        chunk = next(self._chunks, None)
        if chunk is None:
            return None, True
        self.fh.write(chunk)
        return None, False


class FailingDownloader:
    def __init__(self, fh, request):
        self.fh = fh
        self.fh.write(b"partial-data-before-crash")

    def next_chunk(self):
        raise ConnectionError("simulated network drop mid-download")


def test_download_file_creates_destination_folder_and_writes_content(tmp_path, monkeypatch):
    from src import gdrive_connector

    fake_service = FakeDriveService()
    monkeypatch.setattr(gdrive_connector, "drive_service", fake_service)
    monkeypatch.setattr(gdrive_connector, "MediaIoBaseDownload", FakeDownloader)

    destination_folder = str(tmp_path / "raw")
    result_path = gdrive_connector.download_file(
        "fake-file-id", "SRC01_sales_transactions.csv", destination_folder=destination_folder
    )

    expected_path = os.path.join(destination_folder, "SRC01_sales_transactions.csv")
    assert result_path == expected_path
    assert os.path.exists(expected_path)
    with open(expected_path, "rb") as fh:
        assert fh.read() == b"col1,col2\n1,2\n"


def test_download_file_calls_get_media_with_correct_file_id(tmp_path, monkeypatch):
    from src import gdrive_connector

    fake_service = FakeDriveService()
    monkeypatch.setattr(gdrive_connector, "drive_service", fake_service)
    monkeypatch.setattr(gdrive_connector, "MediaIoBaseDownload", FakeDownloader)

    gdrive_connector.download_file(
        "the-real-file-id", "SRC01_sales_transactions.csv", destination_folder=str(tmp_path / "raw")
    )

    assert fake_service.files_resource.get_media_calls == ["the-real-file-id"]


def test_download_file_removes_partial_file_on_download_error(tmp_path, monkeypatch):
    from src import gdrive_connector

    fake_service = FakeDriveService()
    monkeypatch.setattr(gdrive_connector, "drive_service", fake_service)
    monkeypatch.setattr(gdrive_connector, "MediaIoBaseDownload", FailingDownloader)

    destination_folder = str(tmp_path / "raw")
    with pytest.raises(ConnectionError):
        gdrive_connector.download_file(
            "fake-file-id", "SRC01_sales_transactions.csv", destination_folder=destination_folder
        )

    expected_path = os.path.join(destination_folder, "SRC01_sales_transactions.csv")
    assert not os.path.exists(expected_path)


def test_folder_id_validation_raises_regardless_of_import_or_main(monkeypatch):
    """Module-level validation must fire on import, not just inside __main__."""
    import dotenv

    from src import gdrive_connector

    original_value = gdrive_connector.FOLDER_ID
    monkeypatch.delenv("GDRIVE_FOLDER_ID", raising=False)
    # load_dotenv() would otherwise silently refill GDRIVE_FOLDER_ID from the
    # real .env on reload (it fills in vars *absent* from os.environ) - patch
    # the real dotenv.load_dotenv so `from dotenv import load_dotenv` re-binds
    # to this no-op when the module re-executes its imports on reload.
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: None)
    try:
        with pytest.raises(RuntimeError, match="GDRIVE_FOLDER_ID"):
            importlib.reload(gdrive_connector)
    finally:
        monkeypatch.setenv("GDRIVE_FOLDER_ID", original_value)
        importlib.reload(gdrive_connector)


def test_list_files_in_folder_follows_pagination(monkeypatch):
    from src import gdrive_connector

    page1 = {
        "files": [{"id": "1", "name": "a.csv", "mimeType": "text/csv"}],
        "nextPageToken": "TOKEN2",
    }
    page2 = {"files": [{"id": "2", "name": "b.csv", "mimeType": "text/csv"}]}

    class FakeExecuteResult:
        def __init__(self, data):
            self._data = data

        def execute(self):
            return self._data

    class FakeFilesResource:
        def __init__(self):
            self.page_tokens_requested = []

        def list(self, q, fields, pageToken=None):
            self.page_tokens_requested.append(pageToken)
            page = page1 if pageToken is None else page2
            return FakeExecuteResult(page)

    class FakeDriveService:
        def __init__(self):
            self.files_resource = FakeFilesResource()

        def files(self):
            return self.files_resource

    fake_service = FakeDriveService()
    monkeypatch.setattr(gdrive_connector, "drive_service", fake_service)

    result = gdrive_connector.list_files_in_folder("folder-x")

    assert result == [
        {"id": "1", "name": "a.csv", "mimeType": "text/csv"},
        {"id": "2", "name": "b.csv", "mimeType": "text/csv"},
    ]
    assert fake_service.files_resource.page_tokens_requested == [None, "TOKEN2"]
