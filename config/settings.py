"""Path constants (RAW_DIR, BRONZE_DIR, SILVER_DIR, GOLD_DIR) — filled in Epic Phase 1. No credentials here (see risk register in VDAP-168)."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = str(ROOT_DIR / "data" / "raw")
BRONZE_DIR = str(ROOT_DIR / "data" / "bronze")
SILVER_DIR = str(ROOT_DIR / "data" / "silver")
GOLD_DIR = str(ROOT_DIR / "data" / "gold")
