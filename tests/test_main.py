import os
import uuid

import pytest

pytestmark = pytest.mark.skipif(
    not os.path.exists("credentials.json"),
    reason="main.py imports src.extract, which imports src.gdrive_connector "
    "(eagerly authenticates on import, not present in CI)",
)


@pytest.fixture(autouse=True)
def mock_download_all_sources(monkeypatch):
    import main as main_module

    monkeypatch.setattr(main_module.extract, "download_all_sources", lambda folder_id, batch_id: [])


def test_main_returns_valid_uuid_batch_id():
    from main import main

    batch_id = main()
    assert uuid.UUID(batch_id)


def test_main_generates_new_batch_id_each_call():
    from main import main

    first = main()
    second = main()
    assert first != second


def test_main_logs_carry_the_same_batch_id(capsys):
    from main import main

    batch_id = main()
    out = capsys.readouterr().out
    lines = [line for line in out.splitlines() if line.strip()]
    assert len(lines) >= 2
    for line in lines:
        assert f"[batch_id={batch_id}]" in line


def test_main_calls_download_all_sources_with_folder_id_and_batch_id(monkeypatch):
    import main as main_module
    from main import main

    calls = []
    monkeypatch.setattr(
        main_module.extract,
        "download_all_sources",
        lambda folder_id, batch_id: calls.append((folder_id, batch_id)) or [],
    )

    batch_id = main()

    assert calls == [(main_module.gdrive_connector.FOLDER_ID, batch_id)]
