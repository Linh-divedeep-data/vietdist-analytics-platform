import polars as pl

from src.transform_gold import build_dim_customers, build_dim_products


def test_build_dim_customers_generates_1_based_surrogate_key():
    df = pl.DataFrame(
        {
            "customer_id": ["CUS0001", "CUS0002"],
            "customer_name": ["An", "Binh"],
        }
    )

    result = build_dim_customers(df)

    assert result["customer_key"].to_list() == [1, 2]


def test_build_dim_customers_dedupes_by_customer_id_keeping_first_row():
    df = pl.DataFrame(
        {
            "customer_id": ["CUS0001", "CUS0001", "CUS0002"],
            "customer_name": ["An (bản gốc)", "An (bản trùng)", "Binh"],
        }
    )

    result = build_dim_customers(df)

    assert result.height == 2
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

    assert result.height == 2
    assert result["product_key"].to_list() == [1, 2]
    assert "_batch_id" not in result.columns
    kept_name = result.filter(pl.col("product_id") == "PRD0001")["product_name"].to_list()
    assert kept_name == ["Sữa tươi (bản gốc)"]
