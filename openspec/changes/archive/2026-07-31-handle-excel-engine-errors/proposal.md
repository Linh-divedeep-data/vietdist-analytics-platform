## Why

`read_excel_sources()` (`src/extract.py`) calls `pl.read_excel()` with no error handling around the engine dependency. If `fastexcel` is missing or broken in an environment, Polars raises a raw `ModuleNotFoundError`/`ImportError` from deep inside its `_dependencies` internals — correct but unhelpful for a fresher-level project where the fix is a one-line `uv add fastexcel`. VDAP-41 (vdap-48c) asks for this to fail with a clear, actionable message instead of a confusing traceback.

## What Changes

- Wrap the `pl.read_excel()` call inside `read_excel_sources()` in a try/except that catches `ImportError` (the exception class `ModuleNotFoundError` — raised by Polars when `fastexcel` is missing — subclasses) and re-raises a clear error telling the user to run `uv add fastexcel`.
- Other exception types (corrupted `.xlsx`, missing file) are untouched — out of scope, already handled/tracked separately (missing file → `FileNotFoundError`, VDAP-40; malformed file → out of scope per `read-excel-sources` design.md).
- No change to `read_csv_sources()` — CSV path has no comparable optional-engine dependency.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `excel-source-extraction`: adds a new requirement — missing Excel engine dependency must raise a clear, actionable error instead of Polars' raw internal traceback.

## Impact

- Code: `src/extract.py` (`read_excel_sources()` only), `tests/test_extract.py` (new test).
- Depends on: no new dependency; only wraps existing `pl.read_excel()` call.
- Acceptance test per phase1 doc: temporarily remove `fastexcel` (`uv remove fastexcel` or equivalent), rerun `read_excel_sources()`, confirm the error message is clear guidance, not a raw traceback.
