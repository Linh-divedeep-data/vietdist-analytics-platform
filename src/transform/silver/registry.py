"""SOURCE_OVERRIDES: sources needing extra Silver steps beyond the 6 standard ones."""

from src.transform.silver.unit_of_work.src03_customer_master import (
    apply_customer_master_overrides,
)

SOURCE_OVERRIDES = {
    "SRC03_customer_master.csv": [apply_customer_master_overrides],
}
