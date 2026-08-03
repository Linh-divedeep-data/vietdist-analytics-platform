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
