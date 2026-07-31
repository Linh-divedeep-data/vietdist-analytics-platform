import os

import polars as pl
import pytest

pytestmark = pytest.mark.skipif(
    not os.path.exists("credentials.json"),
    reason="src.extract imports src.gdrive_connector, which eagerly authenticates on import (not present in CI)",
)


def test_download_all_sources_calls_download_file_for_every_listed_file(monkeypatch):
    from src import extract

    fake_files = [
        {"id": "id-1", "name": "SRC01_sales_transactions.csv", "mimeType": "text/csv"},
        {"id": "id-2", "name": "SRC02_sales_target_plan.xlsx", "mimeType": "spreadsheetml"},
        {"id": "id-3", "name": "SRC03_customer_master.csv", "mimeType": "text/csv"},
    ]
    download_calls = []

    monkeypatch.setattr(extract.gdrive_connector, "list_files_in_folder", lambda folder_id: fake_files)
    monkeypatch.setattr(
        extract.gdrive_connector,
        "download_file",
        lambda file_id, file_name: download_calls.append((file_id, file_name)) or f"data/raw/{file_name}",
    )

    extract.download_all_sources("fake-folder-id", batch_id="test-batch")

    assert download_calls == [
        ("id-1", "SRC01_sales_transactions.csv"),
        ("id-2", "SRC02_sales_target_plan.xlsx"),
        ("id-3", "SRC03_customer_master.csv"),
    ]


def test_download_all_sources_returns_status_record_on_success(monkeypatch):
    from src import extract

    fake_files = [{"id": "id-1", "name": "SRC01_sales_transactions.csv"}]

    monkeypatch.setattr(extract.gdrive_connector, "list_files_in_folder", lambda folder_id: fake_files)
    monkeypatch.setattr(
        extract.gdrive_connector,
        "download_file",
        lambda file_id, file_name: f"data/raw/{file_name}",
    )

    result = extract.download_all_sources("fake-folder-id", batch_id="test-batch")

    assert result == [
        {
            "source_file": "SRC01_sales_transactions.csv",
            "status": "success",
            "path": "data/raw/SRC01_sales_transactions.csv",
            "error": None,
        }
    ]


def test_download_all_sources_continues_after_one_file_fails(monkeypatch):
    from src import extract

    fake_files = [
        {"id": "id-1", "name": "SRC01_sales_transactions.csv"},
        {"id": "id-2", "name": "SRC02_sales_target_plan.xlsx"},
        {"id": "id-3", "name": "SRC03_customer_master.csv"},
    ]

    def fake_download_file(file_id, file_name):
        if file_id == "id-2":
            raise ConnectionError("simulated download failure")
        return f"data/raw/{file_name}"

    monkeypatch.setattr(extract.gdrive_connector, "list_files_in_folder", lambda folder_id: fake_files)
    monkeypatch.setattr(extract.gdrive_connector, "download_file", fake_download_file)

    result = extract.download_all_sources("fake-folder-id", batch_id="test-batch")

    assert [r["source_file"] for r in result] == [
        "SRC01_sales_transactions.csv",
        "SRC02_sales_target_plan.xlsx",
        "SRC03_customer_master.csv",
    ]
    assert [r["status"] for r in result] == ["success", "failed", "success"]


def test_download_all_sources_records_error_message_for_failed_file(monkeypatch):
    from src import extract

    fake_files = [{"id": "bad-id", "name": "SRC02_sales_target_plan.xlsx"}]

    def fake_download_file(file_id, file_name):
        raise ConnectionError("simulated download failure")

    monkeypatch.setattr(extract.gdrive_connector, "list_files_in_folder", lambda folder_id: fake_files)
    monkeypatch.setattr(extract.gdrive_connector, "download_file", fake_download_file)

    result = extract.download_all_sources("fake-folder-id", batch_id="test-batch")

    assert result == [
        {
            "source_file": "SRC02_sales_target_plan.xlsx",
            "status": "failed",
            "path": None,
            "error": "simulated download failure",
        }
    ]


def test_download_all_sources_logs_error_via_get_logger_on_failure(monkeypatch, capsys):
    from src import extract

    fake_files = [{"id": "bad-id", "name": "SRC02_sales_target_plan.xlsx"}]

    def fake_download_file(file_id, file_name):
        raise ConnectionError("simulated download failure")

    monkeypatch.setattr(extract.gdrive_connector, "list_files_in_folder", lambda folder_id: fake_files)
    monkeypatch.setattr(extract.gdrive_connector, "download_file", fake_download_file)

    extract.download_all_sources("fake-folder-id", batch_id="test-batch-123")

    out = capsys.readouterr().out
    assert "[batch_id=test-batch-123]" in out
    assert "SRC02_sales_target_plan.xlsx" in out
    assert "simulated download failure" in out


def test_read_csv_sources_returns_dataframe_per_csv_source_with_matching_row_count(tmp_path):
    from src import extract

    (tmp_path / "SRC01_sales_transactions.csv").write_text("order_id,amount\n1,100\n2,200\n")
    (tmp_path / "SRC03_customer_master.csv").write_text("customer_id,name\n1,A\n")
    (tmp_path / "SRC06_distributor_master.csv").write_text("distributor_id,name\n1,B\n2,C\n3,D\n")
    (tmp_path / "SRC09_return_transactions.csv").write_text("return_id,amount\n1,10\n")

    dataframes = extract.read_csv_sources(raw_dir=str(tmp_path))

    assert set(dataframes.keys()) == {
        "SRC01_sales_transactions.csv",
        "SRC03_customer_master.csv",
        "SRC06_distributor_master.csv",
        "SRC09_return_transactions.csv",
    }
    assert dataframes["SRC01_sales_transactions.csv"].height == 2
    assert dataframes["SRC03_customer_master.csv"].height == 1
    assert dataframes["SRC06_distributor_master.csv"].height == 3
    assert dataframes["SRC09_return_transactions.csv"].height == 1


def test_read_csv_sources_reads_all_columns_as_string(tmp_path):
    from src import extract

    (tmp_path / "SRC01_sales_transactions.csv").write_text("order_id,amount\n1,100\n2,200\n")
    (tmp_path / "SRC03_customer_master.csv").write_text("customer_id,name\n1,A\n")
    (tmp_path / "SRC06_distributor_master.csv").write_text("distributor_id,name\n1,B\n2,C\n3,D\n")
    (tmp_path / "SRC09_return_transactions.csv").write_text("return_id,amount\n1,10\n")

    dataframes = extract.read_csv_sources(raw_dir=str(tmp_path))

    for df in dataframes.values():
        assert all(dtype == pl.String for dtype in df.dtypes)


def test_read_csv_sources_raises_on_missing_file(tmp_path):
    from src import extract

    with pytest.raises(FileNotFoundError):
        extract.read_csv_sources(raw_dir=str(tmp_path))


def test_read_excel_sources_returns_dataframe_per_excel_source_with_matching_row_count(tmp_path):
    from src import extract

    pl.DataFrame({"target_id": ["1", "2"], "amount": ["100", "200"]}).write_excel(
        tmp_path / "SRC02_sales_target_plan.xlsx"
    )
    pl.DataFrame({"product_id": ["1"], "name": ["A"]}).write_excel(tmp_path / "SRC04_product_master.xlsx")
    pl.DataFrame({"order_id": ["1", "2", "3"]}).write_excel(tmp_path / "SRC05_distributor_orders.xlsx")
    pl.DataFrame({"employee_id": ["1"]}).write_excel(tmp_path / "SRC07_employee_master.xlsx")
    pl.DataFrame({"territory_id": ["1", "2"]}).write_excel(tmp_path / "SRC08_territory_mapping.xlsx")
    pl.DataFrame({"promo_id": ["1"]}).write_excel(tmp_path / "SRC10_promotion_program.xlsx")

    dataframes = extract.read_excel_sources(raw_dir=str(tmp_path))

    assert set(dataframes.keys()) == {
        "SRC02_sales_target_plan.xlsx",
        "SRC04_product_master.xlsx",
        "SRC05_distributor_orders.xlsx",
        "SRC07_employee_master.xlsx",
        "SRC08_territory_mapping.xlsx",
        "SRC10_promotion_program.xlsx",
    }
    assert dataframes["SRC02_sales_target_plan.xlsx"].height == 2
    assert dataframes["SRC04_product_master.xlsx"].height == 1
    assert dataframes["SRC05_distributor_orders.xlsx"].height == 3
    assert dataframes["SRC07_employee_master.xlsx"].height == 1
    assert dataframes["SRC08_territory_mapping.xlsx"].height == 2
    assert dataframes["SRC10_promotion_program.xlsx"].height == 1


def test_read_excel_sources_reads_all_columns_as_string(tmp_path):
    from src import extract

    pl.DataFrame({"target_id": [1, 2], "amount": [100.5, 200.5]}).write_excel(
        tmp_path / "SRC02_sales_target_plan.xlsx"
    )
    pl.DataFrame({"product_id": [1], "name": ["A"]}).write_excel(tmp_path / "SRC04_product_master.xlsx")
    pl.DataFrame({"order_id": [1, 2, 3]}).write_excel(tmp_path / "SRC05_distributor_orders.xlsx")
    pl.DataFrame({"employee_id": [1]}).write_excel(tmp_path / "SRC07_employee_master.xlsx")
    pl.DataFrame({"territory_id": [1, 2]}).write_excel(tmp_path / "SRC08_territory_mapping.xlsx")
    pl.DataFrame({"promo_id": [1]}).write_excel(tmp_path / "SRC10_promotion_program.xlsx")

    dataframes = extract.read_excel_sources(raw_dir=str(tmp_path))

    for df in dataframes.values():
        assert all(dtype == pl.String for dtype in df.dtypes)


def test_read_excel_sources_raises_on_missing_file(tmp_path):
    from src import extract

    with pytest.raises(FileNotFoundError):
        extract.read_excel_sources(raw_dir=str(tmp_path))


def test_read_excel_sources_raises_clear_error_when_engine_missing(tmp_path, monkeypatch):
    from src import extract

    def fake_read_excel(*args, **kwargs):
        raise ImportError("fastexcel not found")

    monkeypatch.setattr(extract.pl, "read_excel", fake_read_excel)

    with pytest.raises(ImportError, match="uv add fastexcel"):
        extract.read_excel_sources(raw_dir=str(tmp_path))


def test_attach_lineage_adds_all_5_metadata_columns_with_correct_values():
    from src import extract

    df = pl.DataFrame({"order_id": ["1", "2"], "amount": ["100", "200"]})

    result = extract.attach_lineage(
        df, source_file="SRC01_sales_transactions.csv", run_date="2026-07-31", batch_id="abc-123"
    )

    assert result["_source_file"].to_list() == ["SRC01_sales_transactions.csv", "SRC01_sales_transactions.csv"]
    assert result["_source_platform"].to_list() == ["google_drive", "google_drive"]
    assert result["_run_date"].to_list() == ["2026-07-31", "2026-07-31"]
    assert result["_batch_id"].to_list() == ["abc-123", "abc-123"]
    assert result["_ingested_at"].null_count() == 0


def test_attach_lineage_preserves_original_columns_and_rows():
    from src import extract

    df = pl.DataFrame({"order_id": ["1", "2"], "amount": ["100", "200"]})

    result = extract.attach_lineage(
        df, source_file="SRC01_sales_transactions.csv", run_date="2026-07-31", batch_id="abc-123"
    )

    assert result["order_id"].to_list() == ["1", "2"]
    assert result["amount"].to_list() == ["100", "200"]


def test_attach_lineage_stamps_ingested_at_per_call():
    from src import extract

    df = pl.DataFrame({"order_id": ["1"]})

    first = extract.attach_lineage(df, source_file="a.csv", run_date="2026-07-31", batch_id="batch-1")
    second = extract.attach_lineage(df, source_file="a.csv", run_date="2026-07-31", batch_id="batch-1")

    assert first["_ingested_at"].to_list()[0] is not None
    assert second["_ingested_at"].to_list()[0] is not None


def test_cast_to_string_converts_non_string_lineage_column():
    from src import extract

    df = pl.DataFrame({"order_id": ["1", "2"]})
    lineage_df = extract.attach_lineage(df, source_file="a.csv", run_date="2026-07-31", batch_id="batch-1")
    assert lineage_df["_ingested_at"].dtype != pl.String

    result = extract.cast_to_string(lineage_df)

    assert all(dtype == pl.String for dtype in result.dtypes)


def test_cast_to_string_leaves_already_string_dataframe_unchanged():
    from src import extract

    df = pl.DataFrame({"order_id": ["1", "2"], "amount": ["100", "200"]})

    result = extract.cast_to_string(df)

    assert all(dtype == pl.String for dtype in result.dtypes)
    assert result["order_id"].to_list() == ["1", "2"]
    assert result["amount"].to_list() == ["100", "200"]


def test_download_all_sources_does_not_log_on_success(monkeypatch, capsys):
    from src import extract

    fake_files = [{"id": "id-1", "name": "SRC01_sales_transactions.csv"}]

    monkeypatch.setattr(extract.gdrive_connector, "list_files_in_folder", lambda folder_id: fake_files)
    monkeypatch.setattr(
        extract.gdrive_connector,
        "download_file",
        lambda file_id, file_name: f"data/raw/{file_name}",
    )

    extract.download_all_sources("fake-folder-id", batch_id="test-batch")

    out = capsys.readouterr().out
    assert out == ""
