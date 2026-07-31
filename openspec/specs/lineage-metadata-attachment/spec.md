# lineage-metadata-attachment

## Purpose

TBD — extracted from the `attach-lineage-metadata` change. Covers attaching the 5 mandatory Bronze lineage metadata columns (`_source_file`, `_source_platform`, `_run_date`, `_ingested_at`, `_batch_id`) to every source DataFrame during Bronze ingestion, and ensuring a single shared `batch_id` is used across all 10 sources within one pipeline run.

## Requirements

### Requirement: Reusable lineage attachment helper
The system SHALL provide `attach_lineage(df: pl.DataFrame, source_file: str, run_date: str, batch_id: str) -> pl.DataFrame` in `src/extract.py` that returns a new DataFrame with 5 metadata columns added: `_source_file` (the given `source_file`), `_source_platform` (literal `"google_drive"`), `_run_date` (the given `run_date`), `_ingested_at` (current timestamp at call time), `_batch_id` (the given `batch_id`).

#### Scenario: All 5 metadata columns present with correct values
- **WHEN** `attach_lineage(df, source_file="SRC01_sales_transactions.csv", run_date="2026-07-31", batch_id="abc-123")` is called on any DataFrame
- **THEN** the returned DataFrame has all original columns plus `_source_file="SRC01_sales_transactions.csv"`, `_source_platform="google_drive"`, `_run_date="2026-07-31"`, `_batch_id="abc-123"` on every row, and `_ingested_at` populated with a timestamp

#### Scenario: Original data untouched
- **WHEN** `attach_lineage()` is called on a DataFrame with existing columns and rows
- **THEN** all original columns and row values are preserved unchanged in the returned DataFrame, only the 5 metadata columns are added

### Requirement: One batch_id shared across all 10 sources per run
The system SHALL ensure that a single pipeline run (one call to `main()`) generates exactly one `batch_id` and passes that same value to `attach_lineage()` for all 10 sources (4 CSV + 6 Excel).

#### Scenario: All 10 sources receive the same batch_id
- **WHEN** `main()` runs one full pipeline invocation
- **THEN** `attach_lineage()` is called once per source (10 times total: 4 from `read_csv_sources()`, 6 from `read_excel_sources()`), and every call receives the identical `batch_id` value that `main()` generated at the start of the run

#### Scenario: Two separate runs get different batch_ids
- **WHEN** `main()` is called twice (two separate runs)
- **THEN** all `attach_lineage()` calls within the first run share one `batch_id`, all calls within the second run share a different `batch_id`, and the two `batch_id` values differ from each other
