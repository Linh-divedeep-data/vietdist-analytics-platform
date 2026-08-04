"""build_ingest_log_record() + write_ingest_log() — filled in Epic Phase 1 (VDAP-116-118)."""

import os


def build_ingest_log_record(
    batch_id: str,
    source_file: str,
    rows_loaded: int,
    status: str,
    duration_sec: float,
    source_platform: str = "google_drive",
) -> dict:
    return {
        "batch_id": batch_id,
        "source_name": os.path.splitext(source_file)[0],
        "source_file": source_file,
        "source_platform": source_platform,
        "rows_loaded": rows_loaded,
        "status": status,
        "duration_sec": duration_sec,
    }
