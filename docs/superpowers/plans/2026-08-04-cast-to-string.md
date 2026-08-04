# cast_to_string() Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `cast_to_string(df) -> pl.DataFrame` in `src/extract/lineage.py`, which casts every column of a DataFrame to `pl.String` so no column dtype can break a Bronze write (fail-safe ingestion), including the `Datetime`-typed `_ingested_at` column left by `attach_lineage()`.

**Architecture:** Single pure function using `df.select(pl.all().cast(pl.String))` — no per-column logic, no branching, casts uniformly regardless of source dtype.

**Tech Stack:** Polars (`pl.all()`, `.cast(pl.String)`, `DataFrame.select()`).

## Global Constraints

- Only touch `src/extract/lineage.py` and `tests/test_lineage.py` — do NOT touch `src/extract/unit_of_work/base.py` (`process_source()` wiring is a separate future ticket).
- Must cast ALL columns, including `Datetime`-typed ones (e.g. `_ingested_at` from `attach_lineage()`).
- Follow existing convention in `src/extract/lineage.py`: plain function, type hints on params/return, no per-function docstring.
- Preserve existing `attach_lineage()` function and all its passing tests untouched.

---

### Task 1: Implement cast_to_string() with tests

**Files:**
- Modify: `src/extract/lineage.py`
- Modify: `tests/test_lineage.py`

**Interfaces:**
- Consumes: `lineage.attach_lineage(df, source_file, run_date, batch_id) -> pl.DataFrame` (existing, already implemented) — used in one test to produce a DataFrame containing a `Datetime` column.
- Produces: `cast_to_string(df: pl.DataFrame) -> pl.DataFrame` — returns a new DataFrame with every column cast to `pl.String`, same row/column count and column names as input.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_lineage.py` (after the existing `attach_lineage` tests, keep existing imports and `_sample_df()` as-is):

```python
def test_cast_to_string_casts_all_columns_to_string_dtype():
    df = _sample_df().with_columns(pl.col("id").cast(pl.Int64))

    result = lineage.cast_to_string(df)

    assert all(dtype == pl.String for dtype in result.dtypes)


def test_cast_to_string_casts_datetime_column_from_attach_lineage():
    df = _sample_df()
    with_lineage = lineage.attach_lineage(
        df, source_file="SRC01_sales.csv", run_date="2026-08-04", batch_id="batch-123"
    )
    assert with_lineage["_ingested_at"].dtype != pl.String  # sanity: still Datetime before cast

    result = lineage.cast_to_string(with_lineage)

    assert all(dtype == pl.String for dtype in result.dtypes)
    assert result["_ingested_at"].to_list()[0] is not None


def test_cast_to_string_preserves_columns_and_row_count():
    df = _sample_df().with_columns(pl.col("id").cast(pl.Int64))

    result = lineage.cast_to_string(df)

    assert result.columns == df.columns
    assert result.height == df.height
    assert result.width == df.width


def test_cast_to_string_preserves_values_as_strings():
    df = _sample_df().with_columns(pl.col("id").cast(pl.Int64))

    result = lineage.cast_to_string(df)

    assert result["id"].to_list() == ["1", "2", "3"]
    assert result["amount"].to_list() == ["100", "200", "300"]
```

Add `import polars as pl` reference is already present in the test file (existing `import polars as pl` line) — no new imports needed since `pl.col`/`pl.Int64` come from the same `pl` import already there.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_lineage.py -v -k cast_to_string`
Expected: FAIL with `AttributeError: module 'src.extract.lineage' has no attribute 'cast_to_string'`

- [ ] **Step 3: Write implementation**

In `src/extract/lineage.py`, append after the existing `attach_lineage()` function (no new imports needed — `pl` is already imported):

```python
def cast_to_string(df: pl.DataFrame) -> pl.DataFrame:
    return df.select(pl.all().cast(pl.String))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_lineage.py -v`
Expected: PASS (8 passed — 4 existing `attach_lineage` tests + 4 new `cast_to_string` tests)

- [ ] **Step 5: Run full test suite and lint to check for regressions**

Run: `uv run pytest -v`
Expected: all tests pass, no regressions

Run: `uvx ruff check src/extract/lineage.py tests/test_lineage.py`
Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add src/extract/lineage.py tests/test_lineage.py
git commit -m "feat(VDAP-288): add cast_to_string() to enforce all-String Bronze invariant"
```

---

## Self-Review Notes

- **Spec coverage:** `cast_to_string(df) -> pl.DataFrame` via `df.select(pl.all().cast(pl.String))` — matches Technical Steps exactly. AC ("all columns String including `_ingested_at`") covered by `test_cast_to_string_casts_all_columns_to_string_dtype` and `test_cast_to_string_casts_datetime_column_from_attach_lineage`. Value preservation and row/column count covered by `test_cast_to_string_preserves_columns_and_row_count` / `test_cast_to_string_preserves_values_as_strings`.
- **Placeholder scan:** none — all steps contain literal code.
- **Type consistency:** `cast_to_string(df: pl.DataFrame) -> pl.DataFrame` matches how it's called in all tests; consumes `attach_lineage()`'s existing exact signature/return type.
- **Out of scope confirmed:** `unit_of_work/base.py` / `process_source()` untouched — wiring is a separate ticket (2p0.7 / 2p0.2.5 per bd search), not this one.
