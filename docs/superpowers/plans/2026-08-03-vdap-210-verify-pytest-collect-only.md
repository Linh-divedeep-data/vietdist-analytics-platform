# VDAP-210 Verify pytest --collect-only Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing `pytest --collect-only` CI step (added in VDAP-205) actually exercise every importable module under `src/` and `config/`, so a broken import in those packages fails CI clearly — not just when `tests/` happens to contain a real test file.

**Architecture:** Add one placeholder test file, `tests/test_placeholder.py`, with one test function per current `src/`/`config/` submodule, each importing that submodule and asserting it's not `None`. This gives `pytest --collect-only` (and later, real `pytest` runs) a concrete reason to import the whole package tree today, instead of only importing whatever future test files happen to import.

**Tech Stack:** pytest, GitHub Actions (existing `.github/workflows/ci.yml` from VDAP-205, no changes needed there).

## Global Constraints

- AC (VDAP-210, verbatim): CI job pass khi chưa có test thật; fail rõ ràng nếu có lỗi import trong `src/`.
- Technical Steps (verbatim): "verify chạy pass với tests/ rỗng (hoặc file test placeholder)" — placeholder file is an explicitly authorized option, not scope creep.
- Every `src/**/*.py` and `config/**/*.py` file today is a docstring-only skeleton (Epic Phase 1 fills them in later) with zero import-time side effects — confirmed by reading all 8 files. Safe to import directly in CI, no credentials/env needed.
- `gdrive_connector.py` (repo root) is NOT under `src/` — out of scope for this ticket's AC, do not import it (it performs real Google auth at import time and would require credentials in CI).
- Do not modify `.github/workflows/ci.yml` — the exit-code-5 handling from VDAP-205 (feature/VDAP-205-ci-lint-test-workflow, merged to develop) already covers both AC branches correctly; adding a real test file changes pytest's exit code from 5 to 0 on success, which the existing `if [ "$code" -eq 5 ]` branch already passes through unchanged (falls to `exit "$code"` which is 0).

---

### Task 1: Add placeholder import-coverage test

**Files:**
- Create: `tests/test_placeholder.py`

**Interfaces:**
- Consumes: `src` (`src/__init__.py`), `src.extract` (`__init__.py`, `parser.py`, `orchestrator.py`, `lineage.py`, `registry.py`, `ingest_log.py`), `src.extract.unit_of_work` (`__init__.py`, `base.py`), `config` (`__init__.py`, `settings.py`, `sources.py`) — all current modules, no functions/classes exist in them yet (docstring-only).
- Produces: nothing consumed by later tasks — this is the final task.

- [ ] **Step 1: Write the failing test**

Create `tests/test_placeholder.py`:
```python
"""Placeholder import-coverage tests (VDAP-210).

Purpose: make `pytest --collect-only` actually import every module under
src/ and config/, so a broken import fails CI now — not only once real
tests exist. Delete/replace individual functions here as Epic Phase 1
(P1.x tickets) adds real tests for each module.
"""


def test_src_package_importable():
    import src

    assert src is not None


def test_src_extract_parser_importable():
    from src.extract import parser

    assert parser is not None


def test_src_extract_orchestrator_importable():
    from src.extract import orchestrator

    assert orchestrator is not None


def test_src_extract_lineage_importable():
    from src.extract import lineage

    assert lineage is not None


def test_src_extract_registry_importable():
    from src.extract import registry

    assert registry is not None


def test_src_extract_ingest_log_importable():
    from src.extract import ingest_log

    assert ingest_log is not None


def test_src_extract_unit_of_work_base_importable():
    from src.extract.unit_of_work import base

    assert base is not None


def test_config_settings_importable():
    from config import settings

    assert settings is not None


def test_config_sources_importable():
    from config import sources

    assert sources is not None
```

This file does not exist yet, so this is the "failing" state (test collection currently reports 0 items instead of 9).

- [ ] **Step 2: Run collection to verify the new state**

Run: `uv run pytest --collect-only -q`
Expected before Step 1 is saved: `no tests collected` (0 items) — confirms current gap.
Expected after Step 1 is saved: `9/9 tests collected` (all 9 functions listed, 0 errors).

- [ ] **Step 3: Run the tests for real (not just collect) to verify they pass**

Run: `uv run pytest -v`
Expected: `9 passed` in output, exit code 0.

- [ ] **Step 4: Prove the negative case — a broken src/ import fails CI clearly**

Temporarily add a bad import to any one src module, e.g. append this line to the top of `src/extract/parser.py`:
```python
import this_module_does_not_exist_xyz
```
Run: `uv run pytest --collect-only -q`
Expected: `ERROR collecting tests/test_placeholder.py` with `ModuleNotFoundError: No module named 'this_module_does_not_exist_xyz'`, non-zero exit code (not 5 — a real collection error).

Then revert the temporary line (do not commit it):
```bash
git checkout -- src/extract/parser.py
```
Run: `uv run pytest --collect-only -q` again — confirm back to `9 tests collected`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add tests/test_placeholder.py
git commit -m "test(VDAP-210): add placeholder import-coverage tests for src/ and config/"
```

- [ ] **Step 6: Push and confirm CI run is green (AC)**

This happens after `finishing-a-development-branch` pushes the branch — verify with:
```bash
gh run list --workflow=ci.yml --limit=1
```
Expected: latest run for this branch is `success`.

---

## Self-Review

**1. Spec coverage:** AC "pass khi chưa có test thật" → already covered by VDAP-205's exit-code-5 handling, unaffected since this task adds real tests (exit code becomes 0, not 5 — same `if` branch harmlessly falls through). AC "fail rõ ràng nếu có lỗi import trong src/" → Task 1 Step 4 proves this directly with a real broken import. Technical Steps' "file test placeholder" option → Task 1 Step 1. No gaps.
**2. Placeholder scan:** The word "placeholder" in the filename/docstring is the ticket's own required terminology (ticket's Technical Steps literally says "file test placeholder"), not an unfinished plan step — every test function has real, runnable content.
**3. Type consistency:** N/A — no shared functions/types across tasks (single task, single file).
