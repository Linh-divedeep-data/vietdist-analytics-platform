## Why

Bronze ingestion requires 5 lineage metadata columns (`_source_file`, `_source_platform`, `_run_date`, `_ingested_at`, `_batch_id`) on every DataFrame before it can be written to Bronze Parquet (P1.4) — CLAUDE.md's non-negotiable data-lineage rule. Right now `read_csv_sources()`/`read_excel_sources()` (VDAP-39/40) return bare DataFrames with no metadata, and `main.py` generates one `batch_id` per run (VDAP-27) but never threads it anywhere past `download_all_sources()`. VDAP-42 (vdap-sho) asks for a reusable `attach_lineage()` helper; VDAP-43 (vdap-000) asks for that one `batch_id` to reach all 10 sources consistently. Both are subtasks of the same parent story (VDAP-33 / P1.3) and are sequential (VDAP-43 needs VDAP-42's function to exist), so this change covers both together.

## What Changes

- Add `attach_lineage(df: pl.DataFrame, source_file: str, run_date: str, batch_id: str) -> pl.DataFrame` to `src/extract.py`, using `with_columns()` to add the 5 metadata columns per the Jira technical steps.
- Wire `main.py`: after `download_all_sources()`, read all 10 sources (`read_csv_sources()` + `read_excel_sources()`) and call `attach_lineage()` on each of the 10 resulting DataFrames, passing the single `batch_id` already generated at the top of `main()` — so all 10 share the same `_batch_id`.
- `run_date` is a placeholder (`datetime.now()` date, formatted `YYYY-MM-DD`) inside `main()` for now — real `--run-date` CLI wiring is a separate tracked task (vdap-24y, argparse setup) not yet implemented; `attach_lineage()` itself just accepts `run_date` as a parameter, agnostic to where it comes from.
- No Bronze Parquet write — explicitly out of scope per the parent story (VDAP-33), tracked separately (P1.4).

## Capabilities

### New Capabilities
- `lineage-metadata-attachment`: attaching the 5 Bronze lineage metadata columns to any DataFrame via a reusable helper, and ensuring one shared `batch_id` reaches all 10 sources per pipeline run.

### Modified Capabilities
(none — `csv-source-extraction` and `excel-source-extraction` specs are unaffected; this change consumes their output, doesn't change their read contract)

## Impact

- Code: `src/extract.py` (new `attach_lineage()` function), `main.py` (wire read + attach for all 10 sources), `tests/test_extract.py` and `tests/test_main.py` (new tests).
- Depends on: `read_csv_sources()` (VDAP-39), `read_excel_sources()` (VDAP-40) already returning dict-of-DataFrame; `main()`'s existing `batch_id` generation (VDAP-27).
- Blocks: P1.4 (Bronze Parquet write) — needs lineage columns present before writing.
