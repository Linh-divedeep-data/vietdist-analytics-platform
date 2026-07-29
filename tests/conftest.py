import logging

import pytest


@pytest.fixture(autouse=True)
def reset_shared_logger():
    logger = logging.getLogger("vdap_pipeline")
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)
    logger.propagate = True
    yield
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)
    logger.propagate = True
