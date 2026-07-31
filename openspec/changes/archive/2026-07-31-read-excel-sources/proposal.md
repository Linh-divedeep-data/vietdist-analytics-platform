## Why

Phase 1 Bronze ingestion needs raw source data in memory as Polars DataFrames before metadata/lineage columns can be attached and written to Parquet. 6 of the 10 VDAP sources are Excel (SRC02 sales_target_plan, SRC04 product_master, SRC05 distributor_orders, SRC07 employee_master, SRC08 territory_mapping, SRC10 promotion_program), already downloaded to `data/raw/` by `download_all_sources()`. `read_csv_sources()` (VDAP-39) covers the 4 CSV sources; nothing yet reads the 6 Excel sources into DataFrames (VDAP-40 / vdap-hy1).

## What Changes

- Add `read_excel_sources()` to `src/extract.py`: reads the 6 Excel sources from `data/raw/` via `pl.read_excel()` (fastexcel engine, per `pyproject.toml` dependency and phase1 doc hint), returns a dict keyed by source filename mapping to its Polars DataFrame.
- Add `EXCEL_SOURCES` list to `src/constants.py`, alongside the existing `CSV_SOURCES` — same separation-of-concerns rationale as VDAP-39 (file list vs. read logic).
- No changes to CSV sources (SRC01/03/06/09) — already covered by `read_csv_sources()`.
- No metadata/lineage columns, casting, or Bronze write — out of scope, handled by later Phase 1 tasks (P1.3 metadata, P1.4 Bronze write).

## Capabilities

### New Capabilities
- `excel-source-extraction`: reading VDAP's 6 Excel sources from `data/raw/` into in-memory Polars DataFrames, one per source file.

### Modified Capabilities
(none — `csv-source-extraction` spec is unaffected; this is a separate, parallel capability)

## Impact

- Code: `src/extract.py` (new function), `src/constants.py` (new `EXCEL_SOURCES` list), `tests/test_extract.py` (new tests).
- Depends on: `data/raw/*.xlsx` already present (downloaded by `download_all_sources()`); `fastexcel` already in `pyproject.toml` dependencies (needed for Polars' Excel engine — see phase1_bronze_ingestion.md hint).
- Blocks: P1.3 (lineage metadata columns) and P1.4 (Bronze Parquet write) for the 6 Excel sources.
