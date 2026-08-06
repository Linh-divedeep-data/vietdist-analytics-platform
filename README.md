# VietDist Analytics Platform

[![CI](https://github.com/Linh-divedeep-data/vietdist-analytics-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/Linh-divedeep-data/vietdist-analytics-platform/actions/workflows/ci.yml)

A Bronze/Silver/Gold data lakehouse pipeline for **VietDist**, a fictional FMCG distributor. It ingests 10 raw CSV/Excel sources from Google Drive, cleans and standardizes them, and models a Kimball star schema (7 dimensions, 4 facts, 1 mart) ready for ad-hoc SQL or BI consumption — no database server required, just Parquet files on disk.

> Personal portfolio project (Data Engineer track). Business context, actors, and requirements are documented in [`docs/BRD_Solution_Architecture.md`](docs/BRD_Solution_Architecture.md).

## Architecture

```
Google Drive (10 sources)
        │  gdrive_connector.py
        ▼
┌───────────────┐   raw CSV/Excel, unmodified
│  data/raw/    │
└───────┬───────┘
        │  src/extract/  (schema validation, lineage columns, idempotent write)
        ▼
┌───────────────┐   + _source_file, _batch_id, _run_date, ... ; ingest_log.parquet
│  data/bronze/ │
└───────┬───────┘
        │  src/transform/silver/  (type casts, dedup, NULL handling, text standardization)
        ▼
┌───────────────┐   1 clean Parquet per source ; silver_log.parquet
│  data/silver/ │
└───────┬───────┘
        │  src/transform/gold/  (surrogate keys, SCD2, Unknown Member rows, PII drop)
        ▼
┌───────────────┐   7 dims + 4 facts + 1 mart ; gold_log.parquet
│  data/gold/   │
└───────────────┘
        │
        ▼
   DuckDB / Power BI (ad-hoc SQL, dashboards — consumption layer, outside this repo)
```

Each layer is idempotent per `run_date`: rerunning a date overwrites that date's data files but appends to that layer's log file, so run history accumulates instead of being lost.

## Tech Stack

| Concern | Choice |
|---|---|
| Language | Python 3.14 |
| DataFrame engine | [Polars](https://pola.rs/) (Lazy API in Silver) |
| Storage format | Parquet, partitioned by `run_date` under `data/{bronze,silver,gold}/` |
| Source connector | Google Drive API (`google-api-python-client`) |
| Excel parsing | `fastexcel` |
| Package/env manager | [`uv`](https://docs.astral.sh/uv/) |
| Testing | `pytest` |
| Linting | `ruff` |
| CI | GitHub Actions (lint + full test suite on every push/PR) |

## Prerequisites

- Python 3.14 (see `.python-version`)
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/)
- A Google Service Account with read access to the source Drive folder

## Getting Started

1. Clone the repo:
   ```bash
   git clone git@github.com:Linh-divedeep-data/vietdist-analytics-platform.git
   cd vietdist-analytics-platform
   ```

2. Copy the environment template and fill in your Google Service Account key path:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set `GOOGLE_SERVICE_ACCOUNT_JSON` to the path of your `credentials.json` (default: `credentials.json` in the repo root) and `GDRIVE_FOLDER_ID` to the source Drive folder ID. Place the actual `credentials.json` (provided separately — never commit this file) at that path.

3. Install dependencies:
   ```bash
   uv sync
   ```

## Usage

`main.py` runs one layer at a time. `--layer` is required; `--run-date` (`YYYY-MM-DD`) defaults to today (UTC):

```bash
uv run main.py --layer bronze --run-date 2026-08-04
uv run main.py --layer silver --run-date 2026-08-04
uv run main.py --layer gold   --run-date 2026-08-04
```

Each layer reads the previous layer's output for the same `run_date`, so run them in that order on a first pass. A successful run looks like:

```
2026-08-04 12:00:00,000 [INFO] [batch_id=...] pipeline run started
2026-08-04 12:00:00,000 [INFO] [batch_id=...] OK: 10/10 nguồn thành công ở layer=silver
2026-08-04 12:00:00,000 [INFO] [batch_id=...] pipeline run finished
```
and exit code `0`; a non-zero exit code means at least one source failed for that layer (see `<layer>_log.parquet` under that layer's output directory for per-source detail).

> `--layer all` is accepted by the CLI (`choices=["bronze","silver","gold","all"]`) but not wired up yet — run the three layers separately for now.

## Testing

```bash
uv run pytest        # full suite
uvx ruff check .      # lint
```

CI runs both on every push and pull request (see `.github/workflows/ci.yml`).

## Project Structure

```
src/
├── extract/              # Bronze: raw CSV/Excel -> data/bronze/<date>/*.parquet
│   ├── unit_of_work/       # 1 module per source (SRC01..SRC10)
│   ├── registry.py         # UNIT_OF_WORK: source_file -> run()
│   └── orchestrator.py     # run_bronze_ingestion()
├── transform/
│   ├── silver/            # Bronze -> cleaned data/silver/<date>/*.parquet
│   │   ├── steps.py          # the 6 standard cleaning steps
│   │   ├── base.py           # transform_source_with_stats() engine
│   │   ├── registry.py       # per-source overrides beyond the 6 standard steps
│   │   ├── unit_of_work/     # only sources that need an override live here
│   │   ├── log.py            # silver_log.parquet record building/writing
│   │   └── orchestrator.py   # run_silver_transform()
│   └── gold/              # Silver -> Dim/Fact/Mart data/gold/<date>/*.parquet
│       ├── base.py           # shared helpers (surrogate keys, SCD2 as-of join, ...)
│       ├── dims/              # 1 file per dimension
│       ├── facts/             # 1 file per fact table
│       ├── marts/             # 1 file per data mart
│       ├── registry.py        # BUILD_ORDER (dims -> facts -> marts)
│       ├── log.py             # gold_log.parquet record building/writing
│       └── orchestrator.py    # run_gold_transform()
├── gdrive_connector.py
└── logger.py

config/            # source registry, required columns, path constants — no src/ imports
tests/             # 1 test file per src/ module, pytest
docs/              # BRD, per-phase design notes, star schema design
```

See [`docs/phase1_bronze_ingestion.md`](docs/phase1_bronze_ingestion.md), [`docs/phase2_silver_cleansing.md`](docs/phase2_silver_cleansing.md), and [`docs/phase3_gold_production.md`](docs/phase3_gold_production.md) for the design behind each layer, and [`docs/gold_star_schema_design.md`](docs/gold_star_schema_design.md) for the grain statements, bus matrix, and ERD behind the Gold star schema.

## Status

Bronze, Silver, and Gold layers are implemented and covered by the test suite. `--layer all` orchestration and the Power BI dashboard/reporting layer (Phase 4) are not yet built.
