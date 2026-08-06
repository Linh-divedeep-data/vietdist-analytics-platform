from datetime import date

import polars as pl

from src.transform_gold import (
    add_is_current_flag,
    add_scd2_valid_dates,
    add_surrogate_key,
    add_unknown_member,
    build_dim_customers,
    build_dim_date,
    build_dim_distributors,
    build_dim_employees,
    build_dim_products,
    build_dim_promotion,
    build_dim_territory,
    build_fact_sales,
    build_fact_targets,
    dedupe_by_business_key,
    drop_lineage_columns,
    drop_pii_columns,
    join_employee_asof,
)


def test_drop_lineage_columns_removes_all_5_lineage_columns():
    df = pl.DataFrame(
        {
            "customer_id": ["CUS0001"],
            "_source_file": ["SRC03_customer_master.csv"],
            "_source_platform": ["gdrive"],
            "_run_date": ["2026-08-04"],
            "_ingested_at": ["2026-08-04T00:00:00"],
            "_batch_id": ["batch-1"],
        }
    )

    result = drop_lineage_columns(df)

    assert result.columns == ["customer_id"]


def test_drop_lineage_columns_is_noop_when_no_lineage_columns_present():
    df = pl.DataFrame({"customer_id": ["CUS0001"]})

    result = drop_lineage_columns(df)

    assert result.columns == ["customer_id"]


def test_add_surrogate_key_starts_at_1_not_0():
    df = pl.DataFrame({"product_id": ["PRD0001", "PRD0002", "PRD0003"]})

    result = add_surrogate_key(df, "product_key")

    assert result["product_key"].to_list() == [1, 2, 3]
    assert result.columns[0] == "product_key"


def test_dedupe_by_business_key_keeps_first_row_and_logs_dropped_count(caplog):
    import logging

    df = pl.DataFrame(
        {
            "product_id": ["PRD0001", "PRD0001", "PRD0002"],
            "product_name": ["gốc", "trùng", "khác"],
        }
    )

    with caplog.at_level(logging.WARNING):
        result = dedupe_by_business_key(df, "product_id")

    assert result.height == 2
    assert "product_id" in caplog.text
    assert "1" in caplog.text


def test_dedupe_by_business_key_does_not_log_when_no_duplicates(caplog):
    import logging

    df = pl.DataFrame({"product_id": ["PRD0001", "PRD0002"]})

    with caplog.at_level(logging.WARNING):
        result = dedupe_by_business_key(df, "product_id")

    assert result.height == 2
    assert caplog.text == ""


def test_add_unknown_member_prepends_row_with_key_minus_1_and_infers_unknown_string_default():
    df = pl.DataFrame(
        {
            "customer_id": ["CUS0001", "CUS0002"],
            "customer_name": ["An", "Binh"],
        }
    ).with_row_index(name="customer_key", offset=1)

    result = add_unknown_member(df, "customer_key", "customer_id")

    assert result["customer_key"].to_list() == [-1, 1, 2]
    assert result.schema["customer_key"] == pl.Int64
    unknown_row = result.filter(pl.col("customer_key") == -1).row(0, named=True)
    assert unknown_row["customer_id"] == "UNKNOWN"
    assert unknown_row["customer_name"] == "Unknown"


def test_add_unknown_member_applies_overrides_instead_of_dtype_default():
    df = pl.DataFrame(
        {
            "employee_id": ["EMP001"],
            "valid_from": [date(2024, 1, 1)],
            "valid_to": [None],
            "is_current": [True],
        }
    ).with_row_index(name="employee_key", offset=1)

    result = add_unknown_member(df, "employee_key", "employee_id", overrides={"is_current": False})

    unknown_row = result.filter(pl.col("employee_key") == -1).row(0, named=True)
    assert unknown_row["employee_id"] == "UNKNOWN"
    assert unknown_row["valid_from"] is None
    assert unknown_row["valid_to"] is None
    # is_current must be the override (False), NOT the dtype default (None/null) —
    # a null here would break any downstream filter(pl.col("is_current")) that expects a bool.
    assert unknown_row["is_current"] is False


def test_drop_pii_columns_removes_configured_columns_for_dim():
    df = pl.DataFrame(
        {
            "customer_id": ["CUS0001"],
            "address": ["123 Lê Lợi"],
            "phone": ["0900000000"],
            "tax_code": ["MST0001"],
        }
    )

    result = drop_pii_columns(df, "dim_customers")

    assert result.columns == ["customer_id"]


def test_drop_pii_columns_is_noop_when_pii_column_absent():
    df = pl.DataFrame({"distributor_id": ["DIST0001"], "phone": ["0900000000"]})

    result = drop_pii_columns(df, "dim_distributors")

    # dim_distributors is configured to drop phone AND tax_code, but this df never had
    # tax_code — strict=False must not raise for the missing one.
    assert result.columns == ["distributor_id"]


def test_build_dim_customers_generates_1_based_surrogate_key():
    df = pl.DataFrame(
        {
            "customer_id": ["CUS0001", "CUS0002"],
            "customer_name": ["An", "Binh"],
        }
    )

    result = build_dim_customers(df)

    assert result["customer_key"].to_list() == [-1, 1, 2]


def test_build_dim_customers_dedupes_by_customer_id_keeping_first_row():
    df = pl.DataFrame(
        {
            "customer_id": ["CUS0001", "CUS0001", "CUS0002"],
            "customer_name": ["An (bản gốc)", "An (bản trùng)", "Binh"],
        }
    )

    result = build_dim_customers(df)

    assert result.height == 3
    kept_name = result.filter(pl.col("customer_id") == "CUS0001")["customer_name"].to_list()
    assert kept_name == ["An (bản gốc)"]


def test_build_dim_customers_drops_lineage_columns():
    df = pl.DataFrame(
        {
            "customer_id": ["CUS0001"],
            "customer_name": ["An"],
            "_source_file": ["SRC03_customer_master.csv"],
            "_batch_id": ["batch-1"],
        }
    )

    result = build_dim_customers(df)

    assert "_source_file" not in result.columns
    assert "_batch_id" not in result.columns
    assert "customer_name" in result.columns


def test_build_dim_products_generates_1_based_surrogate_key_and_dedupes_by_product_id():
    df = pl.DataFrame(
        {
            "product_id": ["PRD0001", "PRD0001", "PRD0002"],
            "product_name": ["Sữa tươi (bản gốc)", "Sữa tươi (bản trùng)", "Bánh quy"],
            "_batch_id": ["batch-1", "batch-1", "batch-1"],
        }
    )

    result = build_dim_products(df)

    assert result.height == 3
    assert result["product_key"].to_list() == [-1, 1, 2]
    assert "_batch_id" not in result.columns
    kept_name = result.filter(pl.col("product_id") == "PRD0001")["product_name"].to_list()
    assert kept_name == ["Sữa tươi (bản gốc)"]


def test_build_dim_distributors_generates_1_based_surrogate_key_and_dedupes_by_distributor_id():
    df = pl.DataFrame(
        {
            "distributor_id": ["DIST0001", "DIST0001", "DIST0002"],
            "distributor_name": ["Kho A (bản gốc)", "Kho A (bản trùng)", "Kho B"],
            "_batch_id": ["batch-1", "batch-1", "batch-1"],
        }
    )

    result = build_dim_distributors(df)

    assert result.height == 3
    assert result["distributor_key"].to_list() == [-1, 1, 2]
    assert "_batch_id" not in result.columns
    kept_name = result.filter(pl.col("distributor_id") == "DIST0001")["distributor_name"].to_list()
    assert kept_name == ["Kho A (bản gốc)"]


def test_build_dim_customers_has_exactly_1_unknown_member_row():
    df = pl.DataFrame({"customer_id": ["CUS0001"], "customer_name": ["An"]})

    result = build_dim_customers(df)

    unknown_rows = result.filter(pl.col("customer_key") == -1)
    assert unknown_rows.height == 1
    assert unknown_rows["customer_id"].to_list() == ["UNKNOWN"]


def test_build_dim_products_has_exactly_1_unknown_member_row():
    df = pl.DataFrame({"product_id": ["PRD0001"], "product_name": ["Bánh quy"]})

    result = build_dim_products(df)

    unknown_rows = result.filter(pl.col("product_key") == -1)
    assert unknown_rows.height == 1
    assert unknown_rows["product_id"].to_list() == ["UNKNOWN"]


def test_build_dim_distributors_has_exactly_1_unknown_member_row():
    df = pl.DataFrame({"distributor_id": ["DIST0001"], "distributor_name": ["Kho A"]})

    result = build_dim_distributors(df)

    unknown_rows = result.filter(pl.col("distributor_key") == -1)
    assert unknown_rows.height == 1
    assert unknown_rows["distributor_id"].to_list() == ["UNKNOWN"]


def test_build_dim_customers_drops_pii_columns():
    df = pl.DataFrame(
        {
            "customer_id": ["CUS0001"],
            "customer_name": ["An"],
            "address": ["123 Lê Lợi"],
            "phone": ["0900000000"],
            "tax_code": ["MST0001"],
        }
    )

    result = build_dim_customers(df)

    assert "address" not in result.columns
    assert "phone" not in result.columns
    assert "tax_code" not in result.columns
    assert "customer_name" in result.columns


def test_build_dim_distributors_drops_pii_columns():
    df = pl.DataFrame(
        {
            "distributor_id": ["DIST0001"],
            "distributor_name": ["Kho A"],
            "phone": ["0900000000"],
            "tax_code": ["MST0001"],
        }
    )

    result = build_dim_distributors(df)

    assert "phone" not in result.columns
    assert "tax_code" not in result.columns
    assert "distributor_name" in result.columns


def test_build_dim_date_covers_full_min_to_max_range_inclusive():
    df = pl.DataFrame(
        {"order_date": [date(2024, 1, 1), date(2024, 1, 3)]},
    )

    result = build_dim_date(df)

    assert result.height == 3
    assert result["full_date"].to_list() == [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)]


def test_build_dim_date_generates_yyyymmdd_integer_date_key():
    df = pl.DataFrame({"order_date": [date(2024, 1, 1), date(2024, 1, 1)]})

    result = build_dim_date(df)

    assert result["date_key"].to_list() == [20240101]


def test_build_dim_date_derives_year_quarter_month_day():
    df = pl.DataFrame({"order_date": [date(2024, 3, 15), date(2024, 3, 15)]})

    result = build_dim_date(df)

    row = result.row(0, named=True)
    assert row["year"] == 2024
    assert row["quarter"] == 1
    assert row["month"] == 3
    assert row["day"] == 15


def test_build_dim_date_column_order_matches_erd():
    df = pl.DataFrame({"order_date": [date(2024, 1, 1), date(2024, 1, 1)]})

    result = build_dim_date(df)

    assert result.columns == ["date_key", "full_date", "year", "quarter", "month", "day"]


def test_add_scd2_valid_dates_covers_middle_resigned_and_active_last_versions():
    df = pl.DataFrame(
        {
            "employee_id": ["EMP001", "EMP001", "EMP002"],
            "version": ["v1", "v2", "v1"],
            "effective_date": [date(2024, 1, 1), date(2024, 6, 1), date(2024, 1, 1)],
            "resign_date": [None, None, date(2024, 9, 30)],
        }
    )

    result = add_scd2_valid_dates(df)

    rows = {(r["employee_id"], r["version"]): r for r in result.to_dicts()}
    # EMP001 v1: không phải version cuối -> valid_to = effective_date của v2
    assert rows[("EMP001", "v1")]["valid_from"] == date(2024, 1, 1)
    assert rows[("EMP001", "v1")]["valid_to"] == date(2024, 6, 1)
    # EMP001 v2: version cuối, đang làm (resign_date NULL) -> valid_to = NULL
    assert rows[("EMP001", "v2")]["valid_from"] == date(2024, 6, 1)
    assert rows[("EMP001", "v2")]["valid_to"] is None
    # EMP002 v1: version cuối, đã nghỉ -> valid_to = resign_date
    assert rows[("EMP002", "v1")]["valid_from"] == date(2024, 1, 1)
    assert rows[("EMP002", "v1")]["valid_to"] == date(2024, 9, 30)


def test_add_scd2_valid_dates_sorts_input_regardless_of_row_order():
    df = pl.DataFrame(
        {
            "employee_id": ["EMP001", "EMP001"],
            "version": ["v2", "v1"],
            "effective_date": [date(2024, 6, 1), date(2024, 1, 1)],
            "resign_date": [None, None],
        }
    )

    result = add_scd2_valid_dates(df)

    rows = {r["version"]: r for r in result.to_dicts()}
    assert rows["v1"]["valid_to"] == date(2024, 6, 1)
    assert rows["v2"]["valid_to"] is None


def test_add_is_current_flag_true_when_valid_to_is_null():
    df = pl.DataFrame(
        {
            "employee_id": ["EMP001"],
            "valid_from": [date(2024, 6, 1)],
            "valid_to": [None],
        }
    )

    result = add_is_current_flag(df)

    assert result["is_current"].to_list() == [True]


def test_add_is_current_flag_false_when_valid_to_is_a_future_version_date():
    df = pl.DataFrame(
        {
            "employee_id": ["EMP001"],
            "valid_from": [date(2024, 1, 1)],
            "valid_to": [date(2024, 6, 1)],
        }
    )

    result = add_is_current_flag(df)

    assert result["is_current"].to_list() == [False]


def test_add_is_current_flag_false_for_last_version_of_resigned_employee():
    # AC quan trọng nhất: nhân viên đã nghỉ (valid_to = resign_date, KHÔNG NULL)
    # không được có version nào is_current=True.
    df = pl.DataFrame(
        {
            "employee_id": ["EMP002"],
            "valid_from": [date(2024, 1, 1)],
            "valid_to": [date(2024, 9, 30)],
        }
    )

    result = add_is_current_flag(df)

    assert result["is_current"].to_list() == [False]


def test_build_dim_employees_chains_scd2_dates_flag_and_surrogate_key():
    df = pl.DataFrame(
        {
            "employee_id": ["EMP001", "EMP001", "EMP002"],
            "version": ["v1", "v2", "v1"],
            "effective_date": [date(2024, 1, 1), date(2024, 6, 1), date(2024, 1, 1)],
            "resign_date": [None, None, date(2024, 9, 30)],
            "_batch_id": ["batch-1", "batch-1", "batch-1"],
        }
    )

    result = build_dim_employees(df)

    assert "_batch_id" not in result.columns
    assert result.columns[0] == "employee_key"
    real_rows = result.filter(pl.col("employee_key") != -1)
    assert real_rows["employee_key"].to_list() == [1, 2, 3]

    rows = {(r["employee_id"], r["version"]): r for r in real_rows.to_dicts()}
    # EMP001 v1: không phải version cuối -> valid_to = effective_date của v2, không phải current
    assert rows[("EMP001", "v1")]["valid_to"] == date(2024, 6, 1)
    assert rows[("EMP001", "v1")]["is_current"] is False
    # EMP001 v2: version cuối, đang làm (resign_date NULL) -> valid_to NULL, đang current
    assert rows[("EMP001", "v2")]["valid_to"] is None
    assert rows[("EMP001", "v2")]["is_current"] is True
    # EMP002 v1: version cuối, đã nghỉ -> valid_to = resign_date, KHÔNG current
    assert rows[("EMP002", "v1")]["valid_to"] == date(2024, 9, 30)
    assert rows[("EMP002", "v1")]["is_current"] is False


def test_build_dim_employees_unknown_member_has_is_current_false_not_null():
    df = pl.DataFrame(
        {
            "employee_id": ["EMP001"],
            "version": ["v1"],
            "effective_date": [date(2024, 1, 1)],
            "resign_date": [None],
        }
    )

    result = build_dim_employees(df)

    unknown_rows = result.filter(pl.col("employee_key") == -1)
    assert unknown_rows.height == 1
    unknown_row = unknown_rows.row(0, named=True)
    assert unknown_row["employee_id"] == "UNKNOWN"
    assert unknown_row["valid_from"] is None
    assert unknown_row["valid_to"] is None
    # Must be False, not null — a null is_current would break any dashboard/report
    # filter that does filter(pl.col("is_current")) expecting a plain boolean.
    assert unknown_row["is_current"] is False


def test_build_dim_employees_drops_pii_columns():
    df = pl.DataFrame(
        {
            "employee_id": ["EMP001"],
            "version": ["v1"],
            "effective_date": [date(2024, 1, 1)],
            "resign_date": [None],
            "phone": ["0900000000"],
            "date_of_birth": [date(1990, 1, 1)],
        }
    )

    result = build_dim_employees(df)

    assert "phone" not in result.columns
    assert "date_of_birth" not in result.columns
    assert "employee_id" in result.columns


def test_join_employee_asof_resolves_version_change_missing_employee_and_resignation():
    dim_employees = pl.DataFrame(
        {
            "employee_id": ["EMP001", "EMP001", "EMP002", "UNKNOWN"],
            "employee_key": [1, 2, 3, -1],
            "valid_from": [date(2024, 1, 1), date(2024, 6, 1), date(2024, 1, 1), None],
            "valid_to": [date(2024, 6, 1), None, date(2024, 9, 30), None],
        }
    )
    orders = pl.DataFrame(
        {
            "order_id": ["O1", "O2", "O3", "O4"],
            "order_date": [date(2024, 2, 1), date(2024, 7, 1), date(2024, 11, 1), date(2024, 3, 1)],
            "employee_id": ["EMP001", "EMP001", "EMP002", "EMP999"],
        }
    )

    result = join_employee_asof(orders, dim_employees, "order_date")

    assert "valid_from" not in result.columns
    assert "valid_to" not in result.columns
    rows = {r["order_id"]: r["employee_key"] for r in result.to_dicts()}
    assert rows["O1"] == 1  # trong khoảng version v1 (2024-01-01 .. 2024-06-01)
    assert rows["O2"] == 2  # sau khi đổi vùng, version v2 đang active (valid_to=NULL)
    assert rows["O3"] == -1  # SAU ngày nghỉ việc (2024-09-30) — KHÔNG match version cũ, KHÔNG null
    assert rows["O4"] == -1  # employee_id không tồn tại trong dim_employees
    assert result["employee_key"].null_count() == 0


def test_build_fact_sales_resolves_all_fks_with_no_nulls():
    dim_customers = build_dim_customers(
        pl.DataFrame({"customer_id": ["CUS0001", "CUS0002"], "customer_name": ["An", "Binh"]})
    )
    dim_products = build_dim_products(
        pl.DataFrame({"product_id": ["PRD0001", "PRD0002"], "product_name": ["Sữa", "Bánh"]})
    )
    dim_employees = build_dim_employees(
        pl.DataFrame(
            {
                "employee_id": ["EMP001", "EMP001", "EMP002"],
                "version": ["v1", "v2", "v1"],
                "effective_date": [date(2024, 1, 1), date(2024, 6, 1), date(2024, 1, 1)],
                "resign_date": [None, None, date(2024, 9, 30)],
            }
        )
    )
    sales = pl.DataFrame(
        {
            "order_id": ["O1", "O2", "O3", "O4"],
            "order_date": [date(2024, 2, 1), date(2024, 7, 1), date(2024, 11, 1), date(2024, 3, 1)],
            "customer_id": ["CUS0001", "CUS0002", "CUS9999", "CUS0001"],
            "product_id": ["PRD0001", "PRD0002", "PRD0001", "PRD9999"],
            "employee_id": ["EMP001", "EMP001", "EMP002", "EMP999"],
            "net_amount": [100.0, 200.0, 50.0, 75.0],
        }
    )
    dim_date = build_dim_date(sales)

    result = build_fact_sales(sales, dim_customers, dim_products, dim_employees, dim_date)

    fk_cols = ["customer_key", "product_key", "date_key", "employee_key"]
    assert result.select(fk_cols).null_count().sum_horizontal().sum() == 0

    rows = {r["order_id"]: r for r in result.to_dicts()}
    assert rows["O1"]["customer_key"] == 1
    assert rows["O1"]["product_key"] == 1
    assert rows["O1"]["date_key"] == 20240201
    assert rows["O1"]["employee_key"] == 1  # EMP001 v1, còn hiệu lực tại 2024-02-01

    assert rows["O2"]["employee_key"] == 2  # EMP001 v2 (đổi vùng), đúng version tại 2024-07-01

    assert rows["O3"]["customer_key"] == -1  # CUS9999 không tồn tại
    assert rows["O3"]["employee_key"] == -1  # EMP002 đã nghỉ trước 2024-11-01

    assert rows["O4"]["product_key"] == -1  # PRD9999 không tồn tại
    assert rows["O4"]["employee_key"] == -1  # EMP999 không tồn tại trong dim_employees


def test_build_fact_targets_resolves_employee_key_keeps_year_month_no_date_key():
    dim_employees = build_dim_employees(
        pl.DataFrame(
            {
                "employee_id": ["EMP001", "EMP001"],
                "version": ["v1", "v2"],
                "effective_date": [date(2024, 1, 1), date(2024, 6, 1)],
                "resign_date": [None, None],
            }
        )
    )
    targets = pl.DataFrame(
        {
            "employee_id": ["EMP001", "EMP001", "EMP999"],
            "region": ["North", "South", "East"],
            "year": [2024, 2024, 2024],
            "month": [2, 7, 3],
            "target_revenue": [1000.0, 2000.0, 500.0],
        }
    )

    result = build_fact_targets(targets, dim_employees)

    assert result.height == targets.height
    assert "date_key" not in result.columns
    assert "_target_date" not in result.columns
    assert result["employee_key"].null_count() == 0

    rows = {(r["employee_id"], r["month"]): r for r in result.to_dicts()}
    assert rows[("EMP001", 2)]["employee_key"] == 1  # tháng 2, còn ở version v1
    assert rows[("EMP001", 7)]["employee_key"] == 2  # tháng 7, đã đổi sang version v2
    assert rows[("EMP999", 3)]["employee_key"] == -1  # employee_id không tồn tại
    # year/month giữ nguyên giá trị gốc, không bị đổi kiểu hay giá trị
    assert rows[("EMP001", 2)]["year"] == 2024
    assert rows[("EMP001", 2)]["target_revenue"] == 1000.0


def test_fact_sales_and_fact_targets_preserve_run_date_and_batch_id_lineage_cols():
    dim_customers = build_dim_customers(
        pl.DataFrame({"customer_id": ["CUS0001"], "customer_name": ["An"]})
    )
    dim_products = build_dim_products(
        pl.DataFrame({"product_id": ["PRD0001"], "product_name": ["Sữa"]})
    )
    dim_employees = build_dim_employees(
        pl.DataFrame(
            {
                "employee_id": ["EMP001"],
                "version": ["v1"],
                "effective_date": [date(2024, 1, 1)],
                "resign_date": [None],
            }
        )
    )
    sales = pl.DataFrame(
        {
            "order_id": ["O1"],
            "order_date": [date(2024, 2, 1)],
            "customer_id": ["CUS0001"],
            "product_id": ["PRD0001"],
            "employee_id": ["EMP001"],
            "net_amount": [100.0],
            "_run_date": ["2024-02-01"],
            "_batch_id": ["batch-abc"],
        }
    )
    dim_date = build_dim_date(sales)

    fact_sales = build_fact_sales(sales, dim_customers, dim_products, dim_employees, dim_date)

    assert "_run_date" in fact_sales.columns
    assert "_batch_id" in fact_sales.columns

    targets = pl.DataFrame(
        {
            "employee_id": ["EMP001"],
            "year": [2024],
            "month": [2],
            "target_revenue": [1000.0],
            "_run_date": ["2024-02-01"],
            "_batch_id": ["batch-xyz"],
        }
    )

    fact_targets = build_fact_targets(targets, dim_employees)

    assert "_run_date" in fact_targets.columns
    assert "_batch_id" in fact_targets.columns


def test_build_dim_territory_generates_surrogate_key_and_unknown_member():
    df = pl.DataFrame(
        {
            "territory_id": ["TER0001", "TER0002"],
            "employee_id": ["EMP001", "EMP002"],
            "customer_id": ["CUS0001", "CUS0002"],
            "region": ["North", "South"],
            "team": ["Team A", "Team B"],
            "_batch_id": ["batch-1", "batch-1"],
        }
    )

    result = build_dim_territory(df)

    assert "_batch_id" not in result.columns
    assert result["territory_key"].to_list() == [-1, 1, 2]

    unknown_rows = result.filter(pl.col("territory_key") == -1)
    assert unknown_rows.height == 1
    assert unknown_rows["territory_id"].to_list() == ["UNKNOWN"]

    real_row = result.filter(pl.col("territory_id") == "TER0001").row(0, named=True)
    assert real_row["region"] == "North"
    assert real_row["team"] == "Team A"


def test_build_dim_promotion_generates_surrogate_key_and_unknown_member():
    df = pl.DataFrame(
        {
            "promotion_id": ["PROMO0001", "PROMO0002"],
            "promotion_name": ["Khuyến mãi hè", "Khuyến mãi Tết"],
            "start_date": [date(2024, 6, 1), date(2024, 1, 1)],
            "end_date": [date(2024, 6, 30), date(2024, 1, 31)],
            "applicable_products": ["PRD0001,PRD0002", "PRD0003"],
            "_batch_id": ["batch-1", "batch-1"],
        }
    )

    result = build_dim_promotion(df)

    assert "_batch_id" not in result.columns
    assert result["promotion_key"].to_list() == [-1, 1, 2]

    unknown_rows = result.filter(pl.col("promotion_key") == -1)
    assert unknown_rows.height == 1
    assert unknown_rows["promotion_id"].to_list() == ["UNKNOWN"]

    real_row = result.filter(pl.col("promotion_id") == "PROMO0001").row(0, named=True)
    assert real_row["start_date"] == date(2024, 6, 1)
    assert real_row["end_date"] == date(2024, 6, 30)
    assert real_row["applicable_products"] == "PRD0001,PRD0002"
