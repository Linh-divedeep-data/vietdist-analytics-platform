import logging
import re

from src.logger import get_logger


def test_default_level_is_info():
    logger = get_logger("batch-1")
    assert logger.logger.getEffectiveLevel() == logging.INFO


def test_level_is_configurable():
    logger = get_logger("batch-2", level=logging.DEBUG)
    assert logger.logger.getEffectiveLevel() == logging.DEBUG


def test_no_duplicate_handlers_on_repeated_calls():
    get_logger("batch-a")
    get_logger("batch-b")
    assert len(logging.getLogger("vdap_pipeline").handlers) == 1


def test_does_not_propagate_to_root():
    logger = get_logger("batch-1")
    assert logger.logger.propagate is False


def test_explicit_level_not_reset_by_later_call_without_level():
    debug_logger = get_logger("bronze-batch", level=logging.DEBUG)
    get_logger("silver-batch")  # sequential call later, no explicit level
    assert debug_logger.logger.getEffectiveLevel() == logging.DEBUG


def test_output_includes_timestamp_level_batch_id_message(capsys):
    logger = get_logger("test-batch")
    logger.info("hello")
    out = capsys.readouterr().out
    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", out)
    assert "[INFO]" in out
    assert "[batch_id=test-batch]" in out
    assert "hello" in out
