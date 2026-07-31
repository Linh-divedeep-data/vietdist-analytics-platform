## 1. Test (TDD — write and watch fail first)

- [x] 1.1 In `tests/test_extract.py`, add a test that monkeypatches `pl.read_excel` to raise `ImportError("fastexcel not found")`, asserts `read_excel_sources()` raises `ImportError` with `uv add fastexcel` in the message
- [x] 1.2 Run `uv run pytest tests/test_extract.py -k engine -v`, confirm it fails (currently the raw `ImportError` propagates unchanged, message won't contain `uv add fastexcel`)

## 2. Implementation

- [x] 2.1 In `src/extract.py`, wrap `read_excel_sources()`'s body in a try/except catching `ImportError`
- [x] 2.2 On catch, re-raise `ImportError` with message including `uv add fastexcel` guidance, chaining the original exception (`raise ... from e`)
- [x] 2.3 Run the test from 1.1 again, confirm it passes
- [x] 2.4 Confirm the happy path (fastexcel installed) is unaffected — no behavior change when there's no error

## 3. Verification

- [x] 3.1 Run full `uv run pytest tests/test_extract.py -v`, confirm all tests pass, no regressions on existing `read_excel_sources()` tests (row count, all-String dtype, missing-file `FileNotFoundError`)
- [x] 3.2 Manually verify acceptance criteria: `uv remove fastexcel` (or rename its dist-info), run `read_excel_sources()` against real `data/raw/`, confirm the clear `uv add fastexcel` message appears (not a raw Polars traceback), then reinstall (`uv add fastexcel`)
- [x] 3.3 Run `uv run ruff check src/extract.py tests/test_extract.py`
