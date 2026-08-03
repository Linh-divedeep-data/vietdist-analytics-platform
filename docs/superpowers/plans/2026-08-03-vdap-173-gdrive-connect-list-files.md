# VDAP-173 Google Drive Connect + list_files_in_folder() Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `src/gdrive_connector.py` with `get_drive_service()` (Service Account auth) and `list_files_in_folder(folder_id)` that reliably lists every file in a Drive folder, including folders with more than the ~100-file page size Drive API returns per call.

**Architecture:** Two functions. `get_drive_service()` builds a fresh Drive API client from `credentials.json` each call (no caching, no import-time side effects — needed so tests can import the module without live credentials). `list_files_in_folder(folder_id)` calls `get_drive_service()` internally and loops on `nextPageToken` until Drive stops returning one, accumulating `files(id, name, mimeType)` across every page. `get_folder_id_from_env()` is a separate fail-fast helper for the `if __name__ == "__main__":` entrypoint — it's not inside `list_files_in_folder` because that function's signature takes `folder_id` as a parameter (per the ticket's own Output/Deliverable wording), not read from env internally.

**Tech Stack:** `google-auth` (`google.oauth2.service_account.Credentials`), `googleapiclient.discovery.build`, Drive API v3 `files().list()`.

## Global Constraints

- Technical Steps (VDAP-173, verbatim): `Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)` với scope `drive.readonly`; `build("drive", "v3", credentials=credentials)`; `list_files_in_folder(folder_id)`: query `"'{folder_id}' in parents and trashed=false"`, duyệt hết `nextPageToken`; module-level fail-fast raise `RuntimeError` nếu thiếu `GDRIVE_FOLDER_ID`.
- AC (verbatim): `list_files_in_folder(FOLDER_ID)` trả đúng 10 file (SRC01-SRC10), kể cả khi folder có > 100 file (test bằng pagination giả lập qua monkeypatch).
- File(s): `src/gdrive_connector.py` only. Do NOT modify or delete the existing repo-root `gdrive_connector.py` — that's a teacher-provided learning scaffold with its own separate `download_file()` TODO tracked by a different ticket (`2p0.1.2`), out of scope here.
- Deliberate design fixes vs. the root scaffold (documented, not silent): (1) no eager `drive_service = get_drive_service()` at module level — breaks importability/testability; (2) root file's `list_files_in_folder` doesn't paginate at all (would silently drop files past the first ~100); (3) no fail-fast for missing folder id.
- `GDRIVE_FOLDER_ID` isn't in `.env.example` yet — add it as a placeholder (not a real value; a folder ID isn't a secret, but `.env.example` convention here is placeholders only, matching `GOOGLE_SERVICE_ACCOUNT_JSON`'s existing entry).
- Real end-to-end proof already gathered this session (not part of the automated test suite, but confirms the real API/credentials/folder actually work): running the root scaffold against the real folder (`1or8Z1cuL8pkcRypbv3odkMbhAgpje_lr`) returned exactly 10 files named `SRC01_sales_transactions.csv` … `SRC10_promotion_program.xlsx`. Reuse this same folder ID for Task 1's manual live-verification step — never hardcode it into `src/gdrive_connector.py` itself.

---

### Task 1: `src/gdrive_connector.py` with pagination + fail-fast

**Files:**
- Create: `src/gdrive_connector.py`
- Modify: `.env.example` (add `GDRIVE_FOLDER_ID=` placeholder line)
- Test: `tests/test_gdrive_connector.py`

**Interfaces:**
- Produces: `get_drive_service()` (no args, returns a Drive API v3 resource object), `list_files_in_folder(folder_id: str) -> list[dict]` (each dict has `id`, `name`, `mimeType`), `get_folder_id_from_env() -> str` (raises `RuntimeError` if `GDRIVE_FOLDER_ID` unset/empty).

- [x] **Step 1: Write the failing tests**

Create `tests/test_gdrive_connector.py`:
```python
import pytest

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
```

- [x] **Step 2: Run tests to verify they fail** — confirmed `ImportError: cannot import name 'gdrive_connector' from 'src'`

Run: `uv run pytest tests/test_gdrive_connector.py -v`
Expected: `ModuleNotFoundError: No module named 'src.gdrive_connector'` — file doesn't exist yet.

- [x] **Step 3: Write minimal implementation**

Create `src/gdrive_connector.py`:
```python
"""Google Drive connector (VDAP-173): Service Account auth + list files in a folder.

get_drive_service() builds a fresh client per call (no module-level
caching) so this module can be imported in tests without live
credentials — tests monkeypatch get_drive_service() itself.
"""

import os

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "credentials.json")


def get_drive_service():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(
            f"Không tìm thấy file {SERVICE_ACCOUNT_FILE}. Đặt file ở thư mục gốc dự án "
            "hoặc set GOOGLE_SERVICE_ACCOUNT_JSON trong .env."
        )
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build("drive", "v3", credentials=credentials)


def list_files_in_folder(folder_id: str) -> list[dict]:
    service = get_drive_service()
    query = f"'{folder_id}' in parents and trashed=false"

    files: list[dict] = []
    page_token = None
    while True:
        response = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=page_token,
        ).execute()
        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return files


def get_folder_id_from_env() -> str:
    folder_id = os.getenv("GDRIVE_FOLDER_ID")
    if not folder_id:
        raise RuntimeError(
            "GDRIVE_FOLDER_ID chưa được set trong .env — không biết đọc folder Drive nào."
        )
    return folder_id


if __name__ == "__main__":
    folder_id = get_folder_id_from_env()
    print("Đang lấy danh sách file...")
    files = list_files_in_folder(folder_id)
    print(f"Tìm thấy {len(files)} file(s).")
    for f in files:
        print(f"  {f['name']} ({f['mimeType']})")
```

- [x] **Step 4: Add `GDRIVE_FOLDER_ID` to `.env.example`**

Add a line to `.env.example`:
```
GDRIVE_FOLDER_ID=your-google-drive-folder-id
```

- [x] **Step 5: Run tests to verify they pass** — `4 passed` (plan draft said 5, actual file has 4 test functions, correct count)

Run: `uv run pytest tests/test_gdrive_connector.py -v`
Expected: `5 passed`.

- [x] **Step 6: Run the full suite to confirm no regressions** — `21 passed`, `--collect-only` exit 0

Run: `uv run pytest -q`
Expected: all tests pass (17 existing + 5 new = 22 passed), `uv run pytest --collect-only -q` exits 0.

- [x] **Step 7: Manually verify against the real Google Drive folder** — got exactly 10 files, SRC01_sales_transactions.csv..SRC10_promotion_program.xlsx, matching the root scaffold's earlier live result; fail-fast RuntimeError confirmed with exact message

```bash
GDRIVE_FOLDER_ID=1or8Z1cuL8pkcRypbv3odkMbhAgpje_lr uv run python -c "
from src.gdrive_connector import list_files_in_folder
files = list_files_in_folder('1or8Z1cuL8pkcRypbv3odkMbhAgpje_lr')
print(len(files), 'files')
for f in sorted(files, key=lambda x: x['name']):
    print(f['name'])
"
```
Expected: `10 files`, names `SRC01_sales_transactions.csv` through `SRC10_promotion_program.xlsx` (same 10 real files the root scaffold already confirmed exist in this folder).

Then confirm the fail-fast path works too:
```bash
uv run python -c "
import os
os.environ.pop('GDRIVE_FOLDER_ID', None)
from src.gdrive_connector import get_folder_id_from_env
get_folder_id_from_env()
"
```
Expected: `RuntimeError: GDRIVE_FOLDER_ID chưa được set trong .env — không biết đọc folder Drive nào.`

- [ ] **Step 8: Commit**

```bash
git add src/gdrive_connector.py tests/test_gdrive_connector.py .env.example
git commit -m "feat(VDAP-173): add src/gdrive_connector.py with paginated list_files_in_folder()"
```

---

## Self-Review

**1. Spec coverage:** Technical Steps (Credentials.from_service_account_file + drive.readonly scope, build("drive","v3",...), pagination via nextPageToken, module fail-fast for missing GDRIVE_FOLDER_ID) → Task 1 Step 3. AC (10 real files, pagination past 100 verified via monkeypatch) → Step 1 tests (`test_list_files_in_folder_returns_all_10_files_single_page`, `test_list_files_in_folder_paginates_past_100_files`) + Step 7 live run against the real folder. No gaps.
**2. Placeholder scan:** No TBD/TODO. `your-google-drive-folder-id` in `.env.example` is the standard placeholder convention already used for `GOOGLE_SERVICE_ACCOUNT_JSON`-style entries, not an unfinished step.
**3. Type consistency:** `list_files_in_folder(folder_id: str) -> list[dict]` used identically in tests (fake service returns matching dict shapes) and implementation. `get_folder_id_from_env() -> str` — return type and raise behavior match between the test and the `__main__` block that consumes it.
