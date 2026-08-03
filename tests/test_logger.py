import logging
import re

import pytest

from src.logger import get_logger


@pytest.fixture(autouse=True)
def _reset_shared_logger():
    """Each test needs its own capsys-captured stream, but get_logger()
    only attaches a handler once (on first call). Clearing handlers
    before/after every test forces a fresh handler bound to *this*
    test's capsys-patched sys.stderr, instead of reusing a handler
    whose .stream still points at a previous test's capsys object."""
    logger = logging.getLogger("vietdist")
    logger.handlers.clear()
    yield
    logger.handlers.clear()


LOG_LINE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} "
    r"\[(?P<level>[A-Z]+)\] \[batch_id=(?P<batch_id>[^\]]+)\] (?P<message>.+)$"
)


def test_info_log_matches_expected_format(capsys):
    get_logger("test-batch").info("hello")

    output = capsys.readouterr().err.strip()
    match = LOG_LINE_RE.match(output)

    assert match is not None, f"log line did not match expected format: {output!r}"
    assert match.group("level") == "INFO"
    assert match.group("batch_id") == "test-batch"
    assert match.group("message") == "hello"


def test_error_log_uses_error_level(capsys):
    get_logger("batch-2").error("something broke")

    output = capsys.readouterr().err.strip()
    match = LOG_LINE_RE.match(output)

    assert match is not None, f"log line did not match expected format: {output!r}"
    assert match.group("level") == "ERROR"
    assert match.group("batch_id") == "batch-2"
    assert match.group("message") == "something broke"


def test_different_batch_ids_are_independent(capsys):
    get_logger("batch-a").info("from a")
    get_logger("batch-b").info("from b")

    lines = capsys.readouterr().err.strip().splitlines()
    assert len(lines) == 2

    first = LOG_LINE_RE.match(lines[0])
    second = LOG_LINE_RE.match(lines[1])
    assert first.group("batch_id") == "batch-a"
    assert second.group("batch_id") == "batch-b"


def test_get_logger_returns_logger_adapter():
    adapter = get_logger("test-batch")
    assert isinstance(adapter, logging.LoggerAdapter)
