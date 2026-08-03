# VDAP-232 src/logger.py Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A single shared `src/logger.py` module exporting `get_logger(batch_id)`, so every module in the pipeline logs in one consistent format instead of each inventing its own.

**Architecture:** One module-level named logger (`"vietdist"`) configured once with a `StreamHandler` + custom `Formatter`. `get_logger(batch_id)` wraps that shared logger in a `logging.LoggerAdapter` that injects `batch_id` into every record via the adapter's `extra` merging, so the format string can reference `%(batch_id)s` like any other record attribute.

**Tech Stack:** Python `logging` stdlib only — no third-party logging library (ticket's own Tech Stack line).

## Global Constraints

- Technical Notes (VDAP-232, verbatim): `logging.Formatter` với `%(asctime)s [%(levelname)s] [batch_id=...] %(message)s`; `get_logger()` gắn `batch_id` vào output qua `LoggerAdapter`.
- AC (verbatim): `import src.logger`, gọi `get_logger("test-batch").info("hello")` in ra đúng format.
- File(s): `src/logger.py` only — this ticket does NOT wire the logger into `orchestrator.py`/`main.py` (that's bd `8op.5.2`, a separate ticket). Do not touch `src/extract/orchestrator.py`.
- Reuse `pythonpath = ["."]` already configured in `pyproject.toml` (VDAP-210) — `import src.logger` works from `tests/` without extra config.

---

### Task 1: `get_logger(batch_id)` with format-verified tests

**Files:**
- Create: `src/logger.py`
- Test: `tests/test_logger.py`

**Interfaces:**
- Produces: `get_logger(batch_id: str) -> logging.LoggerAdapter` — the only public symbol `src/logger.py` exports. `8op.5.2` (wiring into `main.py`) will call this exact signature later.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_logger.py`:
```python
import logging
import re

import pytest

from src.logger import get_logger


@pytest.fixture(autouse=True)
def _reset_shared_logger():
    """Each test needs its own capsys-captured stream, but get_logger()
    only attaches a handler once (on first call). Clearing handlers
    before/after every test forces a fresh handler bound to *this*
    test's capsys-patched sys.stderr, instead of reusing a handler
    whose .stream still points at a previous test's capsys object."""
    logger = logging.getLogger("vietdist")
    logger.handlers.clear()
    yield
    logger.handlers.clear()


LOG_LINE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} "
    r"\[(?P<level>[A-Z]+)\] \[batch_id=(?P<batch_id>[^\]]+)\] (?P<message>.+)$"
)


def test_info_log_matches_expected_format(capsys):
    get_logger("test-batch").info("hello")

    output = capsys.readouterr().err.strip()
    match = LOG_LINE_RE.match(output)

    assert match is not None, f"log line did not match expected format: {output!r}"
    assert match.group("level") == "INFO"
    assert match.group("batch_id") == "test-batch"
    assert match.group("message") == "hello"


def test_error_log_uses_error_level(capsys):
    get_logger("batch-2").error("something broke")

    output = capsys.readouterr().err.strip()
    match = LOG_LINE_RE.match(output)

    assert match is not None, f"log line did not match expected format: {output!r}"
    assert match.group("level") == "ERROR"
    assert match.group("batch_id") == "batch-2"
    assert match.group("message") == "something broke"


def test_different_batch_ids_are_independent(capsys):
    get_logger("batch-a").info("from a")
    get_logger("batch-b").info("from b")

    lines = capsys.readouterr().err.strip().splitlines()
    assert len(lines) == 2

    first = LOG_LINE_RE.match(lines[0])
    second = LOG_LINE_RE.match(lines[1])
    assert first.group("batch_id") == "batch-a"
    assert second.group("batch_id") == "batch-b"


def test_get_logger_returns_logger_adapter():
    adapter = get_logger("test-batch")
    assert isinstance(adapter, logging.LoggerAdapter)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_logger.py -v`
Expected: `ModuleNotFoundError: No module named 'src.logger'` (or collection error) — `src/logger.py` doesn't exist yet.

- [x] **Step 3: Write minimal implementation** — deviation found and fixed during Step 4: the naive `if not logger.handlers:` guard broke under pytest, because pytest's own log-capturing injects `LogCaptureHandler` instances directly onto any logger with `propagate=False` between fixture setup and the test body running. The guard saw those foreign handlers and wrongly concluded ours was already attached, so it never created the real `StreamHandler`. Fixed by checking for a handler by name (`_HANDLER_NAME = "vietdist-handler"`) instead of checking list emptiness — see the actual `src/logger.py` content below (already updated).

Create `src/logger.py`:
```python
"""Shared logging module (VDAP-232).

Every pipeline module should log through get_logger(batch_id) instead of
configuring its own logging.Logger, so all output shares one format:
"%(asctime)s [%(levelname)s] [batch_id=...] %(message)s".
"""

import logging

_LOG_FORMAT = "%(asctime)s [%(levelname)s] [batch_id=%(batch_id)s] %(message)s"
_LOGGER_NAME = "vietdist"


_HANDLER_NAME = "vietdist-handler"


def get_logger(batch_id: str) -> logging.LoggerAdapter:
    logger = logging.getLogger(_LOGGER_NAME)
    if not any(h.name == _HANDLER_NAME for h in logger.handlers):
        handler = logging.StreamHandler()
        handler.name = _HANDLER_NAME
        handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logging.LoggerAdapter(logger, {"batch_id": batch_id})
```

- [x] **Step 4: Run tests to verify they pass** — 4 tests (not 5; the plan's test count was corrected during self-review, see Task 1 file content), all pass: `4 passed`.

- [x] **Step 5: Run the full suite to confirm no regressions** — `uv run pytest -q` → `13 passed` (VDAP-210's 9 placeholder tests + these 4), `uv run pytest --collect-only -q` → exit 0.

- [x] **Step 6: Manually confirm the exact AC scenario** — ran, output: `2026-08-03 11:57:14,399 [INFO] [batch_id=test-batch] hello` — matches AC exactly.

Run:
```bash
uv run python -c "
import sys
from src.logger import get_logger
get_logger('test-batch').info('hello')
" 
```
Expected stderr output line matching: `YYYY-MM-DD HH:MM:SS,mmm [INFO] [batch_id=test-batch] hello`

- [ ] **Step 7: Commit**

```bash
git add src/logger.py tests/test_logger.py
git commit -m "feat(VDAP-232): add src/logger.py get_logger(batch_id) with shared format"
```

---

## Self-Review

**1. Spec coverage:** Technical Notes (Formatter format string, `get_logger()` + `LoggerAdapter`) → Task 1 Step 3. AC (`get_logger("test-batch").info("hello")` prints correct format) → Task 1 Step 1 test + Step 6 manual confirmation. No gaps.
**2. Placeholder scan:** No TBD/TODO. A duplicate `test_error_log_uses_error_level` stub from initial drafting was caught and removed during self-review — the file above now defines each test function once.
**3. Type consistency:** Single function `get_logger(batch_id: str) -> logging.LoggerAdapter` used identically in tests and implementation. `_LOGGER_NAME`/`_LOG_FORMAT` are private module constants, not part of the public interface.
