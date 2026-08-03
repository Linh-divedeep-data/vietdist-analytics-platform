# VDAP-236 Wire Logger into main.py Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A `main.py` entrypoint that generates one `batch_id` per run and threads it through every log line, so all logging in a single pipeline run can be correlated.

**Architecture:** `main.py` defines `main() -> int`, which generates `batch_id = str(uuid.uuid4())` once, gets a logger via `get_logger(batch_id)` (VDAP-232), and calls one placeholder layer function that also logs through the same `batch_id`. `_run_placeholder_layer` stands in for `src.extract.orchestrator.run_bronze_ingestion()`, which Epic 1 hasn't implemented yet (confirmed: `src/extract/orchestrator.py` is currently docstring-only).

**Tech Stack:** Python stdlib (`uuid`, `sys`), `src.logger.get_logger` (VDAP-232).

## Global Constraints

- Technical Notes (VDAP-236, verbatim): `main.py` tạo `batch_id = str(uuid.uuid4())` đầu chương trình → truyền vào `get_logger(batch_id)` + các hàm extract/transform.
- AC (verbatim, scoped per explicit user decision this session): mọi dòng log trong 1 lần chạy có cùng `batch_id`. The AC's "batch_id khớp với ingest_log.parquet ở Epic 1" clause is forward-looking design intent, not testable today — Epic 1 (`src/extract/orchestrator.py`, `src/extract/ingest_log.py`) is still docstring-only skeleton, confirmed by reading both files.
- Scope: do NOT modify `src/extract/*.py` or `config/*.py` — those belong to separate Epic 1 tickets. This ticket only adds `main.py` + its test.
- `main.py`'s placeholder layer is a named, clearly-commented stand-in (`_run_placeholder_layer`) so Epic 1's real wiring is a drop-in replacement, not a rewrite.

---

### Task 1: `main.py` with batch_id threading

**Files:**
- Create: `main.py`
- Test: `tests/test_main.py`

**Interfaces:**
- Consumes: `get_logger(batch_id: str) -> logging.LoggerAdapter` from `src/logger.py` (VDAP-232).
- Produces: `main() -> int`, the CLI entrypoint VDAP-242 will extend next (adding real exit-code-from-records logic in place of the current `return 0`).

- [x] **Step 1: Write the failing tests**

Create `tests/test_main.py`:
```python
import logging
import re

import pytest

from main import main

LOG_LINE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} "
    r"\[(?P<level>[A-Z]+)\] \[batch_id=(?P<batch_id>[^\]]+)\] (?P<message>.+)$"
)


@pytest.fixture(autouse=True)
def _reset_shared_logger():
    logger = logging.getLogger("vietdist")
    logger.handlers.clear()
    yield
    logger.handlers.clear()


def test_all_log_lines_share_one_batch_id(capsys):
    exit_code = main()

    lines = capsys.readouterr().err.strip().splitlines()
    assert len(lines) >= 2

    batch_ids = set()
    for line in lines:
        match = LOG_LINE_RE.match(line)
        assert match is not None, f"log line did not match expected format: {line!r}"
        batch_ids.add(match.group("batch_id"))

    assert len(batch_ids) == 1
    assert exit_code == 0


def test_different_runs_get_different_batch_ids(capsys):
    main()
    first_run_lines = capsys.readouterr().err.strip().splitlines()
    first_batch_id = LOG_LINE_RE.match(first_run_lines[0]).group("batch_id")

    main()
    second_run_lines = capsys.readouterr().err.strip().splitlines()
    second_batch_id = LOG_LINE_RE.match(second_run_lines[0]).group("batch_id")

    assert first_batch_id != second_batch_id
```

- [x] **Step 2: Run tests to verify they fail** — confirmed `ModuleNotFoundError: No module named 'main'`

Run: `uv run pytest tests/test_main.py -v`
Expected: `ModuleNotFoundError: No module named 'main'` — `main.py` doesn't exist yet.

- [x] **Step 3: Write minimal implementation**

Create `main.py`:
```python
"""Pipeline entrypoint (Sprint 0 skeleton, VDAP-236).

Epic 1 will replace _run_placeholder_layer with the real
src.extract.orchestrator.run_bronze_ingestion() (and its silver/gold
equivalents) — batch_id is already threaded through get_logger() here
so that swap won't need to touch the logging plumbing.
"""

import sys
import uuid

from src.logger import get_logger


def _run_placeholder_layer(batch_id: str) -> None:
    logger = get_logger(batch_id)
    logger.info("placeholder layer running")


def main() -> int:
    batch_id = str(uuid.uuid4())
    logger = get_logger(batch_id)
    logger.info("pipeline run started")
    _run_placeholder_layer(batch_id)
    logger.info("pipeline run finished")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [x] **Step 4: Run tests to verify they pass** — `2 passed`, no repeat of VDAP-232's LogCaptureHandler bug (get_logger()'s name-based guard already handles it)

Run: `uv run pytest tests/test_main.py -v`
Expected: `2 passed`.

- [x] **Step 5: Run the full suite to confirm no regressions** — `15 passed`, `--collect-only` exit 0

Run: `uv run pytest -q`
Expected: all tests pass (13 existing + 2 new = 15 passed), `uv run pytest --collect-only -q` exits 0.

- [x] **Step 6: Manually confirm the exact AC scenario** — `uv run python main.py` printed 3 lines, all with batch_id=0f262737-39e0-45de-bcdc-37f2aa6cf9b5

Run: `uv run python main.py`
Expected: 3 lines on stderr, same `batch_id=<uuid>` on every line, e.g.:
```
2026-08-03 12:00:00,000 [INFO] [batch_id=...] pipeline run started
2026-08-03 12:00:00,000 [INFO] [batch_id=...] placeholder layer running
2026-08-03 12:00:00,000 [INFO] [batch_id=...] pipeline run finished
```

- [ ] **Step 7: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat(VDAP-236): add main.py entrypoint threading batch_id through get_logger"
```

---

## Self-Review

**1. Spec coverage:** Technical Notes (`batch_id = str(uuid.uuid4())` once, threaded into `get_logger()` + extract/transform calls) → Task 1 Step 3 (`_run_placeholder_layer` stands in for the not-yet-built extract/transform call). AC (all log lines share one batch_id) → Task 1 Step 1 tests + Step 6 manual run. "Khớp ingest_log.parquet ở Epic 1" → explicitly out of scope per this session's user decision, documented in Global Constraints. No gaps against the scoped AC.
**2. Placeholder scan:** `_run_placeholder_layer`'s name itself says "placeholder" — that's the deliberate, documented stand-in for Epic 1's real layer function (not an unfinished plan step); its body is fully implemented (logs one line), not a TBD.
**3. Type consistency:** `main() -> int` matches what VDAP-242's plan will extend (same signature, just changing the `return 0` to real exit-code logic). `_run_placeholder_layer(batch_id: str) -> None` is private to this file.
