"""Tuning constants for gdrive_connector retry/backoff."""

GDRIVE_MAX_ATTEMPTS = 3
GDRIVE_BACKOFF_SECONDS = (1, 2, 4)
