# VDAP-174 Config + src/extract Package Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the `config/` and `src/extract/` (+ `src/extract/unit_of_work/`) packages as empty/stub modules so Epic Phase 1 (Bronze ingestion) has a fixed place to put each piece of logic instead of one growing `extract.py`.

**Architecture:** Plain Python packages (`__init__.py` per directory) with one-line docstring stub files — no logic, no imports between the new modules yet. `pyproject.toml` has no `[build-system]` section, so `uv run` just adds the project root to `sys.path`; no packaging/build-backend config needed for these new top-level dirs to be importable.

**Tech Stack:** Python package layout only (no dependencies added).

## Global Constraints

- Exact file list (Jira VDAP-174 Deliverable) — 10 files, plus `src/__init__.py` which the Technical Steps' "tạo `__init__.py` rỗng ở mỗi package" line implies since `src` is itself now a package root:
  - `config/__init__.py`, `config/sources.py`, `config/settings.py`
  - `src/__init__.py`, `src/extract/__init__.py`, `src/extract/parser.py`, `src/extract/lineage.py`, `src/extract/registry.py`, `src/extract/orchestrator.py`, `src/extract/ingest_log.py`
  - `src/extract/unit_of_work/__init__.py`, `src/extract/unit_of_work/base.py`
- Explicit non-goal (Jira, bold): "KHÔNG viết logic thật ở subtask này, chỉ dựng khung" — stub files only, no functions/classes with real behavior.
- AC: `import config.sources, config.settings, src.extract.parser, src.extract.lineage, src.extract.registry, src.extract.orchestrator, src.extract.ingest_log, src.extract.unit_of_work.base` — zero `ImportError`.

---

### Task 1: Scaffold config/ and src/extract/ packages as stubs

**Files:**
- Create: `config/__init__.py` (empty)
- Create: `config/sources.py`
- Create: `config/settings.py`
- Create: `src/__init__.py` (empty)
- Create: `src/extract/__init__.py` (empty)
- Create: `src/extract/parser.py`
- Create: `src/extract/lineage.py`
- Create: `src/extract/registry.py`
- Create: `src/extract/orchestrator.py`
- Create: `src/extract/ingest_log.py`
- Create: `src/extract/unit_of_work/__init__.py` (empty)
- Create: `src/extract/unit_of_work/base.py`

**Interfaces:**
- Consumes: nothing (first task in ticket)
- Produces: importable but empty modules — Epic Phase 1 tickets fill in real functions (`read_csv_source()`, `attach_lineage()`, `cast_to_string()`, `UNIT_OF_WORK` registry dict, `run_bronze_ingestion()`, `build_ingest_log_record()`, `process_source()` in `unit_of_work/base.py`) inside these exact files — no renaming later.

- [ ] **Step 1: Create the directory tree**

Run: `mkdir -p config src/extract/unit_of_work`
Expected: exit code 0 (`src/` already exists from VDAP-171 with a `.gitkeep`, `mkdir -p` is a no-op for it).

- [ ] **Step 2: Create empty `__init__.py` for every package**

Run:
```bash
touch config/__init__.py src/__init__.py src/extract/__init__.py src/extract/unit_of_work/__init__.py
```
Expected: exit code 0, 4 empty files.

- [ ] **Step 3: Create `config/sources.py` stub**

File content:
```python
"""Source registry (CSV_SOURCES, EXCEL_SOURCES, REQUIRED_COLUMNS) — filled in Epic Phase 1 (VDAP-92)."""
```

- [ ] **Step 4: Create `config/settings.py` stub**

File content:
```python
"""Path constants (RAW_DIR, BRONZE_DIR, SILVER_DIR, GOLD_DIR) — filled in Epic Phase 1. No credentials here (see risk register in VDAP-168)."""
```

- [ ] **Step 5: Create `src/extract/parser.py` stub**

File content:
```python
"""CSV/Excel readers (read_csv_source, read_excel_source) + validate_schema() — filled in Epic Phase 1."""
```

- [ ] **Step 6: Create `src/extract/lineage.py` stub**

File content:
```python
"""Lineage metadata (attach_lineage) + String casting (cast_to_string) — filled in Epic Phase 1."""
```

- [ ] **Step 7: Create `src/extract/registry.py` stub**

File content:
```python
"""UNIT_OF_WORK: maps each of the 10 sources to its unit_of_work module — filled in Epic Phase 1."""
```

- [ ] **Step 8: Create `src/extract/orchestrator.py` stub**

File content:
```python
"""run_bronze_ingestion(): main loop over registry.UNIT_OF_WORK + Parquet write — filled in Epic Phase 1."""
```

- [ ] **Step 9: Create `src/extract/ingest_log.py` stub**

File content:
```python
"""build_ingest_log_record() + write_ingest_log() — filled in Epic Phase 1 (VDAP-116-118)."""
```

- [ ] **Step 10: Create `src/extract/unit_of_work/base.py` stub**

File content:
```python
"""process_source(): shared per-source read+lineage+write flow used by every unit_of_work/srcXX_*.py — filled in Epic Phase 1."""
```

- [ ] **Step 11: Verify the AC — every module imports clean**

Run:
```bash
uv run python -c "import config.sources, config.settings, src.extract.parser, src.extract.lineage, src.extract.registry, src.extract.orchestrator, src.extract.ingest_log, src.extract.unit_of_work.base"
```
Expected: no output, exit code 0.

- [ ] **Step 12: Commit**

```bash
git add config/ src/__init__.py src/extract/
git commit -m "feat(VDAP-174): scaffold config/ + src/extract/ package skeleton"
```

---

## Self-Review

**1. Spec coverage:** All 10 Jira-listed files present (Steps 3-10 + the two `__init__.py` pairs in Step 2), plus `src/__init__.py` justified above. AC import list covered verbatim in Step 11. No gaps.
**2. Placeholder scan:** No TBD/TODO/"implement later" phrasing — each stub is a real one-line docstring naming the future function names (useful breadcrumb, not a fake implementation), exactly matching the ticket's "chỉ dựng khung" instruction.
**3. Type consistency:** N/A — no functions/classes defined yet, only module docstrings; future function names named in the docstrings are cross-referenced from the ticket descriptions (VDAP-168 Epic, bd children `2p0.*`) so later tickets land in the right file.
