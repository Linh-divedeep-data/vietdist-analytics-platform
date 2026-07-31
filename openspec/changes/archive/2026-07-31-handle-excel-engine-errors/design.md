## Context

`read_excel_sources()` (`src/extract.py`, added VDAP-40) calls `pl.read_excel()` for each of the 6 `EXCEL_SOURCES` files with no error handling. Polars' `read_excel()` uses `fastexcel` (Rust-based Calamine engine) as its default engine, lazily imported via `polars._dependencies.import_optional("fastexcel", min_version="0.7.0")` (confirmed in installed `polars/io/spreadsheet/functions.py`). When `fastexcel` is missing, that helper raises `ModuleNotFoundError` (a subclass of `ImportError`) with Polars' own generic `pip install fastexcel` message — functional but not tailored to this project's `uv`-based workflow, and the traceback surfaces from deep inside Polars internals rather than pointing at `read_excel_sources()`.

## Goals / Non-Goals

**Goals:**
- Catch the missing-engine case and re-raise with a clear, actionable message: run `uv add fastexcel`.
- Keep the fix scoped to `read_excel_sources()` — don't touch `read_csv_sources()` (no optional-engine dependency there).

**Non-Goals:**
- Handling corrupted/malformed `.xlsx` files (bad zip, unreadable sheet) — different exception shape entirely (fastexcel-raised parse errors, not `ImportError`), explicitly out of scope per `read-excel-sources` change's design.md.
- Falling back to an alternate engine (e.g. `xlsx2csv`, `openpyxl`) at runtime — the phase1 doc's hint ("cài thêm fastexcel hoặc xlsx2csv") is about the developer installing *a* working engine, not the code auto-switching between them. Silent engine-switching would mean different Excel-parsing behavior per environment, which is worse for reproducibility than failing fast with a clear message.
- Missing source *file* (`FileNotFoundError`) — already covered by VDAP-40, untouched by this change.

## Decisions

- **Catch `ImportError` specifically, not a bare `except Exception`.** Verified against the installed `polars` version: `import_optional()` raises `ModuleNotFoundError` (subclasses `ImportError`) when `fastexcel` isn't installed. Catching narrowly means a genuinely different failure (e.g. a real parse error on a corrupted file) still surfaces its own traceback rather than being mislabeled as "missing engine."
- **Re-raise as `ImportError` with a custom message** (not swallow-and-return, not a different exception type) — keeps the exception type semantically correct (still "an import/dependency problem") while replacing the message. Callers that already handle `ImportError` broadly aren't broken.
- **Wrap per-file inside the dict comprehension's underlying loop, not per-source-list-once** — if `fastexcel` is missing, every file in the loop will fail identically; wrapping the whole `read_excel_sources()` body (not each iteration) avoids repeating the same clear message 6 times before the first one even gets a chance to bubble up. In practice this means moving from a dict comprehension to an explicit loop with a try/except around the first `pl.read_excel()` call's failure mode — but since the failure is import-level (happens identically for every file), a single wrapping try/except around the whole function body is sufficient and simplest.

## Risks / Trade-offs

- [Polars version bump changes the internal exception class raised for missing `fastexcel`] → Mitigation: catching `ImportError` (the base class) rather than `ModuleNotFoundError` specifically is already the safer, more future-proof choice — any reasonable Polars implementation of "optional dependency missing" will raise some `ImportError` subclass.
- [Catching `ImportError` broadly could mask an unrelated `ImportError` raised from elsewhere inside Polars' Excel-reading code path for a different reason] → Accepted risk: given the narrow scope (`pl.read_excel()` call only, immediately re-raising with an *additional* clear message rather than swallowing), any such edge case still surfaces a traceback, just with an extra clarifying line — no information is lost.
