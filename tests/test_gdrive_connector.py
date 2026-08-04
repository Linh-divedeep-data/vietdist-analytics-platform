import os

import pytest
from googleapiclient.errors import HttpError

from src import gdrive_connector


class _FakeExecutable:
    def __init__(self, response):
        self._response = response

    def execute(self):
        return self._response


class _FakeFilesResource:
    def __init__(self, pages):
        self._pages = pages
        self.calls = []

    def list(self, q, fields, pageToken=None):
        self.calls.append({"q": q, "fields": fields, "pageToken": pageToken})
        page = self._pages[len(self.calls) - 1]
        return _FakeExecutable(page)


class _FakeService:
    def __init__(self, pages):
        self._files_resource = _FakeFilesResource(pages)

    def files(self):
        return self._files_resource


def _src_file(n):
    ext = "csv" if n in (1, 3, 6, 9) else "xlsx"
    return {"id": f"file-{n:02d}", "name": f"SRC{n:02d}_source.{ext}", "mimeType": "application/octet-stream"}


def test_list_files_in_folder_returns_all_10_files_single_page(monkeypatch):
    files_page = {"files": [_src_file(n) for n in range(1, 11)]}
    fake_service = _FakeService(pages=[files_page])
    monkeypatch.setattr(gdrive_connector, "get_drive_service", lambda: fake_service)

    result = gdrive_connector.list_files_in_folder("folder-abc")

    assert len(result) == 10
    assert {f["name"] for f in result} == {f"SRC{n:02d}_source.{'csv' if n in (1, 3, 6, 9) else 'xlsx'}" for n in range(1, 11)}
    assert fake_service._files_resource.calls == [
        {"q": "'folder-abc' in parents and trashed=false", "fields": "nextPageToken, files(id, name, mimeType)", "pageToken": None}
    ]


def test_list_files_in_folder_paginates_past_100_files(monkeypatch):
    page_1 = {
        "files": [{"id": f"file-{n}", "name": f"file-{n}.csv", "mimeType": "text/csv"} for n in range(100)],
        "nextPageToken": "page-2-token",
    }
    page_2 = {
        "files": [{"id": f"file-{n}", "name": f"file-{n}.csv", "mimeType": "text/csv"} for n in range(100, 130)],
    }
    fake_service = _FakeService(pages=[page_1, page_2])
    monkeypatch.setattr(gdrive_connector, "get_drive_service", lambda: fake_service)

    result = gdrive_connector.list_files_in_folder("folder-big")

    assert len(result) == 130
    assert {f["id"] for f in result} == {f"file-{n}" for n in range(130)}
    assert fake_service._files_resource.calls[0]["pageToken"] is None
    assert fake_service._files_resource.calls[1]["pageToken"] == "page-2-token"


def test_get_folder_id_from_env_raises_runtime_error_when_missing(monkeypatch):
    monkeypatch.delenv("GDRIVE_FOLDER_ID", raising=False)

    with pytest.raises(RuntimeError, match="GDRIVE_FOLDER_ID"):
        gdrive_connector.get_folder_id_from_env()


def test_get_folder_id_from_env_returns_value_when_set(monkeypatch):
    monkeypatch.setenv("GDRIVE_FOLDER_ID", "folder-xyz")

    assert gdrive_connector.get_folder_id_from_env() == "folder-xyz"


class _FakeHttpResp:
    def __init__(self, status):
        self.status = status
        self.reason = "error"


def _http_error(status):
    return HttpError(_FakeHttpResp(status), b"")


def test_download_file_succeeds_after_two_retryable_errors(monkeypatch, tmp_path):
    calls = []
    sleeps = []
    monkeypatch.setattr(gdrive_connector, "_sleep", lambda seconds: sleeps.append(seconds))

    def fake_attempt(file_id, destination_path):
        calls.append(file_id)
        if len(calls) < 3:
            raise _http_error(429)
        with open(destination_path, "w") as fh:
            fh.write("id,name\n1,a\n")

    monkeypatch.setattr(gdrive_connector, "_download_attempt", fake_attempt)

    result = gdrive_connector.download_file("file-1", "out.csv", destination_folder=str(tmp_path))

    assert result == os.path.join(str(tmp_path), "out.csv")
    assert os.path.exists(result)
    with open(result) as fh:
        assert fh.read() == "id,name\n1,a\n"
    assert len(calls) == 3
    assert sleeps == [1, 2]


def test_download_file_raises_immediately_on_403_no_retry(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(gdrive_connector, "_sleep", lambda seconds: (_ for _ in ()).throw(AssertionError("should not sleep")))

    def fake_attempt(file_id, destination_path):
        calls.append(file_id)
        raise _http_error(403)

    monkeypatch.setattr(gdrive_connector, "_download_attempt", fake_attempt)

    destination = os.path.join(str(tmp_path), "out.csv")
    with pytest.raises(HttpError):
        gdrive_connector.download_file("file-1", "out.csv", destination_folder=str(tmp_path))

    assert len(calls) == 1
    assert not os.path.exists(destination)


def test_download_file_cleans_up_and_raises_after_exhausting_retries(monkeypatch, tmp_path):
    calls = []
    sleeps = []
    monkeypatch.setattr(gdrive_connector, "_sleep", lambda seconds: sleeps.append(seconds))

    def fake_attempt(file_id, destination_path):
        calls.append(file_id)
        raise _http_error(500)

    monkeypatch.setattr(gdrive_connector, "_download_attempt", fake_attempt)

    destination = os.path.join(str(tmp_path), "out.csv")
    with pytest.raises(HttpError):
        gdrive_connector.download_file("file-1", "out.csv", destination_folder=str(tmp_path))

    assert len(calls) == 3
    assert sleeps == [1, 2]
    assert not os.path.exists(destination)
