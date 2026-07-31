## ADDED Requirements

### Requirement: Missing Excel engine raises a clear, actionable error
The system SHALL catch `ImportError` raised by `pl.read_excel()` inside `read_excel_sources()` when the required Excel engine (`fastexcel`) is not installed, and re-raise an `ImportError` whose message tells the caller to run `uv add fastexcel`.

#### Scenario: fastexcel not installed
- **WHEN** `read_excel_sources()` is called in an environment where the `fastexcel` package is not installed
- **THEN** an `ImportError` is raised whose message includes the instruction `uv add fastexcel`, instead of Polars' raw internal traceback

#### Scenario: fastexcel installed, read succeeds normally
- **WHEN** `read_excel_sources()` is called in an environment where `fastexcel` is installed and all `EXCEL_SOURCES` files are present
- **THEN** it returns the dict of DataFrames as before, with no behavior change from the missing-engine handling
