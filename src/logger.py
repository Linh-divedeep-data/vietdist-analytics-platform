import logging
import sys


class BatchLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return f"[batch_id={self.extra['batch_id']}] {msg}", kwargs


def get_logger(batch_id: str, level: int | None = None):
    # "vdap_pipeline" is one process-wide shared logger — level is global.
    # Only an explicit `level` overrides it, so a later call left at the
    # default doesn't silently clobber a level an earlier caller requested.
    base_logger = logging.getLogger("vdap_pipeline")
    if not base_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        base_logger.addHandler(handler)
        base_logger.propagate = False
        base_logger.setLevel(logging.INFO)
    if level is not None:
        base_logger.setLevel(level)
    return BatchLoggerAdapter(base_logger, {"batch_id": batch_id})


