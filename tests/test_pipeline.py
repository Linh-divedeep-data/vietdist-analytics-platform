import polars as pl

from src.transform_gold import add_variance_pct, build_mart_sales_vs_target


def test_mart_sales_vs_target():
    fact_sales = pl.DataFrame(
        {
            "order_id": ["O1", "O2", "O3"],
            "region": ["MIỀN BẮC", "MIỀN BẮC", "MIỀN NAM"],
            "order_year": ["2024", "2024", "2024"],
            "order_month": ["1", "1", "1"],
            "net_amount": [100.0, 50.0, 80.0],
        }
    )
    fact_targets = pl.DataFrame(
        {
            "employee_id": ["EMP001", "EMP002"],
            "region": ["MIỀN BẮC", "MIỀN NAM"],
            "year": ["2024", "2024"],
            "month": ["1", "1"],
            "target_revenue": [100.0, 0.0],
        }
    )

    mart = build_mart_sales_vs_target(fact_sales, fact_targets)
    result = add_variance_pct(mart)

    rows = {r["region"]: r for r in result.to_dicts()}

    # MIỀN BẮC: actual = 100 + 50 = 150, target = 100 -> variance_pct = (150-100)/100 = 0.5
    bac = rows["MIỀN BẮC"]
    assert bac["actual_revenue"] == 150.0
    assert bac["target_revenue"] == 100.0
    assert bac["variance_pct"] == 0.5

    # MIỀN NAM: actual = 80, target = 0 -> variance_pct guarded to None, not Inf/crash
    nam = rows["MIỀN NAM"]
    assert nam["actual_revenue"] == 80.0
    assert nam["target_revenue"] == 0.0
    assert nam["variance_pct"] is None
