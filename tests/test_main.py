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
    monkeypatch.setattr(main_module.extract, "read_csv_sources", lambda raw_dir="data/raw": {})
    monkeypatch.setattr(main_module.extract, "read_excel_sources", lambda raw_dir="data/raw": {})
    monkeypatch.setattr(main_module.extract, "cast_to_string", lambda df: df)


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


def test_main_attaches_lineage_to_every_source_with_shared_batch_id(monkeypatch):
    import main as main_module
    from main import main

    monkeypatch.setattr(main_module.extract, "read_csv_sources", lambda raw_dir="data/raw": {
        "fake1.csv": "df-csv-1",
        "fake2.csv": "df-csv-2",
    })
    monkeypatch.setattr(main_module.extract, "read_excel_sources", lambda raw_dir="data/raw": {
        "fake1.xlsx": "df-xlsx-1",
        "fake2.xlsx": "df-xlsx-2",
    })

    attach_calls = []
    monkeypatch.setattr(
        main_module.extract,
        "attach_lineage",
        lambda df, source_file, run_date, batch_id: attach_calls.append((df, source_file, run_date, batch_id))
        or f"lineage-{source_file}",
    )
    monkeypatch.setattr(main_module.extract, "cast_to_string", lambda df: df)

    batch_id = main()

    assert len(attach_calls) == 4
    assert {call[1] for call in attach_calls} == {"fake1.csv", "fake2.csv", "fake1.xlsx", "fake2.xlsx"}
    assert all(call[3] == batch_id for call in attach_calls)


def test_main_casts_each_lineage_attached_dataframe_to_string(monkeypatch):
    import main as main_module
    from main import main

    monkeypatch.setattr(main_module.extract, "read_csv_sources", lambda raw_dir="data/raw": {
        "fake1.csv": "df-csv-1",
        "fake2.csv": "df-csv-2",
    })
    monkeypatch.setattr(main_module.extract, "read_excel_sources", lambda raw_dir="data/raw": {})
    monkeypatch.setattr(
        main_module.extract,
        "attach_lineage",
        lambda df, source_file, run_date, batch_id: f"lineage-{source_file}",
    )

    cast_calls = []
    monkeypatch.setattr(main_module.extract, "cast_to_string", lambda df: cast_calls.append(df) or df)

    main()

    assert set(cast_calls) == {"lineage-fake1.csv", "lineage-fake2.csv"}
