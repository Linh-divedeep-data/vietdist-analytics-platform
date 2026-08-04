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


def test_bronze_layer_calls_run_bronze_ingestion_with_run_date_and_batch_id(monkeypatch):
    captured = {}

    def fake_run_bronze_ingestion(run_date, batch_id):
        captured["run_date"] = run_date
        captured["batch_id"] = batch_id
        return [{"source": "src01", "status": "success"}]

    monkeypatch.setattr("main.run_bronze_ingestion", fake_run_bronze_ingestion)

    exit_code = main(["--layer", "bronze"])

    assert exit_code == 0
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", captured["run_date"])
    assert captured["batch_id"]


def test_bronze_layer_returns_1_when_run_bronze_ingestion_reports_failure(monkeypatch):
    monkeypatch.setattr(
        "main.run_bronze_ingestion",
        lambda run_date, batch_id: [
            {"source": "src01", "status": "success"},
            {"source": "src02", "status": "failed"},
        ],
    )

    exit_code = main(["--layer", "bronze"])

    assert exit_code == 1


def test_all_log_lines_share_one_batch_id(monkeypatch, capsys):
    monkeypatch.setattr(
        "main.run_bronze_ingestion",
        lambda run_date, batch_id: [{"source": "src01", "status": "success"}],
    )

    exit_code = main(["--layer", "bronze"])

    lines = capsys.readouterr().err.strip().splitlines()
    assert len(lines) >= 2

    batch_ids = set()
    for line in lines:
        match = LOG_LINE_RE.match(line)
        assert match is not None, f"log line did not match expected format: {line!r}"
        batch_ids.add(match.group("batch_id"))

    assert len(batch_ids) == 1
    assert exit_code == 0


def test_different_runs_get_different_batch_ids(monkeypatch):
    seen_batch_ids = []

    def fake_run_bronze_ingestion(run_date, batch_id):
        seen_batch_ids.append(batch_id)
        return [{"source": "src01", "status": "success"}]

    monkeypatch.setattr("main.run_bronze_ingestion", fake_run_bronze_ingestion)

    main(["--layer", "bronze"])
    main(["--layer", "bronze"])

    assert len(seen_batch_ids) == 2
    assert seen_batch_ids[0] != seen_batch_ids[1]


def test_missing_layer_argument_errors(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main([])

    assert exc_info.value.code == 2
    assert "--layer" in capsys.readouterr().err


def test_invalid_layer_choice_errors(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--layer", "silver"])

    assert exc_info.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


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
