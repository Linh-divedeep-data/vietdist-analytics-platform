"""Pipeline entrypoint (Sprint 0 skeleton, VDAP-236/VDAP-242; Bronze wired in VDAP-325).

Hook point for real alerting (VDAP-242, out of scope for this ticket —
no webhook/SMTP available to test against in this capstone):
    exit_code = main()
    if exit_code != 0:
        send_alert(...)  # e.g. Slack/email webhook, not implemented here
"""

import argparse
import sys
import uuid
from datetime import UTC, datetime

from src.extract.orchestrator import run_bronze_ingestion
from src.logger import get_logger
from src.transform.gold.orchestrator import run_gold_transform
from src.transform.silver.orchestrator import run_silver_transform


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse CLI args: required --layer, optional --run-date (defaults to today)."""
    parser = argparse.ArgumentParser(
        description="Vietdist pipeline entrypoint — run one layer (or all) for a given run_date."
    )
    parser.add_argument(
        "--layer",
        choices=["bronze", "silver", "gold", "all"],
        required=True,
        help="Which pipeline layer to run: bronze, silver, gold, or all (runs Bronze->Silver->Gold in sequence).",
    )
    parser.add_argument(
        "--run-date",
        required=False,
        default=None,
        help="Run date in YYYY-MM-DD format. Defaults to today (UTC) if omitted.",
    )
    return parser.parse_args(argv)


def _check_layer_results(records: list[dict], layer_name: str, batch_id: str) -> int:
    """Log a summary for one layer's run and return the process exit code."""
    logger = get_logger(batch_id)
    total = len(records)
    failed = [r for r in records if r.get("status") != "success"]

    if failed:
        logger.error(
            "FAILED: %d/%d nguồn lỗi ở layer=%s, xem ingest_log.parquet",
            len(failed),
            total,
            layer_name,
        )
        return 1

    logger.info("OK: %d/%d nguồn thành công ở layer=%s", total, total, layer_name)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse CLI args, run the pipeline once with a fresh batch_id, and return the process exit code."""
    args = _parse_args(argv)
    batch_id = str(uuid.uuid4())
    run_date = args.run_date or datetime.now(UTC).date().isoformat()
    logger = get_logger(batch_id)
    logger.info("pipeline run started")
    if args.layer == "bronze":
        records = run_bronze_ingestion(run_date, batch_id)
    elif args.layer == "silver":
        records = run_silver_transform(run_date, batch_id=batch_id)
    elif args.layer == "gold":
        records = run_gold_transform(run_date, batch_id=batch_id)
    exit_code = _check_layer_results(records, layer_name=args.layer, batch_id=batch_id)
    logger.info("pipeline run finished")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
