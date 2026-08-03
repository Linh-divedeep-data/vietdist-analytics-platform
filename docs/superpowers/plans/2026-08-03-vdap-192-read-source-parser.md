# VDAP-192: read_csv_source()/read_excel_source() Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `read_csv_source(name, raw_dir)` and `read_excel_source(name, raw_dir)` to `src/extract/parser.py` so any single-source CSV or Excel file is read into a Polars DataFrame with every column cast to `String` at read time (fail-safe ingestion), without touching the existing `download_all_sources()` in the same file.

**Architecture:** Two standalone functions, each taking a bare filename (`name`) and a directory (`raw_dir`, default `"data/raw"`), joining them into a `Path`, and returning a `pl.DataFrame`. CSV forces string typing via `infer_schema_length=0` (native Polars option — no post-read cast needed). Excel reads then explicitly casts every column via `.select(pl.all().cast(pl.String))`, because `pl.read_excel` has no equivalent "read everything as string" flag. Missing files are **not** caught — Polars/fastexcel already raise `FileNotFoundError` naturally for both formats (verified manually: `pl.read_csv`/`pl.read_excel` on a nonexistent path both raise real `FileNotFoundError`, not a custom or generic exception). Only `ImportError` (missing `fastexcel` engine) is caught in the Excel path, and re-raised with an actionable message.

**Tech Stack:** Polars (`polars>=1.43.2`, already in `pyproject.toml`), `fastexcel>=0.20.2` (already in `pyproject.toml`, provides the Excel read engine). No new dependencies.

## Global Constraints

- Do not modify `download_all_sources()` or its imports/tests in `src/extract/parser.py` / `tests/test_parser.py` — append only.
- `raw_dir` default is the literal string `"data/raw"` — `config/settings.py` has no real `RAW_DIR` constant yet (docstring placeholder only), so do not import from it.
- Do not use `config/sources.py` (`CSV_SOURCES`/`EXCEL_SOURCES`) in this file — these two functions read one named file at a time; list-driven looping is a later ticket's job.
- No new custom exception classes — AC only requires natural `FileNotFoundError` propagation and a re-raised `ImportError` with guidance text.
- No new dependencies — `fastexcel` is already installed, so real Excel test fixtures can't be hand-authored without an xlsx *writer* library (not installed, and out of scope to add). Excel tests mock `pl.read_excel` at the boundary (same style the existing tests in this file already use for `list_files_in_folder`/`download_file`).
- CSV tests use real files via `tmp_path` — no mocking needed since CSV is plain text.

---

### Task 1: `read_csv_source()`

**Files:**
- Modify: `src/extract/parser.py` (append function + `from pathlib import Path` and `import polars as pl` to the existing imports)
- Test: `tests/test_parser.py` (append tests after the existing 4)

**Interfaces:**
- Produces: `read_csv_source(name: str, raw_dir: str = "data/raw") -> pl.DataFrame`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_parser.py`:

```python
import polars as pl


def test_read_csv_source_casts_all_columns_to_string(tmp_path):
    csv_path = tmp_path / "SRC01_sales.csv"
    csv_path.write_text("id,amount,note\n1,100.5,ok\n2,200.75,ok\n3,300,ok\n")

    df = parser.read_csv_source("SRC01_sales.csv", raw_dir=str(tmp_path))

    assert df.height == 3
    assert all(dtype == pl.String for dtype in df.dtypes)
    assert df["id"].to_list() == ["1", "2", "3"]
    assert df["amount"].to_list() == ["100.5", "200.75", "300"]


def test_read_csv_source_missing_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        parser.read_csv_source("does_not_exist.csv", raw_dir=str(tmp_path))


def test_read_csv_source_default_raw_dir_is_data_raw(monkeypatch):
    captured = {}

    def fake_read_csv(path, infer_schema_length):
        captured["path"] = path
        captured["infer_schema_length"] = infer_schema_length
        return pl.DataFrame({"a": ["1"]})

    monkeypatch.setattr(parser.pl, "read_csv", fake_read_csv)

    parser.read_csv_source("SRC01_sales.csv")

    assert str(captured["path"]) == "data/raw/SRC01_sales.csv"
    assert captured["infer_schema_length"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_parser.py -k read_csv_source -v`
Expected: FAIL with `AttributeError: module 'src.extract.parser' has no attribute 'read_csv_source'`

- [ ] **Step 3: Write minimal implementation**

At the top of `src/extract/parser.py`, add to the existing imports:

```python
from pathlib import Path

import polars as pl
```

Append this function to `src/extract/parser.py`:

```python
def read_csv_source(name: str, raw_dir: str = "data/raw") -> pl.DataFrame:
    path = Path(raw_dir) / name
    return pl.read_csv(path, infer_schema_length=0)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_parser.py -k read_csv_source -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add src/extract/parser.py tests/test_parser.py
git commit -m "feat(VDAP-192): add read_csv_source() casting all columns to String"
```

---

### Task 2: `read_excel_source()`

**Files:**
- Modify: `src/extract/parser.py`
- Test: `tests/test_parser.py`

**Interfaces:**
- Consumes: nothing from Task 1 (independent function, same file).
- Produces: `read_excel_source(name: str, raw_dir: str = "data/raw") -> pl.DataFrame`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_parser.py`:

```python
def test_read_excel_source_casts_all_columns_to_string(monkeypatch):
    fake_df = pl.DataFrame({"id": [1, 2], "amount": [10.5, 20.0]})
    monkeypatch.setattr(parser.pl, "read_excel", lambda path: fake_df)

    df = parser.read_excel_source("SRC02_target.xlsx", raw_dir="data/raw")

    assert df.height == 2
    assert all(dtype == pl.String for dtype in df.dtypes)
    assert df["id"].to_list() == ["1", "2"]


def test_read_excel_source_missing_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        parser.read_excel_source("does_not_exist.xlsx", raw_dir=str(tmp_path))


def test_read_excel_source_reraises_import_error_with_install_hint(monkeypatch):
    def fake_read_excel(path):
        raise ImportError("no Excel engine found")

    monkeypatch.setattr(parser.pl, "read_excel", fake_read_excel)

    with pytest.raises(ImportError, match="uv add fastexcel"):
        parser.read_excel_source("SRC02_target.xlsx", raw_dir="data/raw")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_parser.py -k read_excel_source -v`
Expected: FAIL with `AttributeError: module 'src.extract.parser' has no attribute 'read_excel_source'`

- [ ] **Step 3: Write minimal implementation**

Append to `src/extract/parser.py`:

```python
def read_excel_source(name: str, raw_dir: str = "data/raw") -> pl.DataFrame:
    path = Path(raw_dir) / name
    try:
        df = pl.read_excel(path)
    except ImportError as error:
        raise ImportError(
            f"Missing Excel engine to read {path} — run `uv add fastexcel`"
        ) from error
    return df.select(pl.all().cast(pl.String))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_parser.py -k read_excel_source -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add src/extract/parser.py tests/test_parser.py
git commit -m "feat(VDAP-192): add read_excel_source() with fastexcel ImportError guidance"
```

---

### Task 3: Full-suite verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full test file**

Run: `uv run pytest tests/test_parser.py -v`
Expected: all tests pass (4 pre-existing `download_all_sources` tests + 6 new tests = 10 passed), no regressions.

- [ ] **Step 2: Run the full project test suite**

Run: `uv run pytest -v`
Expected: all tests across the repo pass, nothing else broken by the new imports (`Path`, `polars`) in `parser.py`.

- [ ] **Step 3: Commit (only if Task 3 caused any fix-up changes)**

Skip commit if Step 1/2 pass cleanly with no code changes — Tasks 1 and 2 already committed the real work.

---

## Self-Review Notes

- **Spec coverage:** `read_csv_source` (Task 1), `read_excel_source` (Task 2), all-String cast for both, natural `FileNotFoundError` for both (tested), `ImportError` → `uv add fastexcel` guidance (tested) — all AC items covered.
- **No placeholders:** all test and implementation code is complete and runnable as written.
- **Type consistency:** both functions share the exact signature shape `(name: str, raw_dir: str = "data/raw") -> pl.DataFrame` used consistently across both tasks.
