"""Source registry (CSV_SOURCES, EXCEL_SOURCES, REQUIRED_COLUMNS) — filled in Epic Phase 1 (VDAP-92).

The 10 fixed source files (SRC01-SRC10) per BRD section 2.2. No
imports from src/ here — src/ imports config, not the other way
around (avoids a reverse dependency).
"""

CSV_SOURCES = [
    "SRC01_sales_transactions.csv",
    "SRC03_customer_master.csv",
    "SRC06_distributor_master.csv",
    "SRC09_return_transactions.csv",
]

EXCEL_SOURCES = [
    "SRC02_sales_target_plan.xlsx",
    "SRC04_product_master.xlsx",
    "SRC05_distributor_orders.xlsx",
    "SRC07_employee_master.xlsx",
    "SRC08_territory_mapping.xlsx",
    "SRC10_promotion_program.xlsx",
]

REQUIRED_COLUMNS: dict[str, list[str]] = {
    "SRC01_sales_transactions.csv": [
        "order_id", "order_date", "order_month", "order_quarter", "order_year",
        "customer_id", "region", "province", "channel", "employee_id",
        "product_id", "product_category", "quantity", "unit_price",
        "discount_pct", "discount_amount", "gross_amount", "net_amount",
        "delivery_status", "payment_method", "payment_status",
    ],
    "SRC02_sales_target_plan.xlsx": [
        "plan_version", "version_date", "effective_from", "effective_to",
        "employee_id", "employee_name", "region", "team", "year", "month",
        "target_revenue", "target_quantity", "target_new_customers",
    ],
    "SRC03_customer_master.csv": [
        "customer_id", "customer_name", "customer_type", "channel", "province",
        "region", "address", "phone", "tax_code", "join_date", "credit_limit",
        "status",
    ],
    "SRC04_product_master.xlsx": [
        "product_id", "product_name", "category", "sub_category", "unit",
        "unit_price", "cost_price", "weight_gram", "status", "launch_date",
    ],
    "SRC05_distributor_orders.xlsx": [
        "order_id", "order_date", "order_month", "order_quarter",
        "distributor_id", "region", "channel", "product_id",
        "product_category", "qty_ordered", "qty_delivered", "fill_rate_pct",
        "unit_price_list", "distributor_price", "gross_amount",
        "delivered_amount", "expected_delivery_date", "actual_delivery_date",
        "ontime_delivery", "delivery_status", "payment_terms",
    ],
    "SRC06_distributor_master.csv": [
        "distributor_id", "distributor_name", "tier", "channel", "province",
        "region", "contact_person", "phone", "email", "tax_code", "join_date",
        "credit_limit", "status", "assigned_supervisor_id",
    ],
    "SRC07_employee_master.xlsx": [
        "employee_id", "full_name", "gender", "date_of_birth", "join_date",
        "position", "region", "team", "email", "phone", "status", "version",
        "effective_date", "resign_date", "transfer_note",
    ],
    "SRC08_territory_mapping.xlsx": [
        "territory_id", "employee_id", "customer_id", "region", "team",
        "effective_date", "expiry_date", "version",
    ],
    "SRC09_return_transactions.csv": [
        "return_id", "original_order_id", "return_date", "return_month",
        "customer_id", "employee_id", "product_id", "region", "province",
        "return_quantity", "unit_price", "return_amount", "return_reason",
        "status",
    ],
    "SRC10_promotion_program.xlsx": [
        "promotion_id", "promotion_name", "promotion_type", "target_channel",
        "target_region", "start_date", "end_date", "applicable_products",
        "discount_pct", "min_order_quantity", "budget_vnd", "actual_cost_vnd",
        "status", "created_by",
    ],
}
