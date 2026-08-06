# VietDist Analytics Platform

## Getting Started

1. Clone the repo:
   ```bash
   git clone <repo-url>
   cd vietdist-analytics-platform
   ```

2. Copy the environment template and fill in your Google Service Account key path:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set `GOOGLE_SERVICE_ACCOUNT_JSON` to the path of your `credentials.json` (default: `credentials.json` in the repo root). Place the actual `credentials.json` file (provided separately — never commit this file) at that path.

3. Install dependencies:
   ```bash
   uv sync
   ```

4. Run the pipeline — `--layer` is required, `--run-date` defaults to today (UTC):
   ```bash
   uv run main.py --layer bronze --run-date 2026-08-04
   uv run main.py --layer silver --run-date 2026-08-04
   uv run main.py --layer gold --run-date 2026-08-04
   ```
   Each layer reads its input from the previous layer's output directory (`data/bronze/<date>/`, `data/silver/<date>/`) and writes its own (`data/bronze|silver|gold/<date>/`), so run them in order for a first pass. You should see log lines like:
   ```
   2026-08-03 12:00:00,000 [INFO] [batch_id=...] pipeline run started
   2026-08-03 12:00:00,000 [INFO] [batch_id=...] OK: 10/10 nguồn thành công ở layer=silver
   2026-08-03 12:00:00,000 [INFO] [batch_id=...] pipeline run finished
   ```
   and exit code `0`.

   > `--layer all` (Bronze→Silver→Gold in one command) is accepted by the CLI's `choices` but not wired up yet — run the three layers separately for now.

## Project Structure

```
src/
├── extract/            # Bronze: raw CSV/Excel -> data/bronze/<date>/*.parquet
│   ├── unit_of_work/    # 1 module per source (SRC01..SRC10)
│   ├── registry.py      # UNIT_OF_WORK: source_file -> run()
│   └── orchestrator.py  # run_bronze_ingestion()
├── transform/
│   ├── silver/          # Bronze -> cleaned data/silver/<date>/*.parquet
│   │   ├── steps.py      # the 6 standard cleaning steps
│   │   ├── base.py       # transform_source_with_stats() engine
│   │   ├── registry.py   # per-source overrides beyond the 6 standard steps
│   │   ├── unit_of_work/ # only sources that need an override live here
│   │   ├── log.py        # silver_log.parquet record building/writing
│   │   └── orchestrator.py  # run_silver_transform()
│   └── gold/            # Silver -> Dim/Fact/Mart data/gold/<date>/*.parquet
│       ├── base.py       # shared helpers (surrogate keys, SCD2 as-of join, ...)
│       ├── dims/          # 1 file per dimension
│       ├── facts/         # 1 file per fact table
│       ├── marts/         # 1 file per data mart
│       ├── registry.py    # BUILD_ORDER (dims -> facts -> marts)
│       ├── log.py         # gold_log.parquet record building/writing
│       └── orchestrator.py  # run_gold_transform()
├── gdrive_connector.py
└── logger.py
```

See `docs/phase1_bronze_ingestion.md`, `docs/phase2_silver_cleansing.md`, and `docs/phase3_gold_production.md` for the design behind each layer.
