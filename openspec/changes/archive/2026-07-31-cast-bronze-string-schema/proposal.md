## Why

Bronze must be all-String (CLAUDE.md's fail-safe ingestion rule). `read_csv_sources()` already forces String at read (`infer_schema_length=0`), and `read_excel_sources()` casts to String right after reading — but `attach_lineage()` (VDAP-42/43) adds `_ingested_at` as a `pl.Datetime` column, breaking that invariant on every DataFrame after lineage is attached. VDAP-44 (vdap-am3) asks for one final cast step so every column — including the 5 lineage columns — is String before Bronze write (P1.4).

## What Changes

- Add `cast_to_string(df: pl.DataFrame) -> pl.DataFrame` to `src/extract.py`: `df.select(pl.all().cast(pl.String))`.
- Wire `main.py`: call `cast_to_string()` on each DataFrame immediately after `attach_lineage()`, before the lineage-attached log line.
- No Bronze Parquet write — still out of scope, P1.4's separate write subtasks (vdap-afa, vdap-hch) haven't started yet.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `lineage-metadata-attachment`: adds a requirement that the DataFrame returned after the Bronze pre-write pipeline (lineage attach + string cast) has 100% String dtypes, closing the gap `attach_lineage()`'s `_ingested_at` column left open.

## Impact

- Code: `src/extract.py` (new `cast_to_string()` function), `main.py` (wire the call), `tests/test_extract.py` and `tests/test_main.py` (new tests).
- Depends on: `attach_lineage()` (VDAP-42/43) already attaching the 5 metadata columns.
- Blocks: P1.4 (Bronze Parquet write) — Bronze requires all-String schema before `write_parquet()`.
