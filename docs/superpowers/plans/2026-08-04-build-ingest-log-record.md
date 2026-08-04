# build_ingest_log_record() Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `build_ingest_log_record(batch_id, source_file, rows_loaded, status, duration_sec, source_platform="google_drive") -> dict` in `src/extract/ingest_log.py`, producing one standardized ingest-log record (dict, 7 fields) summarizing the result of processing one source.

**Architecture:** Single pure function with no I/O — builds and returns a plain `dict` literal. `source_name` is derived from `source_file` via `os.path.splitext(source_file)[0]` (strips only the last extension).

**Tech Stack:** Python stdlib `os.path.splitext`.

## Global Constraints

- Only touch `src/extract/ingest_log.py` and `tests/test_ingest_log.py` (new file) — do NOT implement `write_ingest_log()` (separate ticket, Story P1.6, writes to parquet).
- Returned dict must have exactly 7 fields: `batch_id`, `source_name`, `source_file`, `source_platform`, `rows_loaded`, `status`, `duration_sec`.
- `source_platform` defaults to `"google_drive"` when not passed.
- Follow existing convention in `src/extract/lineage.py`/`src/extract/parser.py`: plain function, type hints on params/return, no per-function docstring.
- Keep `tests/test_placeholder.py::test_src_extract_ingest_log_importable` passing (plain module import, no side effects at import time).

---

### Task 1: Implement build_ingest_log_record() with tests

**Files:**
- Modify: `src/extract/ingest_log.py`
- Create: `tests/test_ingest_log.py`

**Interfaces:**
- Produces: `build_ingest_log_record(batch_id: str, source_file: str, rows_loaded: int, status: str, duration_sec: float, source_platform: str = "google_drive") -> dict` — returns `{"batch_id": ..., "source_name": ..., "source_file": ..., "source_platform": ..., "rows_loaded": ..., "status": ..., "duration_sec": ...}`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_ingest_log.py`:

```python
from src.extract import ingest_log


def test_build_ingest_log_record_has_exactly_seven_fields_with_correct_values():
    record = ingest_log.build_ingest_log_record(
        batch_id="batch-123",
        source_file="SRC01_sales.csv",
        rows_loaded=42,
        status="success",
        duration_sec=1.23,
    )

    assert record == {
        "batch_id": "batch-123",
        "source_name": "SRC01_sales",
        "source_file": "SRC01_sales.csv",
        "source_platform": "google_drive",
        "rows_loaded": 42,
        "status": "success",
        "duration_sec": 1.23,
    }


def test_build_ingest_log_record_source_name_strips_only_last_extension():
    record = ingest_log.build_ingest_log_record(
        batch_id="batch-123",
        source_file="SRC01.sales.v2.csv",
        rows_loaded=10,
        status="success",
        duration_sec=0.5,
    )

    assert record["source_name"] == "SRC01.sales.v2"
    assert record["source_file"] == "SRC01.sales.v2.csv"


def test_build_ingest_log_record_default_source_platform_is_google_drive():
    record = ingest_log.build_ingest_log_record(
        batch_id="batch-123",
        source_file="SRC02_target.xlsx",
        rows_loaded=5,
        status="failed",
        duration_sec=0.1,
    )

    assert record["source_platform"] == "google_drive"


def test_build_ingest_log_record_accepts_explicit_source_platform_override():
    record = ingest_log.build_ingest_log_record(
        batch_id="batch-123",
        source_file="SRC03_other.csv",
        rows_loaded=0,
        status="schema_mismatch",
        duration_sec=0.05,
        source_platform="sftp",
    )

    assert record["source_platform"] == "sftp"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_ingest_log.py -v`
Expected: FAIL with `AttributeError: module 'src.extract.ingest_log' has no attribute 'build_ingest_log_record'`

- [ ] **Step 3: Write implementation**

Replace contents of `src/extract/ingest_log.py`:

```python
"""build_ingest_log_record() + write_ingest_log() — filled in Epic Phase 1 (VDAP-116-118)."""

import os


def build_ingest_log_record(
    batch_id: str,
    source_file: str,
    rows_loaded: int,
    status: str,
    duration_sec: float,
    source_platform: str = "google_drive",
) -> dict:
    return {
        "batch_id": batch_id,
        "source_name": os.path.splitext(source_file)[0],
        "source_file": source_file,
        "source_platform": source_platform,
        "rows_loaded": rows_loaded,
        "status": status,
        "duration_sec": duration_sec,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_ingest_log.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Run full test suite and lint to check for regressions**

Run: `uv run pytest -v`
Expected: all tests pass, including `tests/test_placeholder.py::test_src_extract_ingest_log_importable`

Run: `uvx ruff check src/extract/ingest_log.py tests/test_ingest_log.py`
Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add src/extract/ingest_log.py tests/test_ingest_log.py
git commit -m "feat(VDAP-289): add build_ingest_log_record()"
```

---

## Self-Review Notes

- **Spec coverage:** All 7 fields (`batch_id`, `source_name`, `source_file`, `source_platform`, `rows_loaded`, `status`, `duration_sec`) covered by Step 1 tests and Step 3 implementation. `source_name` derivation via `os.path.splitext` covered including the multi-dot-filename edge case. Default vs explicit `source_platform` both covered.
- **Placeholder scan:** none — all steps contain literal code.
- **Type consistency:** single function, single task — no cross-task signature drift possible.
- **Out of scope confirmed:** `write_ingest_log()` untouched, module docstring left as-is (already mentions it, no change needed there).
