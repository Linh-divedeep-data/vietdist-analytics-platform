# VDAP-177 download_all_sources() Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `download_all_sources(folder_id, batch_id)` in `src/extract/parser.py` that lists every file in a Drive folder and downloads each one, returning one record per file so a single call replaces 10 manual `download_file()` calls.

**Architecture:** Thin composition function — no new download/list logic, just wires together `list_files_in_folder` and `download_file` (both already built and tested in VDAP-173/VDAP-175) in a loop, logging through `get_logger(batch_id)`. Deliberately happy-path only: per-file error handling (catching a failure so one bad file doesn't crash the whole batch, `status="failed"`) is a separate open ticket (`vietdist-analytics-platform-2p0.1.4`) — do not add try/except here.

**Tech Stack:** Python loop, `src.gdrive_connector.list_files_in_folder`/`download_file` (VDAP-173/175), `src.logger.get_logger` (VDAP-232).

## Global Constraints

- Technical Steps (VDAP-177, verbatim): loop `files = list_files_in_folder(folder_id)`; for each file, `download_file(file_info["id"], file_info["name"])`, record `status="success"`; log via `get_logger(batch_id)`.
- AC (verbatim): running once downloads exactly 10 files, returns exactly 10 records.
- File(s): `src/extract/parser.py` — per the ticket's own File(s) field, even though this file's current docstring describes CSV/Excel readers (a different, not-yet-built P1.2 concern). Not this ticket's call to relocate; follow the ticket as written.
- Record shape: `{source_file: str, status: str, path: str, error: str | None}`. On this ticket's happy path, `status` is always `"success"`, `error` is always `None` — the `error` field exists in the shape now so `2p0.1.4` (per-file error handling) can populate it later without changing the record's keys.
- Do NOT add try/except around individual `download_file()` calls — that's `2p0.1.4`'s scope, not this ticket's.
- Reuse `list_files_in_folder`/`download_file`/`get_logger` exactly as they exist — no changes to `src/gdrive_connector.py` or `src/logger.py`.

---

### Task 1: `download_all_sources()` happy-path loop

**Files:**
- Modify: `src/extract/parser.py`
- Test: `tests/test_parser.py` (new file — `parser.py` has no dedicated tests yet, only an import-smoke-test in `tests/test_placeholder.py`)

**Interfaces:**
- Consumes: `list_files_in_folder(folder_id: str) -> list[dict]` and `download_file(file_id: str, file_name: str) -> str` (both from `src.gdrive_connector`, VDAP-173/175), `get_logger(batch_id: str) -> logging.LoggerAdapter` (`src.logger`, VDAP-232).
- Produces: `download_all_sources(folder_id: str, batch_id: str) -> list[dict]`, each dict `{source_file, status, path, error}`.

- [x] **Step 1: Write the failing tests**

Create `tests/test_parser.py`:
```python
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
```

- [x] **Step 2: Run tests to verify they fail** — confirmed `AttributeError: ... has no attribute 'list_files_in_folder'` (3 failed)

Run: `uv run pytest tests/test_parser.py -v`
Expected: `AttributeError: module 'src.extract.parser' has no attribute 'download_all_sources'` (and/or `list_files_in_folder`/`download_file` not found as module attributes) — function doesn't exist yet.

- [x] **Step 3: Write minimal implementation**

Replace the content of `src/extract/parser.py`:
```python
"""CSV/Excel readers (read_csv_source, read_excel_source) + validate_schema() — filled in Epic Phase 1.

download_all_sources() (VDAP-177) is the happy-path loop over
list_files_in_folder()/download_file(); per-file error handling
(status="failed" instead of crashing the whole batch) is a separate
ticket (2p0.1.4) — not implemented here.
"""

from src.gdrive_connector import download_file, list_files_in_folder
from src.logger import get_logger


def download_all_sources(folder_id: str, batch_id: str) -> list[dict]:
    logger = get_logger(batch_id)
    files = list_files_in_folder(folder_id)

    records = []
    for file_info in files:
        path = download_file(file_info["id"], file_info["name"])
        logger.info("downloaded %s", file_info["name"])
        records.append(
            {
                "source_file": file_info["name"],
                "status": "success",
                "path": path,
                "error": None,
            }
        )

    return records
```

- [x] **Step 4: Run tests to verify they pass** — `3 passed`

Run: `uv run pytest tests/test_parser.py -v`
Expected: `3 passed`.

- [x] **Step 5: Run the full suite to confirm no regressions** — `27 passed`, `--collect-only` exit 0, `test_src_extract_parser_importable` still green

Run: `uv run pytest -q`
Expected: all tests pass (24 existing + 3 new = 27 passed), `uv run pytest --collect-only -q` exits 0. In particular, `tests/test_placeholder.py::test_src_extract_parser_importable` must still pass — confirms the rewritten `parser.py` still imports cleanly (no import-time side effects/errors).

- [x] **Step 6: Ruff-check the new code** — `All checks passed!`

Run: `uvx ruff check src/extract/parser.py tests/test_parser.py`
Expected: no findings.

- [x] **Step 7: Manually verify against the real Google Drive folder (live, not mocked)** — 10 records, all status success, SRC01-SRC10, error None; cleaned up data/raw/ afterward

```bash
uv run python -c "
from src.extract.parser import download_all_sources
records = download_all_sources('1or8Z1cuL8pkcRypbv3odkMbhAgpje_lr', 'verify-vdap-177')
print(len(records), 'records')
for r in sorted(records, key=lambda x: x['source_file']):
    print(r['source_file'], r['status'], r['path'], r['error'])
"
```
Expected: `10 records`, all `status success`, `source_file` values `SRC01_...` through `SRC10_...`, each `path` pointing at a real file under `data/raw/`, `error None` for all.

Then clean up the 10 real downloaded files (gitignored, but don't leave clutter):
```bash
find data/raw -type f ! -name '.gitkeep' -delete
ls -a data/raw
```
Expected: only `.` `..` `.gitkeep` remain.

- [ ] **Step 8: Commit**

```bash
git add src/extract/parser.py tests/test_parser.py
git commit -m "feat(VDAP-177): add download_all_sources() loop over list_files_in_folder + download_file"
```

---

## Self-Review

**1. Spec coverage:** Technical Steps (loop, download each, status=success, log via get_logger) → Task 1 Step 3. AC (10 files, 10 records) → Step 1's `test_download_all_sources_returns_10_records_on_happy_path` + Step 7's live 10-file run. Scope boundary (no per-file error handling — that's `2p0.1.4`) → explicitly called out in Global Constraints and the function's own docstring comment, so a future reader isn't surprised anything's missing. No gaps.
**2. Placeholder scan:** No TBD/TODO. `error: None` on every record is a real, intentional value (not a stub) — it's what the happy path always produces; `2p0.1.4` will be the ticket that ever sets it to a real error string.
**3. Type consistency:** `download_all_sources(folder_id: str, batch_id: str) -> list[dict]` — record shape `{source_file: str, status: str, path: str, error: str | None}` used identically in implementation and all 3 tests.
