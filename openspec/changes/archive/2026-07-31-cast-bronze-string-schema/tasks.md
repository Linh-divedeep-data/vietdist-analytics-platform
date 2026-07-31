## 1. cast_to_string() — test first (TDD)

- [x] 1.1 In `tests/test_extract.py`, add a test: build a DataFrame via `attach_lineage()` (so `_ingested_at` is `pl.Datetime`), call `extract.cast_to_string()` on it, assert every column dtype is `pl.String`
- [x] 1.2 Add a second test: `cast_to_string()` on an already-all-String DataFrame leaves values/dtypes unchanged
- [x] 1.3 Run `uv run pytest tests/test_extract.py -k cast_to_string -v`, confirm it fails (`AttributeError: module 'src.extract' has no attribute 'cast_to_string'`)

## 2. cast_to_string() — implementation

- [x] 2.1 In `src/extract.py`, add `cast_to_string(df: pl.DataFrame) -> pl.DataFrame` returning `df.select(pl.all().cast(pl.String))`
- [x] 2.2 Run the tests from 1.1/1.2 again, confirm they pass

## 3. Wire main.py — test first (TDD)

- [x] 3.1 In `tests/test_main.py`, extend or add a test that monkeypatches `extract.attach_lineage` to return a sentinel value and `extract.cast_to_string` to record its call args; run `main()`; assert `cast_to_string` was called once per source, each call receiving the value `attach_lineage` returned for that source
- [x] 3.2 Run `uv run pytest tests/test_main.py -k cast -v`, confirm it fails (main.py doesn't call `cast_to_string` yet)

## 4. Wire main.py — implementation

- [x] 4.1 In `main.py`, call `extract.cast_to_string(...)` on the result of each `attach_lineage()` call, same loop iteration
- [x] 4.2 Run the test from 3.1 again, confirm it passes
- [x] 4.3 Add `cast_to_string` to the shared autouse mock fixture in `tests/test_main.py` (pass-through no-op) so unrelated tests aren't affected

## 5. Verification

- [x] 5.1 Run full `uv run pytest tests/test_extract.py tests/test_main.py -v`, confirm all tests pass, no regressions
- [x] 5.2 Manually run `uv run python main.py` against real `data/raw/`, confirm no crash; spot-check in a REPL that a lineage-attached + cast DataFrame has `df.dtypes` entirely `pl.String`
- [x] 5.3 Run `uv run ruff check src/extract.py main.py tests/test_extract.py tests/test_main.py`
