## Context

`src/extract.py` has `read_csv_sources()` (4 sources) and `read_excel_sources()` (6 sources), both returning `dict[str, pl.DataFrame]` keyed by filename, no metadata columns. `main.py` generates one `batch_id = str(uuid.uuid4())` at the top of `main()` (VDAP-27) and currently only passes it to `download_all_sources()`. Nothing yet reads the physical files into DataFrames from within `main()`, and nothing attaches the 5 lineage columns CLAUDE.md requires (`_source_file`, `_source_platform`, `_run_date`, `_ingested_at`, `_batch_id`). This change closes that gap up to (but not including) the Bronze Parquet write, which is P1.4's job.

## Goals / Non-Goals

**Goals:**
- One reusable `attach_lineage(df, source_file, run_date, batch_id) -> pl.DataFrame` helper, usable identically for CSV- and Excel-sourced DataFrames.
- Wire `main()` to read all 10 sources and attach lineage to each, using the single `batch_id` already generated once per run — satisfying VDAP-43's "all 10 share the same `_batch_id`" acceptance criteria in-memory.
- Keep `attach_lineage()` itself agnostic to where `run_date` comes from (just a string parameter) — no coupling to CLI parsing.

**Non-Goals:**
- Bronze Parquet write — explicitly out of scope per parent story VDAP-33, handled by P1.4 (vdap-hch/vdap-afa/vdap-am3).
- Real `--run-date` CLI argument parsing — separate tracked task (vdap-24y, S1 CLI orchestration argparse). This change uses a placeholder (`datetime.now()` formatted `YYYY-MM-DD`) inside `main()` so the pipeline is runnable end-to-end today; swapping the placeholder for a real parsed CLI arg later is a one-line change in `main()`, not in `attach_lineage()`.
- `ingest_log` (rows_loaded/status/duration_sec) — separate task (P1.5, vdap-izy/vdap-2ej/vdap-779).

## Decisions

- **`attach_lineage()` takes primitives (`source_file: str`, `run_date: str`, `batch_id: str`), not a config object.** Matches the Jira technical steps exactly (`attach_lineage(df, source_file, run_date, batch_id)`) and keeps the function trivially testable with plain values — no premature abstraction for a 4-argument helper.
- **`_ingested_at` uses `datetime.now()` evaluated once per `attach_lineage()` call, not passed in.** Each source's ingestion timestamp is naturally the moment it's processed; passing it in from the caller would just move `datetime.now()` up one level for no benefit, and per-source timestamps (rather than one shared timestamp) are more accurate lineage — download/read time can differ slightly per file.
- **`main()` computes `run_date` once via `datetime.now().strftime("%Y-%m-%d")` and passes the same value to all 10 `attach_lineage()` calls** — one run, one `run_date`, matching how `batch_id` is already handled. This is a placeholder pending vdap-24y's real `--run-date` argparse wiring; documented inline with a comment referencing that ticket so it isn't mistaken for a permanent design choice.
- **`main()` reads via `read_csv_sources()` + `read_excel_sources()` (dicts), then loops both dicts calling `attach_lineage(df, source_file=name, ...)` for each entry** — reuses the existing dict-of-DataFrame contract rather than introducing a new combined "read all 10" function; keeps `read_csv_sources`/`read_excel_sources` single-responsibility (read only) and `attach_lineage` single-responsibility (attach only), composed in `main()`.
- **No file write, no return-value change to `main()` beyond what's needed for testing** — `main()` still returns `batch_id` (existing contract, tested by `test_main.py`); the 10 lineage-attached DataFrames aren't persisted or returned anywhere yet since there's nowhere for them to go until P1.4. For testability, `main()` logs a one-line summary (count of sources processed) the same way it already does for `download_all_sources()`'s success/fail counts — this gives the acceptance criteria ("all 10 share `_batch_id`") a natural place to be asserted in a test (by capturing the DataFrames via a monkeypatched `attach_lineage` and checking the `batch_id` argument each call received).

## Risks / Trade-offs

- [`run_date` placeholder (`datetime.now()`) means every real run's `_run_date` is "today", not a chosen backfill/replay date] → Acceptable short-term: CLAUDE.md's idempotency model partitions by `run_date`, but partitioning/Bronze-write isn't implemented yet in this change (P1.4). Mitigation: inline comment + this design doc flag it clearly so vdap-24y's argparse work is the obvious next step, not a forgotten one.
- [Looping two separate dicts (`read_csv_sources()` + `read_excel_sources()`) in `main()` duplicates the same 3-line attach loop twice] → Accepted: 2 loops of 3 lines each is simpler and more readable than introducing a combined-read abstraction for only 10 total files; not worth the abstraction per project's anti-premature-abstraction guidance.
