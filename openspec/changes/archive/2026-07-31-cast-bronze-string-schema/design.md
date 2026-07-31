## Context

`attach_lineage()` (VDAP-42/43, `src/extract.py`) adds `_ingested_at` via `pl.lit(datetime.now(UTC))`, which Polars types as `pl.Datetime`. Every other column at this point is already `pl.String` (`read_csv_sources()`'s `infer_schema_length=0`, `read_excel_sources()`'s post-read cast, and `attach_lineage()`'s other 4 `pl.lit(str)` columns). `_ingested_at` is the one remaining non-String column standing between the current pipeline state and Bronze's all-String requirement.

## Goals / Non-Goals

**Goals:**
- One small, reusable `cast_to_string(df) -> pl.DataFrame` step that guarantees 100% String dtypes on any DataFrame, regardless of what non-String columns it might carry (not hardcoded to just `_ingested_at` — defensive against any future column that isn't already a string).
- Wire it into `main()` right after `attach_lineage()`, per source.

**Non-Goals:**
- Bronze Parquet write itself — separate subtasks (vdap-afa, vdap-hch), not started.
- Choosing a specific timestamp string format for `_ingested_at` — `pl.Datetime.cast(pl.String)`'s default representation is used as-is; reformatting (e.g. ISO 8601 without Polars' default separator) is a non-issue unless a downstream Silver/Gold consumer needs a specific format, which isn't the case yet.

## Decisions

- **`cast_to_string(df) -> pl.DataFrame` is a separate function, not folded into `attach_lineage()`.** Matches the Jira ticket's own scoping (VDAP-44 is a distinct subtask from VDAP-42/43) and keeps `attach_lineage()`'s responsibility (add lineage columns) separate from Bronze's schema-enforcement responsibility (all-String) — a Silver/Gold-layer caller could reuse `attach_lineage()`'s column-adding logic without inheriting Bronze's String-cast requirement, if that ever comes up.
- **`df.select(pl.all().cast(pl.String))` (exact Jira technical step), applied generically to all columns** — not a targeted cast of just `_ingested_at`. Defensive: if any future change adds another non-String column before this step runs, it's still caught automatically rather than silently breaking Bronze's invariant.
- **Wired in `main()` immediately after `attach_lineage()`, in the same loop iteration** — one DataFrame flows read → attach_lineage → cast_to_string per source, no intermediate collection/batching needed since Polars operations here are eager (already established pattern from VDAP-39/40/42/43).

## Risks / Trade-offs

- [Casting `pl.Datetime` to `pl.String` uses Polars' default datetime-to-string format, not a custom one] → Acceptable: no downstream consumer of `_ingested_at` exists yet (Silver/Gold not built), and CLAUDE.md doesn't mandate a specific string format for this column, only that it exists and is String-typed.
