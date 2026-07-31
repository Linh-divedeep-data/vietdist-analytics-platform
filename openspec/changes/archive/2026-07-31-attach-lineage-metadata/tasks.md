## 1. attach_lineage() helper — test first (TDD)

- [x] 1.1 In `tests/test_extract.py`, add a test building a small fixture DataFrame, calling `extract.attach_lineage(df, source_file=..., run_date=..., batch_id=...)`, asserting all 5 metadata columns present with correct values and original columns/rows unchanged
- [x] 1.2 Run `uv run pytest tests/test_extract.py -k attach_lineage -v`, confirm it fails (`AttributeError: module 'src.extract' has no attribute 'attach_lineage'`)

## 2. attach_lineage() helper — implementation

- [x] 2.1 In `src/extract.py`, add `attach_lineage(df: pl.DataFrame, source_file: str, run_date: str, batch_id: str) -> pl.DataFrame` using `with_columns()` per Jira technical steps (5 `pl.lit(...)` columns)
- [x] 2.2 Run the test from 1.1 again, confirm it passes
- [x] 2.3 Add a second test: calling `attach_lineage()` twice in quick succession produces two DataFrames whose `_ingested_at` values are both valid timestamps (not asserting exact equality, since each call stamps its own time)

## 3. Wire main.py — test first (TDD)

- [x] 3.1 In `tests/test_main.py`, add a test monkeypatching `extract.read_csv_sources`/`extract.read_excel_sources` to return small fixture dicts (e.g. 2 fake CSV + 2 fake Excel entries) and `extract.attach_lineage` to record its call args; run `main()`; assert `attach_lineage` was called once per fixture entry (not necessarily 10, given fixtures), and every call received the same `batch_id` that `main()` returned
- [x] 3.2 Run `uv run pytest tests/test_main.py -k lineage -v`, confirm it fails (main.py doesn't call read_csv_sources/read_excel_sources/attach_lineage yet)

## 4. Wire main.py — implementation

- [x] 4.1 In `main.py`, import `datetime` and compute `run_date = datetime.now().strftime("%Y-%m-%d")` once per run (placeholder pending real `--run-date` CLI arg, vdap-24y) — add inline comment noting this
- [x] 4.2 After the existing `download_all_sources()` call, call `extract.read_csv_sources()` and `extract.read_excel_sources()`, loop each dict's items calling `extract.attach_lineage(df, source_file=name, run_date=run_date, batch_id=batch_id)`
- [x] 4.3 Log a one-line summary (count of sources lineage-attached), same pattern as the existing extract-done log line
- [x] 4.4 Run the test from 3.1 again, confirm it passes
- [x] 4.5 Update the existing `test_main_calls_download_all_sources_with_folder_id_and_batch_id`-style fixture/mocks if the new calls break it (mock `read_csv_sources`/`read_excel_sources`/`attach_lineage` in the shared autouse fixture so unrelated tests aren't forced to touch real `data/raw/`)

## 5. Verification

- [x] 5.1 Run full `uv run pytest tests/test_extract.py tests/test_main.py -v`, confirm all tests pass, no regressions
- [x] 5.2 Manually run `uv run python main.py` against real `data/raw/` (10 real files present), confirm no crash and log summary shows 10 sources processed
- [x] 5.3 Run `uv run ruff check src/extract.py main.py tests/test_extract.py tests/test_main.py`
