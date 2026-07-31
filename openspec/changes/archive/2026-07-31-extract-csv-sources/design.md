## Context

`src/extract.py` currently has `download_all_sources()` which pulls all 10 SRC files from Google Drive into `data/raw/`. The next Phase 1 step (P1.2) is reading the physical files into Polars DataFrames. CSV sources (SRC01, SRC03, SRC06, SRC09) are the simpler half — no Excel engine concerns — and are the scope of VDAP-39.

## Goals / Non-Goals

**Goals:**
- Read the 4 CSV sources from `data/raw/` into Polars DataFrames via `pl.read_csv()`.
- Return them keyed by source filename so downstream code (metadata attachment, Bronze write) can iterate consistently.
- Raw directory path configurable (not hardcoded), so tests can point at a tmp dir instead of real `data/raw/`.

**Non-Goals:**
- Excel sources (separate function/task, vdap-hy1).
- Type casting, lineage metadata columns, Bronze Parquet write — all later Phase 1 tasks.
- Lazy evaluation (`pl.scan_csv`) — CLAUDE.md's lazy-eval rule applies to Silver/Gold reading from Bronze Parquet, not this raw Bronze-landing read; Bronze intentionally reads eagerly since it force-casts everything to String right after.

## Decisions

- **One function, `read_csv_sources(raw_dir="data/raw")`, returns `dict[str, pl.DataFrame]`.** Mirrors the existing `download_all_sources()` shape (explicit, no hidden global state) and keeps the CSV_SOURCES list colocated as the single source of truth for which 4 files this function handles.
- **`raw_dir` parameter instead of hardcoded `data/raw`.** Matches how `test_extract.py` already tests `download_all_sources` via monkeypatch/fakes rather than touching the real filesystem — here we use `tmp_path` fixture with real CSV content instead, since `pl.read_csv` has no seams to fake without an unnecessary abstraction.
- **No per-file error handling in this function.** Unlike `download_all_sources()` (network calls, expected to fail), a missing/malformed local CSV after successful download is an unexpected state — let `pl.read_csv` raise naturally. Per-file error handling for extraction-level failures is a separate concern if/when it's needed (not in VDAP-39's acceptance criteria).

## Risks / Trade-offs

- [Hardcoded CSV_SOURCES list drifts from actual `data/raw/` contents if a source is renamed] → Mitigation: acceptance criteria already requires exact row-count match against source file, which would fail loudly (FileNotFoundError) rather than silently skip.
