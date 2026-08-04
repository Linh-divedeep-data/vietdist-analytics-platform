"""run_bronze_ingestion(): main loop over registry.UNIT_OF_WORK + Parquet write — filled in Epic Phase 1."""

import os

from config.settings import BRONZE_DIR


def get_bronze_output_dir(run_date: str, bronze_dir: str = BRONZE_DIR) -> str:
    out_dir = os.path.join(bronze_dir, run_date.replace("-", ""))
    os.makedirs(out_dir, exist_ok=True)
    return out_dir
