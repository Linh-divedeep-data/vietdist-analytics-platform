"""Pipeline entrypoint (Sprint 0 skeleton, VDAP-236).

Epic 1 will replace _run_placeholder_layer with the real
src.extract.orchestrator.run_bronze_ingestion() (and its silver/gold
equivalents) — batch_id is already threaded through get_logger() here
so that swap won't need to touch the logging plumbing.
"""

import sys
import uuid

from src.logger import get_logger


def _run_placeholder_layer(batch_id: str) -> None:
    logger = get_logger(batch_id)
    logger.info("placeholder layer running")


def main() -> int:
    batch_id = str(uuid.uuid4())
    logger = get_logger(batch_id)
    logger.info("pipeline run started")
    _run_placeholder_layer(batch_id)
    logger.info("pipeline run finished")
    return 0


if __name__ == "__main__":
    sys.exit(main())
