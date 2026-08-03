import logging
import re

import pytest

from main import _check_layer_results, main

LOG_LINE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} "
    r"\[(?P<level>[A-Z]+)\] \[batch_id=(?P<batch_id>[^\]]+)\] (?P<message>.+)$"
)


@pytest.fixture(autouse=True)
def _reset_shared_logger():
    logger = logging.getLogger("vietdist")
    logger.handlers.clear()
    yield
    logger.handlers.clear()


def test_all_log_lines_share_one_batch_id(capsys):
    exit_code = main()

    lines = capsys.readouterr().err.strip().splitlines()
    assert len(lines) >= 2

    batch_ids = set()
    for line in lines:
        match = LOG_LINE_RE.match(line)
        assert match is not None, f"log line did not match expected format: {line!r}"
        batch_ids.add(match.group("batch_id"))

    assert len(batch_ids) == 1
    assert exit_code == 0


def test_different_runs_get_different_batch_ids(capsys):
    main()
    first_run_lines = capsys.readouterr().err.strip().splitlines()
    first_batch_id = LOG_LINE_RE.match(first_run_lines[0]).group("batch_id")

    main()
    second_run_lines = capsys.readouterr().err.strip().splitlines()
    second_batch_id = LOG_LINE_RE.match(second_run_lines[0]).group("batch_id")

    assert first_batch_id != second_batch_id


def test_check_layer_results_returns_1_and_logs_error_on_any_failure(capsys):
    records = [
        {"source": "src01", "status": "success"},
        {"source": "src02", "status": "failed"},
    ]

    exit_code = _check_layer_results(records, layer_name="bronze", batch_id="batch-x")

    assert exit_code == 1
    output = capsys.readouterr().err
    assert "FAILED: 1/2" in output
    assert "layer=bronze" in output
    assert "[ERROR]" in output
    assert "ingest_log.parquet" in output


def test_check_layer_results_returns_0_and_logs_ok_when_all_succeed(capsys):
    records = [
        {"source": "src01", "status": "success"},
        {"source": "src02", "status": "success"},
    ]

    exit_code = _check_layer_results(records, layer_name="bronze", batch_id="batch-x")

    assert exit_code == 0
    output = capsys.readouterr().err
    assert "OK" in output
    assert "layer=bronze" in output
