"""Pipeline entrypoint (Sprint 0 skeleton, VDAP-236/VDAP-242).

Epic 1 will replace _run_placeholder_layer with the real
src.extract.orchestrator.run_bronze_ingestion() (and its silver/gold
equivalents) — batch_id and the records-in/exit-code-out contract are
already wired here so that swap won't need to touch this file's control
flow.

Hook point for real alerting (VDAP-242, out of scope for this ticket —
no webhook/SMTP available to test against in this capstone):
    exit_code = main()
    if exit_code != 0:
        send_alert(...)  # e.g. Slack/email webhook, not implemented here
"""

import sys
import uuid

from src.logger import get_logger


def _run_placeholder_layer(batch_id: str) -> list[dict]:
    logger = get_logger(batch_id)
    logger.info("placeholder layer running")
    return [{"source": "placeholder", "status": "success"}]


def _check_layer_results(records: list[dict], layer_name: str, batch_id: str) -> int:
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


def main() -> int:
    batch_id = str(uuid.uuid4())
    logger = get_logger(batch_id)
    logger.info("pipeline run started")
    records = _run_placeholder_layer(batch_id)
    exit_code = _check_layer_results(records, layer_name="bronze", batch_id=batch_id)
    logger.info("pipeline run finished")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
