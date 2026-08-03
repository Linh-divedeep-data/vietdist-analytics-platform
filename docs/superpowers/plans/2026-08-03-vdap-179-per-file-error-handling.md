# VDAP-179 Per-File Error Handling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One file failing to download (network error, permission error, etc.) inside `download_all_sources()` must not crash the whole batch — the other 9 files should still download normally, and the failed one gets a `status="failed"` record instead of an unhandled exception.

**Architecture:** Wrap the existing `download_file()` call inside `download_all_sources()`'s loop (VDAP-177) in `try/except Exception`. On success, unchanged behavior. On failure: `logger.error(...)`, append a `status="failed"` record with `error=str(e)` and `path=None`, do not re-raise, continue to the next file.

**Tech Stack:** Python `try/except Exception`.

## Global Constraints

- Technical Steps (VDAP-179, verbatim): wrap `download_file()` in try/except; on error, `logger.error(...)`, append `status="failed"` record; do NOT re-raise — loop continues to the next file.
- AC (verbatim): simulate 1/10 file failing (`monkeypatch` raising `ConnectionError`) → the other 9 remain `status="success"`, still exactly 10 records, no exception escapes `download_all_sources()`.
- File(s): `src/extract/parser.py` — modify the `download_all_sources()` VDAP-177 already added, do not create a new file.
- `path` on a failed record: the ticket doesn't specify a value; `None` is the correct choice since no file was actually written for that source.
- Do not touch `_download_attempt`/retry logic inside `src/gdrive_connector.py` (VDAP-175) — that's a separate, lower-level retry mechanism for *transient* errors within one download; this ticket's try/except is a *different* layer, catching whatever `download_file()` ultimately raises (after its own retries are exhausted) so one bad source doesn't take down the other 9.

---

### Task 1: try/except around `download_file()` in the loop

**Files:**
- Modify: `src/extract/parser.py`
- Test: `tests/test_parser.py` (extend — already has 3 tests from VDAP-177)

**Interfaces:**
- Consumes: `download_all_sources(folder_id: str, batch_id: str) -> list[dict]` (VDAP-177, signature unchanged).
- Produces: same signature; record shape unchanged (`{source_file, status, path, error}`), but `status` can now be `"failed"` with `path=None`, `error=<message>` in addition to the existing `"success"` case.

- [x] **Step 1: Write the failing test**

Append to `tests/test_parser.py`:
```python
def test_download_all_sources_continues_after_one_file_fails(monkeypatch, capsys):
    monkeypatch.setattr(parser, "list_files_in_folder", lambda folder_id: _fake_files())

    def fake_download_file(file_id, file_name):
        if file_id == "file-05":
            raise ConnectionError("network unreachable")
        return f"data/raw/{file_name}"

    monkeypatch.setattr(parser, "download_file", fake_download_file)

    records = parser.download_all_sources("folder-abc", "batch-123")

    assert len(records) == 10

    failed = [r for r in records if r["status"] == "failed"]
    succeeded = [r for r in records if r["status"] == "success"]

    assert len(failed) == 1
    assert failed[0]["source_file"] == "SRC05_source.csv"
    assert failed[0]["path"] is None
    assert "network unreachable" in failed[0]["error"]

    assert len(succeeded) == 9
    for record in succeeded:
        assert record["error"] is None
        assert record["path"] == f"data/raw/{record['source_file']}"

    output = capsys.readouterr().err
    assert output.count("[ERROR]") == 1
    assert "SRC05_source.csv" in output
```

- [x] **Step 2: Run test to verify it fails** — confirmed unhandled `ConnectionError` propagated out (1 failed, 3 passed)

Run: `uv run pytest tests/test_parser.py -v`
Expected: the new test fails with an unhandled `ConnectionError` propagating out of `download_all_sources()` (the current VDAP-177 implementation has no try/except around `download_file()`), so pytest reports it as an error, not a normal assertion failure. The 3 existing tests still pass.

- [x] **Step 3: Write minimal implementation**

Edit `src/extract/parser.py`'s `download_all_sources()`:
```python
def download_all_sources(folder_id: str, batch_id: str) -> list[dict]:
    logger = get_logger(batch_id)
    files = list_files_in_folder(folder_id)

    records = []
    for file_info in files:
        try:
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
        except Exception as error:
            logger.error("failed to download %s: %s", file_info["name"], error)
            records.append(
                {
                    "source_file": file_info["name"],
                    "status": "failed",
                    "path": None,
                    "error": str(error),
                }
            )

    return records
```

- [x] **Step 4: Run test to verify it passes** — `4 passed`

Run: `uv run pytest tests/test_parser.py -v`
Expected: `4 passed`.

- [x] **Step 5: Run the full suite to confirm no regressions** — `28 passed`, `--collect-only` exit 0

Run: `uv run pytest -q`
Expected: all tests pass (27 existing + 1 new = 28 passed), `uv run pytest --collect-only -q` exits 0.

- [x] **Step 6: Ruff-check the new code** — flagged BLE001 (blind Exception catch), deliberate per ticket's own Technical Steps; added `# noqa: BLE001` with justification comment, re-checked clean

Run: `uvx ruff check src/extract/parser.py tests/test_parser.py`
Expected: no findings.

- [x] **Step 7: Manually verify against the real Google Drive folder (live, not mocked, simulating a real failure)** — 10 records, 9 real success + SRC03 failed with exact simulated error message, path None; cleaned up data/raw/ afterward

```bash
uv run python -c "
from src.extract import parser

_original_download_file = parser.download_file
def flaky_download_file(file_id, file_name):
    if file_name.startswith('SRC03'):
        raise ConnectionError('simulated network failure')
    return _original_download_file(file_id, file_name)
parser.download_file = flaky_download_file

records = parser.download_all_sources('1or8Z1cuL8pkcRypbv3odkMbhAgpje_lr', 'verify-vdap-179')
print(len(records), 'records')
for r in sorted(records, key=lambda x: x['source_file']):
    print(r['source_file'], r['status'], r['path'], r['error'])
"
```
Expected: `10 records` — 9 real downloads with `status success`, exactly 1 (`SRC03_customer_master.csv`) with `status failed`, `path None`, `error` containing `simulated network failure`. No exception printed/raised by the script itself.

Clean up the 9 real downloaded files afterward:
```bash
find data/raw -type f ! -name '.gitkeep' -delete
ls -a data/raw
```
Expected: only `.` `..` `.gitkeep` remain.

- [ ] **Step 8: Commit**

```bash
git add src/extract/parser.py tests/test_parser.py
git commit -m "feat(VDAP-179): catch per-file download errors, status=failed instead of crashing batch"
```

---

## Self-Review

**1. Spec coverage:** Technical Steps (try/except around download_file, logger.error, status=failed record, no re-raise) → Task 1 Step 3. AC (1/10 fails, 9 succeed, 10 records total, no exception escapes) → Step 1's test (mocked) + Step 7 (live, real 9 downloads + 1 simulated failure). No gaps.
**2. Placeholder scan:** No TBD/TODO. `path: None` on failure is a deliberate, documented value (Global Constraints explains why), not an unfinished stub.
**3. Type consistency:** `download_all_sources(folder_id: str, batch_id: str) -> list[dict]` signature unchanged from VDAP-177; record shape keys (`source_file`, `status`, `path`, `error`) unchanged — only the set of values `status`/`path`/`error` can take is extended (`"failed"`/`None`/`<message>` alongside the existing `"success"`/`<path>`/`None`).
