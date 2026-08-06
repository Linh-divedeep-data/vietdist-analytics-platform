from datetime import date

import polars as pl

from src.transform_gold import build_dim_employees


def test_scd2_valid_to():
    silver_df = pl.DataFrame(
        {
            "employee_id": ["EMP001", "EMP001", "EMP002"],
            "version": ["v1", "v2", "v1"],
            "effective_date": [date(2024, 1, 1), date(2024, 6, 1), date(2024, 1, 1)],
            "resign_date": [None, None, date(2024, 9, 30)],
        }
    )

    result = build_dim_employees(silver_df)
    rows = result.filter(pl.col("employee_id") != "UNKNOWN").to_dicts()
    versions = {(r["employee_id"], r["version"]): r for r in rows}

    # Case 1 — đổi vùng: version cũ (v1) valid_to phải = effective_date của version mới (v2)
    emp001_v1 = versions[("EMP001", "v1")]
    emp001_v2 = versions[("EMP001", "v2")]
    assert emp001_v1["valid_to"] == date(2024, 6, 1)
    assert emp001_v1["valid_to"] == emp001_v2["effective_date"]
    assert emp001_v1["is_current"] is False
    assert emp001_v2["is_current"] is True  # version mới nhất, còn đang làm việc

    # Case 2 — nghỉ việc: valid_to của version cuối PHẢI = resign_date, KHÔNG được NULL
    emp002_v1 = versions[("EMP002", "v1")]
    assert emp002_v1["valid_to"] == date(2024, 9, 30)
    assert emp002_v1["valid_to"] is not None
    assert emp002_v1["is_current"] is False
