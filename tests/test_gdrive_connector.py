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
