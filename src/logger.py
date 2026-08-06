"""Shared logging module (VDAP-232).

Every pipeline module should log through get_logger(batch_id) instead of
configuring its own logging.Logger, so all output shares one format:
"%(asctime)s [%(levelname)s] [batch_id=...] %(message)s".
"""

import logging

_LOG_FORMAT = "%(asctime)s [%(levelname)s] [batch_id=%(batch_id)s] %(message)s"
_LOGGER_NAME = "vietdist"
_HANDLER_NAME = "vietdist-handler"


def get_logger(batch_id: str) -> logging.LoggerAdapter:
    """Return a logger adapter that stamps every log line with batch_id."""
    logger = logging.getLogger(_LOGGER_NAME)
    # Check by handler name, not `if not logger.handlers`: other tools
    # (e.g. pytest's own log-capturing) can attach their own handlers to
    # this logger; a bare emptiness check would then wrongly skip adding
    # ours, since it'd see *a* handler and assume it's already configured.
    if not any(h.name == _HANDLER_NAME for h in logger.handlers):
        handler = logging.StreamHandler()
        handler.name = _HANDLER_NAME
        handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logging.LoggerAdapter(logger, {"batch_id": batch_id})
