"""run_gold_transform(): read data/silver/<date>/, build per registry.BUILD_ORDER,
write data/gold/<date>/."""

import os
import uuid

import polars as pl

from config.settings import GOLD_DIR, SILVER_DIR
from src.logger import get_logger
from src.transform.gold.dims.dim_customers import build_dim_customers
from src.transform.gold.dims.dim_date import build_dim_date
from src.transform.gold.dims.dim_distributors import build_dim_distributors
from src.transform.gold.dims.dim_employees import build_dim_employees
from src.transform.gold.dims.dim_products import build_dim_products
from src.transform.gold.dims.dim_promotion import build_dim_promotion
from src.transform.gold.dims.dim_territory import build_dim_territory
from src.transform.gold.facts.fact_distributor_orders import build_fact_distributor_orders
from src.transform.gold.facts.fact_returns import build_fact_returns
from src.transform.gold.facts.fact_sales import build_fact_sales
from src.transform.gold.facts.fact_targets import build_fact_targets
from src.transform.gold.log import build_gold_log_record, write_gold_log
from src.transform.gold.marts.mart_sales_vs_target import add_variance_pct, build_mart_sales_vs_target
from src.transform.gold.registry import BUILD_ORDER
from src.transform.silver.orchestrator import get_silver_output_dir


def get_gold_output_dir(run_date: str, gold_dir: str = GOLD_DIR) -> str:
    """Return (creating if needed) the Gold output directory for a run_date."""
    out_dir = os.path.join(gold_dir, run_date.replace("-", ""))
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def write_gold_parquet(df: pl.DataFrame, table_name: str, out_dir: str) -> str:
    """Write a built Gold table (Dim/Fact/Mart) to out_dir/<table_name>.parquet."""
    path = os.path.join(out_dir, f"{table_name}.parquet")
    df.write_parquet(path)
    return path


def run_gold_transform(
    run_date: str, silver_dir: str = SILVER_DIR, gold_dir: str = GOLD_DIR, batch_id: str | None = None
) -> list[dict]:
    """Build every Dim/Fact/Mart table from Silver output and write them to Gold.
    Unlike Bronze/Silver (independent per-source loops), Gold's 12 tables form one
    dependency chain (dims -> facts -> mart) — a failure anywhere aborts the whole
    batch instead of skipping just one source, reported as a single failed record.
    batch_id is optional (mirrors run_silver_transform) — a fresh uuid4 is generated
    here when the caller doesn't supply one, purely to stamp the error log line."""
    silver_source_dir = get_silver_output_dir(run_date, silver_dir)
    out_dir = get_gold_output_dir(run_date, gold_dir)

    def read(source_name: str) -> pl.DataFrame:
        return pl.read_parquet(os.path.join(silver_source_dir, f"{source_name}.parquet"))

    try:
        dim_customers = build_dim_customers(read("SRC03_customer_master"))
        dim_products = build_dim_products(read("SRC04_product_master"))
        dim_distributors = build_dim_distributors(read("SRC06_distributor_master"))
        dim_territory = build_dim_territory(read("SRC08_territory_mapping"))
        dim_promotion = build_dim_promotion(read("SRC10_promotion_program"))
        dim_employees = build_dim_employees(read("SRC07_employee_master"))

        sales_silver = read("SRC01_sales_transactions")
        dim_date = build_dim_date(sales_silver)

        fact_sales = build_fact_sales(sales_silver, dim_customers, dim_products, dim_employees, dim_date)
        fact_targets = build_fact_targets(read("SRC02_sales_target_plan"), dim_employees)
        fact_returns = build_fact_returns(read("SRC09_return_transactions"), dim_customers, dim_products, dim_employees)
        fact_distributor_orders = build_fact_distributor_orders(
            read("SRC05_distributor_orders"), dim_distributors, dim_products
        )

        mart_sales_vs_target = add_variance_pct(build_mart_sales_vs_target(fact_sales, fact_targets))

        tables = {
            "dim_customers": dim_customers,
            "dim_products": dim_products,
            "dim_distributors": dim_distributors,
            "dim_date": dim_date,
            "dim_territory": dim_territory,
            "dim_promotion": dim_promotion,
            "dim_employees": dim_employees,
            "fact_sales": fact_sales,
            "fact_targets": fact_targets,
            "fact_returns": fact_returns,
            "fact_distributor_orders": fact_distributor_orders,
            "mart_sales_vs_target": mart_sales_vs_target,
        }
        for table_name in BUILD_ORDER:
            df = tables[table_name]
            write_gold_parquet(df, table_name, out_dir)
            write_gold_log(
                build_gold_log_record(table_name, run_date, df.height, "success"), out_dir
            )

        return [{"table_name": name, "status": "success"} for name in BUILD_ORDER]
    except Exception as error:  # noqa: BLE001 -- any failure anywhere in this interdependent chain aborts the whole Gold batch
        get_logger(batch_id or str(uuid.uuid4())).error("Gold layer transform thất bại: %s", error)
        write_gold_log(
            build_gold_log_record("gold_layer", run_date, 0, "failed", str(error)), out_dir
        )
        return [{"table_name": "gold_layer", "status": "failed", "error": str(error)}]
