# VDAP-242 Exit Code + Summary Log Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `main.py` exits non-zero and logs a clear ERROR summary whenever any source in a layer run failed, so an external caller (cron, script, `&&`) can detect pipeline failure from the exit code alone — not by reading logs after the fact.

**Architecture:** Extract the "count failures, log summary, decide exit code" logic into a standalone `_check_layer_results(records, layer_name, batch_id) -> int`, decoupled from where `records` came from. `_run_placeholder_layer` (VDAP-236) now returns `list[dict]` instead of `None`, and `main()` feeds that into `_check_layer_results` and returns its result instead of a hardcoded `0`.

**Tech Stack:** Python stdlib (`sys.exit` via `main()`'s return value), `src.logger.get_logger` (VDAP-232).

## Global Constraints

- Technical Notes (VDAP-242, verbatim): sau mỗi layer chạy xong, đếm record `status != "success"`; ≥1 lỗi → log ERROR summary + `sys.exit(1)`; 0 lỗi → `sys.exit(0)` + summary "OK".
- Exact error summary format (verbatim from ticket): `"FAILED: N/M nguồn lỗi ở layer=X, xem ingest_log.parquet"`, on stderr. `src/logger.py`'s `StreamHandler` already routes to stderr — use `logger.error(...)`, not `print()`.
- AC (verbatim): giả lập 1 nguồn `status="failed"` → exit code 1 + summary lỗi rõ ràng trên stderr; toàn bộ thành công → exit code 0.
- Out of scope (ticket's own words): real Slack/email integration — only leave a comment marking the hook point (`if exit_code != 0: send_alert(...)`), no webhook/SMTP code.
- This branch forks from `feature/VDAP-236-wire-logger-main` (PR #38, not yet merged) since it needs `main.py`/`_run_placeholder_layer` from that ticket. Once #38 merges, this branch's PR will show a clean diff against `develop`.

---

### Task 1: `_check_layer_results` + wire into `main()`

**Files:**
- Modify: `main.py` (change `_run_placeholder_layer`'s return type; add `_check_layer_results`; wire into `main()`)
- Test: `tests/test_main.py` (extend existing file — do not create a new one)

**Interfaces:**
- Consumes: `get_logger(batch_id: str) -> logging.LoggerAdapter` (VDAP-232, unchanged).
- Produces: `_check_layer_results(records: list[dict], layer_name: str, batch_id: str) -> int` — returns `1` if any record's `status` != `"success"`, else `0`. `_run_placeholder_layer(batch_id: str) -> list[dict]` — return type changed from `None`.

- [x] **Step 1: Write the failing tests**

Add to `tests/test_main.py` (append; keep the existing imports, fixture, and two tests as-is):
```python
from main import _check_layer_results, main


def test_check_layer_results_returns_1_and_logs_error_on_any_failure(capsys):
    records = [
        {"source": "src01", "status": "success"},
        {"source": "src02", "status": "failed"},
    ]

    exit_code = _check_layer_results(records, layer_name="bronze", batch_id="batch-x")

    assert exit_code == 1
    output = capsys.readouterr().err
    assert "FAILED: 1/2" in output
    assert "layer=bronze" in output
    assert "[ERROR]" in output
    assert "ingest_log.parquet" in output


def test_check_layer_results_returns_0_and_logs_ok_when_all_succeed(capsys):
    records = [
        {"source": "src01", "status": "success"},
        {"source": "src02", "status": "success"},
    ]

    exit_code = _check_layer_results(records, layer_name="bronze", batch_id="batch-x")

    assert exit_code == 0
    output = capsys.readouterr().err
    assert "OK" in output
    assert "layer=bronze" in output
```

Note: `test_all_log_lines_share_one_batch_id` (already in the file from VDAP-236) still asserts `exit_code == 0` — this stays correct because `_run_placeholder_layer`'s only record is always `status: "success"`.

- [x] **Step 2: Run tests to verify they fail** — confirmed `ImportError: cannot import name '_check_layer_results' from 'main'`

Run: `uv run pytest tests/test_main.py -v`
Expected: `ImportError: cannot import name '_check_layer_results' from 'main'` (2 new tests error at collection; the 2 existing tests are unaffected by the import error only if pytest reports a collection error for the whole file — expect the whole file to fail to collect, which is the correct "red" state before Step 3).

- [x] **Step 3: Write minimal implementation**

Edit `main.py` to:
```python
"""Pipeline entrypoint (Sprint 0 skeleton, VDAP-236/VDAP-242).

Epic 1 will replace _run_placeholder_layer with the real
src.extract.orchestrator.run_bronze_ingestion() (and its silver/gold
equivalents) — batch_id and the records-in/exit-code-out contract are
already wired here so that swap won't need to touch this file's control
flow.

Hook point for real alerting (VDAP-242, out of scope for this ticket —
no webhook/SMTP available to test against in this capstone):
    exit_code = main()
    if exit_code != 0:
        send_alert(...)  # e.g. Slack/email webhook, not implemented here
"""

import sys
import uuid

from src.logger import get_logger


def _run_placeholder_layer(batch_id: str) -> list[dict]:
    logger = get_logger(batch_id)
    logger.info("placeholder layer running")
    return [{"source": "placeholder", "status": "success"}]


def _check_layer_results(records: list[dict], layer_name: str, batch_id: str) -> int:
    logger = get_logger(batch_id)
    total = len(records)
    failed = [r for r in records if r.get("status") != "success"]

    if failed:
        logger.error(
            "FAILED: %d/%d nguồn lỗi ở layer=%s, xem ingest_log.parquet",
            len(failed),
            total,
            layer_name,
        )
        return 1

    logger.info("OK: %d/%d nguồn thành công ở layer=%s", total, total, layer_name)
    return 0


def main() -> int:
    batch_id = str(uuid.uuid4())
    logger = get_logger(batch_id)
    logger.info("pipeline run started")
    records = _run_placeholder_layer(batch_id)
    exit_code = _check_layer_results(records, layer_name="bronze", batch_id=batch_id)
    logger.info("pipeline run finished")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
```

- [x] **Step 4: Run tests to verify they pass** — `4 passed`

Run: `uv run pytest tests/test_main.py -v`
Expected: `4 passed`.

- [x] **Step 5: Run the full suite to confirm no regressions** — `17 passed`, `--collect-only` exit 0

Run: `uv run pytest -q`
Expected: all tests pass (15 existing + 2 new = 17 passed), `uv run pytest --collect-only -q` exits 0.

- [x] **Step 6: Manually confirm both AC scenarios end-to-end** — success: exit 0, "OK: 1/1 nguồn thành công ở layer=bronze"; failure: exit 1, "FAILED: 1/1 nguồn lỗi ở layer=bronze, xem ingest_log.parquet"

Success path:
```bash
uv run python main.py; echo "exit code: $?"
```
Expected: `exit code: 0`, last log line before that is `OK: 1/1 nguồn thành công ở layer=bronze`.

Failure path (simulate 1 failed source without touching production code):
```bash
uv run python -c "
import main
main._run_placeholder_layer = lambda batch_id: [{'source': 'src01', 'status': 'failed'}]
raise SystemExit(main.main())
"
echo "exit code: $?"
```
Expected: `exit code: 1`, an ERROR line matching `FAILED: 1/1 nguồn lỗi ở layer=bronze, xem ingest_log.parquet` on stderr.

- [ ] **Step 7: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat(VDAP-242): exit non-zero + log ERROR summary when a layer has failures"
```

---

## Self-Review

**1. Spec coverage:** Technical Steps (count failures, ERROR summary, sys.exit(1)/0) → Task 1 Step 3 `_check_layer_results`. Exact summary string → Step 3's `logger.error(...)` format string, verified verbatim in Step 1's test assertions and Step 6's manual run. AC (simulate 1 failed source → exit 1 + clear stderr summary; all succeed → exit 0) → Step 1 tests (unit level) + Step 6 (full end-to-end `main()` run, including the failure path via monkeypatching `_run_placeholder_layer` — no production code branches on "am I being tested"). Alerting hook-point → docstring comment in Step 3, no real integration code. No gaps.
**2. Placeholder scan:** No TBD/TODO. The alerting hook is a comment, not a stub function — the ticket explicitly asks for a comment only, not code.
**3. Type consistency:** `_check_layer_results(records: list[dict], layer_name: str, batch_id: str) -> int` used identically in tests and implementation. `_run_placeholder_layer`'s new return type (`list[dict]`) matches what `_check_layer_results` and `main()` expect it to produce.
