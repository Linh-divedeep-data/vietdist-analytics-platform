# VDAP-175 download_file() + Retry/Backoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `download_file(file_id, file_name, destination_folder="data/raw")` in `src/gdrive_connector.py` that downloads one Drive file, retrying transient errors (429/500/503, timeouts) with exponential backoff, and never leaves a 0-byte/partial file behind.

**Architecture:** Split into `_download_attempt(file_id, destination_path)` — one real download attempt via `get_media()` + `MediaIoBaseDownload`, and `download_file()` — a retry wrapper around it. Tests monkeypatch `_download_attempt` directly (the same pattern VDAP-173 used for `get_drive_service`), so retry/backoff/cleanup logic is tested without mocking Google's internal HTTP transport, which the library itself doesn't make easy to fake realistically.

**Tech Stack:** `googleapiclient.http.MediaIoBaseDownload`, `googleapiclient.errors.HttpError`, `io.FileIO`, `time.sleep` (via a module-level `_sleep` alias for testability).

## Global Constraints

- Technical Steps (VDAP-175, verbatim): `service.files().get_media(fileId=file_id)` → `MediaIoBaseDownload` writes chunks to `io.FileIO` → retry loop catches `HttpError` (429/500/503) or `TimeoutError`, exponential backoff (1s, 2s, 4s), max 3 attempts; non-retryable errors (403/404) raise immediately; after 3 failed attempts, `os.remove()` the partial file then re-raise.
- AC (verbatim): downloaded file matches original content (row count via `pl.read_csv`/`pl.read_excel` — verified live, not mocked); no 0-byte/partial file left on error; monkeypatched 2×429 then success on 3rd call → returns correct path, no raise; monkeypatched 403 → raises immediately, no retry.
- File(s): `src/gdrive_connector.py` only (extend the file VDAP-173 created — do not create a new file).
- `googleapiclient.errors.HttpError(resp, content, uri=None)` requires `resp.status` (int) and `resp.reason` (str); `content` must be `bytes`. Confirmed by reading the library source: any JSON-parsing exceptions inside `HttpError.__init__` are caught internally, so `content=b""` is always safe — no need to fake a full JSON error body.
- `_cleanup_partial_file` must run after **every** failure, retryable or not — `io.FileIO(path, "wb")` truncates/creates the file the instant it's opened, so even a first-attempt 403 leaves a 0-byte file unless cleaned up.
- `_sleep = time.sleep` at module level (mirrors `MediaIoBaseDownload`'s own `self._sleep = time.sleep` testability pattern) so tests can monkeypatch it and never actually sleep.

---

### Task 1: `download_file()` with retry/backoff

**Files:**
- Modify: `src/gdrive_connector.py`
- Test: `tests/test_gdrive_connector.py` (extend — already has 4 tests from VDAP-173)

**Interfaces:**
- Consumes: `get_drive_service()` (VDAP-173, unchanged).
- Produces: `download_file(file_id: str, file_name: str, destination_folder: str = "data/raw") -> str` (returns the downloaded file's path). `_download_attempt(file_id: str, destination_path: str) -> None` and `_cleanup_partial_file(path: str) -> None` are private helpers, monkeypatch targets for tests.

- [x] **Step 1: Write the failing tests**

Append to `tests/test_gdrive_connector.py`:
```python
import os

from googleapiclient.errors import HttpError


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
```

Note: the fake `_download_attempt` in the success test writes a plain text file directly (not via real `MediaIoBaseDownload`) — this is intentional; these tests exercise `download_file()`'s retry/cleanup logic, not the real chunk-download mechanics (those get exercised by Step 7's live run against the real Drive API).

- [x] **Step 2: Run tests to verify they fail** — `3 failed, 4 passed` (new tests failed with AttributeError on missing download_file/_sleep, existing 4 still green)

Run: `uv run pytest tests/test_gdrive_connector.py -v`
Expected: `AttributeError: module 'src.gdrive_connector' has no attribute 'download_file'` (or similar — the 3 new tests fail, the original 4 still pass since `download_file` doesn't exist yet but isn't imported at module level in a way that breaks collection — confirm by checking the actual error).

- [x] **Step 3: Write minimal implementation**

Add to `src/gdrive_connector.py` (after the existing `get_folder_id_from_env` function, before the `if __name__ == "__main__":` block):
```python
import time

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

_MAX_ATTEMPTS = 3
_RETRYABLE_STATUS_CODES = {429, 500, 503}
_BACKOFF_SECONDS = (1, 2, 4)
_sleep = time.sleep


def _download_attempt(file_id: str, destination_path: str) -> None:
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    with io.FileIO(destination_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()


def _cleanup_partial_file(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)


def download_file(file_id: str, file_name: str, destination_folder: str = "data/raw") -> str:
    os.makedirs(destination_folder, exist_ok=True)
    destination_path = os.path.join(destination_folder, file_name)

    for attempt in range(_MAX_ATTEMPTS):
        try:
            _download_attempt(file_id, destination_path)
            return destination_path
        except HttpError as error:
            _cleanup_partial_file(destination_path)
            is_last_attempt = attempt == _MAX_ATTEMPTS - 1
            if error.resp.status not in _RETRYABLE_STATUS_CODES or is_last_attempt:
                raise
            _sleep(_BACKOFF_SECONDS[attempt])
        except TimeoutError:
            _cleanup_partial_file(destination_path)
            if attempt == _MAX_ATTEMPTS - 1:
                raise
            _sleep(_BACKOFF_SECONDS[attempt])
```

Also add `import io` at the top of the file if not already present (it isn't — the VDAP-173 version of this file doesn't need `io` yet).

- [x] **Step 4: Run tests to verify they pass** — `7 passed`

Run: `uv run pytest tests/test_gdrive_connector.py -v`
Expected: `7 passed` (4 from VDAP-173 + 3 new).

- [x] **Step 5: Run the full suite to confirm no regressions** — `24 passed`, `--collect-only` exit 0

Run: `uv run pytest -q`
Expected: all tests pass (21 existing + 3 new = 24 passed), `uv run pytest --collect-only -q` exits 0.

- [x] **Step 6: Ruff-check the new code** — `All checks passed!`

Run: `uvx ruff check src/gdrive_connector.py`
Expected: no new findings introduced by this change (pre-existing findings in this file, if any, are tracked separately by bd `8op.3.3` and out of scope here).

- [x] **Step 7: Manually verify against the real Google Drive file (live, not mocked)** — downloaded SRC01_sales_transactions.csv for real, 119,101 rows, 21 columns, valid CSV; deleted afterward

```bash
GDRIVE_FOLDER_ID=1or8Z1cuL8pkcRypbv3odkMbhAgpje_lr uv run python -c "
from src.gdrive_connector import list_files_in_folder, download_file
import polars as pl

files = list_files_in_folder('1or8Z1cuL8pkcRypbv3odkMbhAgpje_lr')
src01 = next(f for f in files if f['name'].startswith('SRC01'))
path = download_file(src01['id'], src01['name'])
print('downloaded to:', path)

df = pl.read_csv(path)
print('rows:', df.height, 'cols:', df.columns)
assert df.height > 0
"
```
Expected: prints a real path under `data/raw/`, then a row count > 0 and real column names from `SRC01_sales_transactions.csv` — proves the real chunked download (via actual `MediaIoBaseDownload`, not the mocked `_download_attempt`) produces a valid, fully-written, parseable file.

Clean up the downloaded file afterward (it's gitignored, but no need to leave clutter):
```bash
rm -f data/raw/SRC01_sales_transactions.csv
```

- [ ] **Step 8: Commit**

```bash
git add src/gdrive_connector.py tests/test_gdrive_connector.py
git commit -m "feat(VDAP-175): add download_file() with retry/backoff for transient Drive errors"
```

---

## Self-Review

**1. Spec coverage:** Technical Steps 1-2 (get_media + MediaIoBaseDownload chunks) → `_download_attempt` in Step 3, exercised live in Step 7. Technical Step 3 (retry loop, retryable vs non-retryable status codes, backoff) → `download_file`'s try/except in Step 3, unit-tested in Step 1 (all 3 new tests). Technical Step 4 (cleanup on final failure) → `_cleanup_partial_file`, tested in `test_download_file_cleans_up_and_raises_after_exhausting_retries` AND in the 403 no-retry test (cleanup must fire there too, since a partial file exists even without any retries). AC's "file content matches original, row count via polars" → Step 7 live run. No gaps.
**2. Placeholder scan:** No TBD/TODO. No stub functions — `_download_attempt`'s real implementation is the actual Google API call sequence from the Technical Steps, not a placeholder.
**3. Type consistency:** `download_file(file_id: str, file_name: str, destination_folder: str = "data/raw") -> str` matches the ticket's own Output/Deliverable signature exactly. `_download_attempt(file_id: str, destination_path: str) -> None` and `_cleanup_partial_file(path: str) -> None` are used identically between the implementation and the monkeypatched test doubles (same parameter names/order).
