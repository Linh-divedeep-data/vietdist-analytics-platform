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

4. Run the pipeline:
   ```bash
   uv run main.py
   ```
   You should see log lines like:
   ```
   2026-08-03 12:00:00,000 [INFO] [batch_id=...] pipeline run started
   2026-08-03 12:00:00,000 [INFO] [batch_id=...] placeholder layer running
   2026-08-03 12:00:00,000 [INFO] [batch_id=...] OK: 1/1 nguồn thành công ở layer=bronze
   2026-08-03 12:00:00,000 [INFO] [batch_id=...] pipeline run finished
   ```
   and exit code `0`.

   > `--layer`/`--run-date` CLI flags (e.g. `uv run main.py --layer all --run-date 2026-08-03`) are planned for Phase 3 (P3.8) and not available yet — today's `main.py` runs a fixed placeholder bronze layer.
