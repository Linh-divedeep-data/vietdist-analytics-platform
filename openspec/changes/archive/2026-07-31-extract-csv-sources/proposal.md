## Why

Phase 1 Bronze ingestion needs raw source data in memory as Polars DataFrames before metadata/lineage columns can be attached and written to Parquet. 4 of the 10 VDAP sources are CSV (SRC01 sales_transactions, SRC03 customer_master, SRC06 distributor_master, SRC09 return_transactions), already downloaded to `data/raw/` by the existing `download_all_sources()` extract step. Nothing in `src/extract.py` reads these files into DataFrames yet (VDAP-39 / vdap-bl3).

## What Changes

- Add `read_csv_sources()` to `src/extract.py`: reads the 4 CSV sources from `data/raw/` via `pl.read_csv()`, returns a dict keyed by source filename mapping to its Polars DataFrame.
- No changes to Excel sources (SRC02/04/05/07/08/10) — separate task (vdap-hy1).
- No metadata/lineage columns, casting, or Bronze write — out of scope, handled by later Phase 1 tasks (P1.3 metadata, P1.4 Bronze write).

## Capabilities

### New Capabilities
- `csv-source-extraction`: reading VDAP's 4 CSV sources from `data/raw/` into in-memory Polars DataFrames, one per source file.

### Modified Capabilities
(none — first extraction capability in this repo)

## Impact

- Code: `src/extract.py` (new function), `tests/test_extract.py` (new tests).
- Depends on: `data/raw/*.csv` already present (downloaded by `download_all_sources()`).
- Blocks: P1.3 (lineage metadata columns) and P1.4 (Bronze Parquet write) for the 4 CSV sources.
