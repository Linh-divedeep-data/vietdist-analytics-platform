## 1. Test (TDD — write and watch fail first)

- [x] 1.1 In `tests/test_extract.py`, add a test that calls `extract.read_csv_sources(raw_dir=<tmp_path>)` against 4 fixture CSV files written to `tmp_path`, and asserts the returned dict has exactly the 4 expected source filenames as keys
- [x] 1.2 Extend the same test (or add another) to assert each DataFrame's `.height` matches the known row count of its fixture file, and is > 0
- [x] 1.3 Run `uv run pytest tests/test_extract.py -k read_csv_sources -v`, confirm it fails with `AttributeError: module 'src.extract' has no attribute 'read_csv_sources'`

## 2. Implementation

- [x] 2.1 In `src/extract.py`, add `CSV_SOURCES` list with the 4 filenames (SRC01_sales_transactions.csv, SRC03_customer_master.csv, SRC06_distributor_master.csv, SRC09_return_transactions.csv)
- [x] 2.2 Add `read_csv_sources(raw_dir: str = "data/raw") -> dict[str, pl.DataFrame]` that reads each file in `CSV_SOURCES` from `raw_dir` via `pl.read_csv()` and returns the dict
- [x] 2.3 Run the test from 1.3 again, confirm it passes

## 3. Verification

- [x] 3.1 Run full `uv run pytest tests/test_extract.py -v`, confirm all tests pass (no regressions on `download_all_sources` tests)
- [x] 3.2 Manually run `read_csv_sources()` against the real `data/raw/` directory (already populated), confirm 4 DataFrames returned with row counts > 0
