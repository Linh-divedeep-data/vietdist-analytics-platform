## Context

`src/extract.py` already has `read_csv_sources()` (VDAP-39), reading the 4 CSV sources from `data/raw/` with `pl.read_csv(..., infer_schema_length=0)` to force all-String Bronze fail-safe ingestion, keyed by filename, sourced from a `CSV_SOURCES` list in `src/constants.py`. VDAP-40 (vdap-hy1) needs the equivalent for the 6 Excel sources (SRC02, SRC04, SRC05, SRC07, SRC08, SRC10). `fastexcel` is already a `pyproject.toml` dependency, giving Polars its Excel engine.

## Goals / Non-Goals

**Goals:**
- Read all 6 Excel sources from `data/raw/` into a dict of Polars DataFrames, keyed by source filename, mirroring `read_csv_sources()`'s shape and error behavior.
- All-String columns at read time, consistent with Bronze's fail-safe-ingestion rule (CLAUDE.md) and matching `read_csv_sources()`.
- Missing file raises naturally (no try/except swallow) — same contract as `read_csv_sources()`.

**Non-Goals:**
- No metadata/lineage columns (`_source_file` etc.) — that's P1.3.
- No cast/dedup/NULL-handling — that's Silver (Phase 2).
- No Bronze Parquet write — that's P1.4.
- No fastexcel-engine-error fallback/retry — that's a separate tracked task (vdap-48c).

## Decisions

- **Force all-String read via `schema_overrides`**: `pl.read_csv` has `infer_schema_length=0` to force String; `pl.read_excel` has no equivalent flag. Use `pl.read_excel(path, schema_overrides={col: pl.String for col in ...})` — but column names aren't known ahead of read. Simpler: read normally then `.cast(pl.String)` on all columns via `df.select(pl.all().cast(pl.String))`, matching the Bronze-layer cast step already planned for P1.3/P1.4 (`pl.all().cast(pl.String)`, per phase1 doc). This avoids needing per-file column introspection and keeps `read_excel_sources()`'s output contract (all-String dict of DataFrames) identical to `read_csv_sources()`.
  - Alternative considered: pass `infer_schema_length=0`-equivalent via `read_options={"infer_schema_length": 0}` (fastexcel accepts some read_options) — rejected, fastexcel's Excel reader doesn't guarantee the same all-String short-circuit as the CSV reader; explicit `.cast(pl.String)` after read is deterministic and self-documenting.
- **New `EXCEL_SOURCES` list in `src/constants.py`**, parallel to `CSV_SOURCES` — same file-list/read-logic separation rationale already documented in that file's docstring (which even names `read_excel_sources` as the next consumer).
- **Function signature mirrors `read_csv_sources(raw_dir: str = "data/raw")`** for consistency and so both can be called identically from whatever P1.2 orchestration wires them together later.

## Risks / Trade-offs

- [fastexcel raises a different exception shape than expected on a corrupt/malformed Excel file, not just missing-file] → Out of scope for this change (tracked separately as vdap-48c); this change only guarantees `FileNotFoundError` propagates for missing files, matching `read_csv_sources()`'s tested contract.
- [`.cast(pl.String)` on an all-null column could raise or produce unexpected nulls-as-string] → Acceptable for Bronze fail-safe layer; downstream NULL-handling is explicitly a Silver-phase concern (CLAUDE.md), not this change's.
