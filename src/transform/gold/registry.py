"""BUILD_ORDER: dims before facts before marts — documents/orders run_gold_transform()'s
existing explicit call sequence; not a generic execution loop (Gold's 12 tables have
non-uniform argument lists, unlike Bronze/Silver's uniform per-source callables)."""

BUILD_ORDER = [
    "dim_customers",
    "dim_products",
    "dim_distributors",
    "dim_date",
    "dim_territory",
    "dim_promotion",
    "dim_employees",
    "fact_sales",
    "fact_targets",
    "fact_returns",
    "fact_distributor_orders",
    "mart_sales_vs_target",
]
