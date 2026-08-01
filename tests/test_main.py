import os
import uuid

import pytest

pytestmark = pytest.mark.skipif(
    not os.path.exists("credentials.json"),
    reason="src.main imports src.extract, which imports src.gdrive_connector "
    "(eagerly authenticates on import, not present in CI)",
)

BRONZE_ARGV = ["--layer", "bronze", "--run-date", "2026-08-01"]


@pytest.fixture(autouse=True)
def mock_pipeline_calls(monkeypatch):
    import src.main as main_module

    monkeypatch.setattr(main_module.extract, "download_all_sources", lambda folder_id, batch_id: [])
    monkeypatch.setattr(main_module.extract, "run_bronze_ingestion", lambda run_date, batch_id: [])


def test_main_requires_layer_and_run_date():
    from src.main import main

    with pytest.raises(SystemExit):
        main([])


def test_main_rejects_invalid_layer_choice():
    from src.main import main

    with pytest.raises(SystemExit):
        main(["--layer", "unknown", "--run-date", "2026-08-01"])


def test_main_returns_valid_uuid_batch_id():
    from src.main import main

    batch_id = main(BRONZE_ARGV)
    assert uuid.UUID(batch_id)


def test_main_generates_new_batch_id_each_call():
    from src.main import main

    first = main(BRONZE_ARGV)
    second = main(BRONZE_ARGV)
    assert first != second


def test_main_logs_carry_the_same_batch_id(capsys):
    from src.main import main

    batch_id = main(BRONZE_ARGV)
    out = capsys.readouterr().out
    lines = [line for line in out.splitlines() if line.strip()]
    assert len(lines) >= 2
    for line in lines:
        assert f"[batch_id={batch_id}]" in line


def test_main_calls_download_all_sources_with_folder_id_and_batch_id_for_bronze_layer(monkeypatch):
    import src.main as main_module
    from src.main import main

    calls = []
    monkeypatch.setattr(
        main_module.extract,
        "download_all_sources",
        lambda folder_id, batch_id: calls.append((folder_id, batch_id)) or [],
    )

    batch_id = main(BRONZE_ARGV)

    assert calls == [(main_module.gdrive_connector.FOLDER_ID, batch_id)]


def test_main_calls_run_bronze_ingestion_with_run_date_and_batch_id(monkeypatch):
    import src.main as main_module
    from src.main import main

    calls = []
    monkeypatch.setattr(
        main_module.extract,
        "run_bronze_ingestion",
        lambda run_date, batch_id: calls.append((run_date, batch_id)) or [],
    )

    batch_id = main(BRONZE_ARGV)

    assert calls == [("2026-08-01", batch_id)]


def test_main_skips_bronze_calls_for_silver_layer(monkeypatch):
    import src.main as main_module
    from src.main import main

    download_calls = []
    ingestion_calls = []
    monkeypatch.setattr(
        main_module.extract, "download_all_sources", lambda folder_id, batch_id: download_calls.append(1) or []
    )
    monkeypatch.setattr(
        main_module.extract, "run_bronze_ingestion", lambda run_date, batch_id: ingestion_calls.append(1) or []
    )

    main(["--layer", "silver", "--run-date", "2026-08-01"])

    assert download_calls == []
    assert ingestion_calls == []


def test_main_runs_bronze_calls_for_all_layer(monkeypatch):
    import src.main as main_module
    from src.main import main

    download_calls = []
    monkeypatch.setattr(
        main_module.extract, "download_all_sources", lambda folder_id, batch_id: download_calls.append(1) or []
    )

    main(["--layer", "all", "--run-date", "2026-08-01"])

    assert download_calls == [1]
