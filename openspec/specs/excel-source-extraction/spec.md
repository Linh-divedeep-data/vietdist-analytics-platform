# excel-source-extraction

## Purpose

TBD — extracted from the `read-excel-sources` change. Covers reading the 6 Excel data sources (`EXCEL_SOURCES` in `src/constants.py`) into Polars DataFrames during Bronze ingestion, keeping columns fail-safe as `pl.String` and letting missing-file errors propagate naturally.

## Requirements

### Requirement: Read all Excel sources into a keyed DataFrame dict
The system SHALL provide `read_excel_sources(raw_dir: str = "data/raw") -> dict[str, pl.DataFrame]` in `src/extract.py` that reads the 6 Excel sources listed in `EXCEL_SOURCES` (`src/constants.py`) from `raw_dir` and returns a dict mapping each source filename to its Polars DataFrame.

#### Scenario: Returns one DataFrame per Excel source with matching row count
- **WHEN** `read_excel_sources(raw_dir=...)` is called against a directory containing all 6 Excel source files
- **THEN** the returned dict has exactly the 6 `EXCEL_SOURCES` filenames as keys, and each DataFrame's row count (`.height`) matches the row count of its source file

### Requirement: Excel columns read as String
The system SHALL ensure every column of every DataFrame returned by `read_excel_sources()` is `pl.String` typed, consistent with Bronze's fail-safe all-String ingestion rule.

#### Scenario: All dtypes are String regardless of source column content
- **WHEN** `read_excel_sources()` reads an Excel source containing numeric, date, or text columns
- **THEN** every column's dtype in the resulting DataFrame is `pl.String`

### Requirement: Missing source file raises naturally
The system SHALL NOT catch or suppress errors when a source file listed in `EXCEL_SOURCES` is absent from `raw_dir`.

#### Scenario: Missing Excel file raises FileNotFoundError
- **WHEN** `read_excel_sources(raw_dir=...)` is called against a directory missing one or more `EXCEL_SOURCES` files
- **THEN** a `FileNotFoundError` propagates to the caller

### Requirement: Missing Excel engine raises a clear, actionable error
The system SHALL catch `ImportError` raised by `pl.read_excel()` inside `read_excel_sources()` when the required Excel engine (`fastexcel`) is not installed, and re-raise an `ImportError` whose message tells the caller to run `uv add fastexcel`.

#### Scenario: fastexcel not installed
- **WHEN** `read_excel_sources()` is called in an environment where the `fastexcel` package is not installed
- **THEN** an `ImportError` is raised whose message includes the instruction `uv add fastexcel`, instead of Polars' raw internal traceback

#### Scenario: fastexcel installed, read succeeds normally
- **WHEN** `read_excel_sources()` is called in an environment where `fastexcel` is installed and all `EXCEL_SOURCES` files are present
- **THEN** it returns the dict of DataFrames as before, with no behavior change from the missing-engine handling
