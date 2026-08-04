# attach_lineage() Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `attach_lineage(df, source_file, run_date, batch_id) -> pl.DataFrame` in `src/extract/lineage.py`, which stamps 5 mandatory Bronze lineage metadata columns onto a Polars DataFrame without altering original data.

**Architecture:** Single pure function using `pl.DataFrame.with_columns()` + `pl.lit()` to append 5 literal-valued columns. `_ingested_at` is computed fresh from `datetime.now(UTC)` at call time (read inside the function body, never memoized/module-level) so repeated calls produce distinct timestamps.

**Tech Stack:** Polars (`with_columns`, `pl.lit`), Python stdlib `datetime` (`datetime.now(UTC)`).

## Global Constraints

- Do not implement `cast_to_string()` — separate future ticket, out of scope for VDAP-287.
- Must preserve all original columns and row count — no filtering/business-logic transforms.
- `_ingested_at` must be stamped per call (not one shared timestamp for a whole batch) — read `datetime.now(UTC)` inside the function body, not as a default arg or module constant.
- Follow existing repo conventions from `src/extract/parser.py`: plain functions, `import polars as pl`, type hints on params/return.
- Keep `tests/test_placeholder.py::test_src_extract_lineage_importable` passing (plain module import, no side effects at import time).

---

### Task 1: Implement attach_lineage() with tests

**Files:**
- Modify: `src/extract/lineage.py`
- Create: `tests/test_lineage.py`

**Interfaces:**
- Produces: `attach_lineage(df: pl.DataFrame, source_file: str, run_date: str, batch_id: str) -> pl.DataFrame` — returns a new DataFrame with original columns/rows unchanged, plus 5 new columns: `_source_file`, `_source_platform`, `_run_date`, `_ingested_at`, `_batch_id`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_lineage.py`:

```python
from datetime import datetime, UTC

import polars as pl

from src.extract import lineage


def _sample_df() -> pl.DataFrame:
    return pl.DataFrame({"id": ["1", "2", "3"], "amount": ["100", "200", "300"]})


def test_attach_lineage_adds_five_columns_with_correct_values():
    df = _sample_df()

    result = lineage.attach_lineage(
        df, source_file="SRC01_sales.csv", run_date="2026-08-04", batch_id="batch-123"
    )

    assert result["_source_file"].to_list() == ["SRC01_sales.csv"] * 3
    assert result["_source_platform"].to_list() == ["google_drive"] * 3
    assert result["_run_date"].to_list() == ["2026-08-04"] * 3
    assert result["_batch_id"].to_list() == ["batch-123"] * 3
    assert all(isinstance(v, datetime) for v in result["_ingested_at"].to_list())


def test_attach_lineage_preserves_original_columns_and_row_count():
    df = _sample_df()

    result = lineage.attach_lineage(
        df, source_file="SRC01_sales.csv", run_date="2026-08-04", batch_id="batch-123"
    )

    assert result.height == df.height
    assert result["id"].to_list() == df["id"].to_list()
    assert result["amount"].to_list() == df["amount"].to_list()
    assert set(df.columns).issubset(set(result.columns))
    assert result.width == df.width + 5


def test_attach_lineage_stamps_ingested_at_fresh_per_call():
    df = _sample_df()

    result_1 = lineage.attach_lineage(
        df, source_file="SRC01_sales.csv", run_date="2026-08-04", batch_id="batch-123"
    )
    result_2 = lineage.attach_lineage(
        df, source_file="SRC01_sales.csv", run_date="2026-08-04", batch_id="batch-123"
    )

    assert result_1["_ingested_at"][0] != result_2["_ingested_at"][0]


def test_attach_lineage_ingested_at_is_close_to_now_utc():
    df = _sample_df()
    before = datetime.now(UTC)

    result = lineage.attach_lineage(
        df, source_file="SRC01_sales.csv", run_date="2026-08-04", batch_id="batch-123"
    )

    after = datetime.now(UTC)
    stamped = result["_ingested_at"][0]
    assert before <= stamped <= after
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_lineage.py -v`
Expected: FAIL with `AttributeError: module 'src.extract.lineage' has no attribute 'attach_lineage'`

- [ ] **Step 3: Write implementation**

Replace contents of `src/extract/lineage.py`:

```python
"""Lineage metadata (attach_lineage) + String casting (cast_to_string) — filled in Epic Phase 1."""

from datetime import UTC, datetime

import polars as pl


def attach_lineage(
    df: pl.DataFrame, source_file: str, run_date: str, batch_id: str
) -> pl.DataFrame:
    return df.with_columns(
        pl.lit(source_file).alias("_source_file"),
        pl.lit("google_drive").alias("_source_platform"),
        pl.lit(run_date).alias("_run_date"),
        pl.lit(datetime.now(UTC)).alias("_ingested_at"),
        pl.lit(batch_id).alias("_batch_id"),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_lineage.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Run full test suite to check for regressions**

Run: `uv run pytest -v`
Expected: all tests pass, including `tests/test_placeholder.py::test_src_extract_lineage_importable`

- [ ] **Step 6: Commit**

```bash
git add src/extract/lineage.py tests/test_lineage.py
git commit -m "feat(VDAP-287): add attach_lineage() for Bronze lineage metadata columns"
```

---

## Self-Review Notes

- **Spec coverage:** All 5 columns (`_source_file`, `_source_platform`, `_run_date`, `_ingested_at`, `_batch_id`) covered by Step 1 tests and Step 3 implementation. Row/column preservation covered by `test_attach_lineage_preserves_original_columns_and_row_count`. Per-call fresh timestamp AC covered by `test_attach_lineage_stamps_ingested_at_fresh_per_call` and sanity-bounded by `test_attach_lineage_ingested_at_is_close_to_now_utc`.
- **Placeholder scan:** none — all steps contain literal code.
- **Type consistency:** single function, single task — no cross-task signature drift possible.
- **Out of scope confirmed:** `cast_to_string()` untouched, module docstring left as-is (already mentions it, no change needed there).
