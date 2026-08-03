# VDAP-186 config/sources.py Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `config/sources.py` declares the 10 fixed source file names (SRC01-SRC10) once, split into `CSV_SOURCES` (4) and `EXCEL_SOURCES` (6), so nothing else in the codebase hardcodes these names.

**Architecture:** Two plain list-of-string constants, no functions, no logic beyond the declaration itself. `config/` must not import from `src/` — `src/` will import `config`, not the reverse — so this file stays a pure leaf with zero internal imports.

**Tech Stack:** Python list constants.

## Global Constraints

- Technical Steps (VDAP-186, verbatim): list exactly the 10 file names per BRD §2.2; do not import anything from `src/` in this file (avoids a reverse dependency).
- AC (verbatim): `len(CSV_SOURCES) + len(EXCEL_SOURCES) == 10`, no duplicate file names.
- File(s): `config/sources.py` only.
- Source of truth for names: BRD §2.2 Data Dictionary (already read) — SRC01 sales_transactions (csv), SRC02 sales_target_plan (xlsx), SRC03 customer_master (csv), SRC04 product_master (xlsx), SRC05 distributor_orders (xlsx), SRC06 distributor_master (csv), SRC07 employee_master (xlsx), SRC08 territory_mapping (xlsx), SRC09 return_transactions (csv), SRC10 promotion_program (xlsx). This matches the ticket's own CSV/EXCEL split (CSV: 01,03,06,09; EXCEL: 02,04,05,07,08,10) and matches the real Drive file names already observed live during VDAP-173/175/177/179 (`SRC01_sales_transactions.csv` … `SRC10_promotion_program.xlsx`).
- Full file names use the format `SRCnn_source_name.ext` — this is what `list_files_in_folder()` actually returns from Drive, so these constants must match those real names exactly, not just the `SRCnn` short codes.

---

### Task 1: `CSV_SOURCES`/`EXCEL_SOURCES` constants

**Files:**
- Modify: `config/sources.py`
- Test: `tests/test_sources.py` (new — no dedicated test file exists yet, only an import-smoke-test in `tests/test_placeholder.py`)

**Interfaces:**
- Produces: `CSV_SOURCES: list[str]`, `EXCEL_SOURCES: list[str]` — module-level constants other code (e.g. the future `read_csv_source`/`read_excel_source` in `src/extract/parser.py`) will import.

- [x] **Step 1: Write the failing tests**

Create `tests/test_sources.py`:
```python
import ast
from pathlib import Path

from config.sources import CSV_SOURCES, EXCEL_SOURCES


def test_total_source_count_is_10():
    assert len(CSV_SOURCES) + len(EXCEL_SOURCES) == 10


def test_no_duplicate_source_names():
    all_sources = CSV_SOURCES + EXCEL_SOURCES
    assert len(all_sources) == len(set(all_sources))


def test_csv_sources_are_the_expected_4():
    assert set(CSV_SOURCES) == {
        "SRC01_sales_transactions.csv",
        "SRC03_customer_master.csv",
        "SRC06_distributor_master.csv",
        "SRC09_return_transactions.csv",
    }


def test_excel_sources_are_the_expected_6():
    assert set(EXCEL_SOURCES) == {
        "SRC02_sales_target_plan.xlsx",
        "SRC04_product_master.xlsx",
        "SRC05_distributor_orders.xlsx",
        "SRC07_employee_master.xlsx",
        "SRC08_territory_mapping.xlsx",
        "SRC10_promotion_program.xlsx",
    }


def test_sources_module_does_not_import_from_src():
    source = Path("config/sources.py").read_text()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("src"), (
                f"config/sources.py must not import from src/: found 'from {node.module} import ...'"
            )
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("src"), (
                    f"config/sources.py must not import src/: found 'import {alias.name}'"
                )
```

- [x] **Step 2: Run tests to verify they fail** — confirmed `ImportError: cannot import name 'CSV_SOURCES'`

Run: `uv run pytest tests/test_sources.py -v`
Expected: `ImportError: cannot import name 'CSV_SOURCES' from 'config.sources'` — constants don't exist yet.

- [x] **Step 3: Write minimal implementation**

Replace the content of `config/sources.py`:
```python
"""Source registry (CSV_SOURCES, EXCEL_SOURCES, REQUIRED_COLUMNS) — filled in Epic Phase 1 (VDAP-92).

The 10 fixed source files (SRC01-SRC10) per BRD section 2.2. No
imports from src/ here — src/ imports config, not the other way
around (avoids a reverse dependency).
"""

CSV_SOURCES = [
    "SRC01_sales_transactions.csv",
    "SRC03_customer_master.csv",
    "SRC06_distributor_master.csv",
    "SRC09_return_transactions.csv",
]

EXCEL_SOURCES = [
    "SRC02_sales_target_plan.xlsx",
    "SRC04_product_master.xlsx",
    "SRC05_distributor_orders.xlsx",
    "SRC07_employee_master.xlsx",
    "SRC08_territory_mapping.xlsx",
    "SRC10_promotion_program.xlsx",
]
```

- [x] **Step 4: Run tests to verify they pass** — `5 passed`

Run: `uv run pytest tests/test_sources.py -v`
Expected: `5 passed`.

- [x] **Step 5: Run the full suite to confirm no regressions** — `32 passed` (this branch forked before PR #46/VDAP-179 merged, so baseline was 27 not 28 as originally estimated), `--collect-only` exit 0

Run: `uv run pytest -q`
Expected: all tests pass (28 existing + 5 new = 33 passed), `uv run pytest --collect-only -q` exits 0. In particular `tests/test_placeholder.py::test_config_sources_importable` must still pass.

- [x] **Step 6: Ruff-check the new code** — `All checks passed!`

Run: `uvx ruff check config/sources.py tests/test_sources.py`
Expected: no findings.

- [x] **Step 7: Manually verify against the real Google Drive folder (live, not mocked)** — `MATCH: config/sources.py exactly matches the real Drive folder`, 0 missing, 0 extra

```bash
uv run python -c "
from src.gdrive_connector import list_files_in_folder
from config.sources import CSV_SOURCES, EXCEL_SOURCES

real_names = {f['name'] for f in list_files_in_folder('1or8Z1cuL8pkcRypbv3odkMbhAgpje_lr')}
declared_names = set(CSV_SOURCES) | set(EXCEL_SOURCES)

missing = real_names - declared_names
extra = declared_names - real_names
print('missing from config/sources.py:', missing or 'none')
print('declared but not on Drive:', extra or 'none')
assert not missing and not extra, 'declared sources do not match real Drive folder contents'
print('MATCH: config/sources.py exactly matches the real Drive folder')
"
```
Expected: `MATCH: config/sources.py exactly matches the real Drive folder` — proves the declared constants aren't just internally consistent, they match what's actually in the real source-of-truth folder.

- [ ] **Step 8: Commit**

```bash
git add config/sources.py tests/test_sources.py
git commit -m "feat(VDAP-186): declare CSV_SOURCES/EXCEL_SOURCES in config/sources.py"
```

---

## Self-Review

**1. Spec coverage:** Technical Steps (10 names per BRD §2.2, no src/ import) → Task 1 Step 3, verified by `test_sources_module_does_not_import_from_src` (Step 1) and Step 7's live Drive comparison. AC (count==10, no duplicates) → `test_total_source_count_is_10`/`test_no_duplicate_source_names` (Step 1). No gaps.
**2. Placeholder scan:** No TBD/TODO. The docstring's `REQUIRED_COLUMNS — filled in Epic Phase 1 (VDAP-92)` reference is pre-existing text describing a different, not-yet-built constant in the same file's eventual scope — not a stub introduced by this plan.
**3. Type consistency:** `CSV_SOURCES: list[str]`, `EXCEL_SOURCES: list[str]` — same shape used identically across implementation and all 5 tests.
