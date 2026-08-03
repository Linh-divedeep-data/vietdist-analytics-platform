# VDAP-198: REQUIRED_COLUMNS + validate_schema() Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `REQUIRED_COLUMNS` (source filename → required column list) to `config/sources.py`, and `validate_schema(df, source_file)` + `SchemaMismatchError` to `src/extract/parser.py`, so a Bronze-layer DataFrame missing a required column fails fast with a clear error, while extra/unexpected columns are only logged, never blocked.

**Architecture:** `REQUIRED_COLUMNS` is a plain `dict[str, list[str]]` literal in `config/sources.py`, keyed by the exact same 10 filenames already in `CSV_SOURCES`/`EXCEL_SOURCES`, values taken verbatim from BRD §2.2 Data Dictionary. `validate_schema()` in `parser.py` imports `REQUIRED_COLUMNS`, diffs `set(df.columns)` against `set(REQUIRED_COLUMNS[source_file])`, logs a warning for extra columns (via a plain module logger — see Global Constraints), and raises a new `SchemaMismatchError(Exception)` carrying `source_file`, `missing_cols`, `extra_cols` when anything required is missing.

**Tech Stack:** Polars (`pl.DataFrame`, already a dependency), Python stdlib `logging`. No new dependencies.

## Global Constraints

- `REQUIRED_COLUMNS` keys must exactly match the 10 filenames already declared in `CSV_SOURCES` + `EXCEL_SOURCES` in `config/sources.py` — no new filenames, no renaming.
- `config/sources.py` must not import from `src/` (existing `test_sources_module_does_not_import_from_src` enforces this) — `REQUIRED_COLUMNS` is a plain literal, no imports needed.
- Do not modify `download_all_sources()`, `read_csv_source()`, or `read_excel_source()` in `src/extract/parser.py` — append only.
- `validate_schema(df, source_file)` takes exactly these two parameters — no `batch_id`. Because of this, the extra-column warning **cannot** go through `src/logger.py`'s `get_logger(batch_id)` — that logger's format string (`%(batch_id)s`) requires a `batch_id` on every record, which a `LoggerAdapter` normally supplies; calling it here without one would raise a `KeyError` during formatting. Use a plain, module-scoped `logging.getLogger(__name__)` instead — independent of the shared batch-scoped pipeline logger, and safe to call with no batch context.
- `SchemaMismatchError` must be its own `Exception` subclass (not `ValueError`), per AC — so a later orchestrator ticket can catch it distinctly and map it to `status="schema_mismatch"` in the ingest log.
- Extra columns are never blocking on their own — only a raise-worthy condition (missing required columns) may raise; when both missing and extra columns exist, still log the extra-column warning before raising for the missing ones.

---

### Task A: `REQUIRED_COLUMNS` in `config/sources.py`

**Files:**
- Modify: `config/sources.py` (append `REQUIRED_COLUMNS` after `EXCEL_SOURCES`)
- Test: `tests/test_sources.py` (append after existing tests)

**Interfaces:**
- Produces: `REQUIRED_COLUMNS: dict[str, list[str]]` — keys are the 10 filenames from `CSV_SOURCES`/`EXCEL_SOURCES`; values are non-empty lists of required column names (used by Task B's `validate_schema`).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_sources.py`:

```python
from config.sources import CSV_SOURCES, EXCEL_SOURCES, REQUIRED_COLUMNS


def test_required_columns_has_entry_for_every_source():
    assert set(REQUIRED_COLUMNS.keys()) == set(CSV_SOURCES) | set(EXCEL_SOURCES)


def test_required_columns_values_are_non_empty_lists():
    for source_file, columns in REQUIRED_COLUMNS.items():
        assert isinstance(columns, list)
        assert len(columns) > 0
        assert len(columns) == len(set(columns)), f"{source_file} has duplicate columns"
```

Note: the existing top-of-file import `from config.sources import CSV_SOURCES, EXCEL_SOURCES` must be replaced by the line above (adding `REQUIRED_COLUMNS` to the same import) rather than duplicated.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_sources.py -k required_columns -v`
Expected: FAIL with `ImportError: cannot import name 'REQUIRED_COLUMNS' from 'config.sources'`

- [ ] **Step 3: Write minimal implementation**

Append to `config/sources.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_sources.py -v`
Expected: all pass (5 pre-existing + 2 new = 7 passed)

- [ ] **Step 5: Commit**

```bash
git add config/sources.py tests/test_sources.py
git commit -m "feat(VDAP-198): add REQUIRED_COLUMNS data dictionary to config/sources.py"
```

---

### Task B: `SchemaMismatchError` + `validate_schema()` in `src/extract/parser.py`

**Files:**
- Modify: `src/extract/parser.py`
- Test: `tests/test_parser.py`

**Interfaces:**
- Consumes: `REQUIRED_COLUMNS: dict[str, list[str]]` from `config.sources` (Task A).
- Produces: `class SchemaMismatchError(Exception)` with attributes `source_file: str`, `missing_cols: list[str]`, `extra_cols: list[str]`; `validate_schema(df: pl.DataFrame, source_file: str) -> None`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_parser.py`:

```python
def test_validate_schema_passes_when_all_required_columns_present():
    df = pl.DataFrame(
        {col: ["x"] for col in REQUIRED_COLUMNS["SRC03_customer_master.csv"]}
    )

    parser.validate_schema(df, "SRC03_customer_master.csv")  # must not raise


def test_validate_schema_raises_schema_mismatch_error_when_column_missing():
    columns = REQUIRED_COLUMNS["SRC03_customer_master.csv"].copy()
    columns.remove("phone")
    df = pl.DataFrame({col: ["x"] for col in columns})

    with pytest.raises(parser.SchemaMismatchError) as exc_info:
        parser.validate_schema(df, "SRC03_customer_master.csv")

    error = exc_info.value
    assert error.source_file == "SRC03_customer_master.csv"
    assert error.missing_cols == ["phone"]
    assert "phone" in str(error)
    assert "SRC03_customer_master.csv" in str(error)


def test_validate_schema_logs_warning_and_does_not_raise_on_extra_column(caplog):
    df = pl.DataFrame(
        {col: ["x"] for col in REQUIRED_COLUMNS["SRC03_customer_master.csv"]}
    )
    df = df.with_columns(pl.lit("y").alias("unexpected_extra_col"))

    with caplog.at_level(logging.WARNING):
        parser.validate_schema(df, "SRC03_customer_master.csv")  # must not raise

    assert "unexpected_extra_col" in caplog.text


def test_validate_schema_raises_on_missing_even_with_extra_column(caplog):
    columns = REQUIRED_COLUMNS["SRC03_customer_master.csv"].copy()
    columns.remove("phone")
    df = pl.DataFrame({col: ["x"] for col in columns})
    df = df.with_columns(pl.lit("y").alias("unexpected_extra_col"))

    with caplog.at_level(logging.WARNING):
        with pytest.raises(parser.SchemaMismatchError) as exc_info:
            parser.validate_schema(df, "SRC03_customer_master.csv")

    assert exc_info.value.missing_cols == ["phone"]
    assert "unexpected_extra_col" in caplog.text
```

Add the missing import at the top of `tests/test_parser.py`:

```python
from config.sources import REQUIRED_COLUMNS
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_parser.py -k validate_schema -v`
Expected: FAIL with `AttributeError: module 'src.extract.parser' has no attribute 'validate_schema'` (and `'SchemaMismatchError'`)

- [ ] **Step 3: Write minimal implementation**

Add to the imports at the top of `src/extract/parser.py`:

```python
import logging

from config.sources import REQUIRED_COLUMNS
```

Append to `src/extract/parser.py`:

```python
_logger = logging.getLogger(__name__)


class SchemaMismatchError(Exception):
    def __init__(self, source_file: str, missing_cols: list[str], extra_cols: list[str]):
        self.source_file = source_file
        self.missing_cols = missing_cols
        self.extra_cols = extra_cols
        super().__init__(
            f"{source_file}: missing required column(s) {missing_cols}"
        )


def validate_schema(df: pl.DataFrame, source_file: str) -> None:
    required = set(REQUIRED_COLUMNS[source_file])
    actual = set(df.columns)

    missing_cols = sorted(required - actual)
    extra_cols = sorted(actual - required)

    if extra_cols:
        _logger.warning(
            "%s: unexpected extra column(s) %s (not in REQUIRED_COLUMNS)",
            source_file,
            extra_cols,
        )

    if missing_cols:
        raise SchemaMismatchError(source_file, missing_cols, extra_cols)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_parser.py -k validate_schema -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add src/extract/parser.py tests/test_parser.py
git commit -m "feat(VDAP-198): add validate_schema() and SchemaMismatchError"
```

---

### Task C: Full-suite verification

**Files:** none (verification only)

- [ ] **Step 1: Run the affected test files**

Run: `uv run pytest tests/test_sources.py tests/test_parser.py -v`
Expected: all pass (7 in `test_sources.py` + 14 in `test_parser.py` = 21 passed), no regressions.

- [ ] **Step 2: Run the full project test suite**

Run: `uv run pytest -v`
Expected: all tests across the repo pass, nothing else broken by the new `logging`/`config.sources` imports in `parser.py`.

- [ ] **Step 3: Commit (only if Task C caused any fix-up changes)**

Skip commit if Steps 1–2 pass cleanly with no code changes — Tasks A and B already committed the real work.

---

## Self-Review Notes

- **Spec coverage:** `REQUIRED_COLUMNS` for all 10 sources (Task A), `validate_schema()` raising `SchemaMismatchError` on missing columns (Task B), extra columns logged not blocked (Task B), `SchemaMismatchError` as its own `Exception` subclass carrying `source_file`/`missing_cols`/`extra_cols` (Task B) — all AC items from bd covered.
- **No placeholders:** all test and implementation code is complete and runnable as written.
- **Type consistency:** `validate_schema(df: pl.DataFrame, source_file: str) -> None` and `SchemaMismatchError(source_file: str, missing_cols: list[str], extra_cols: list[str])` are used identically between the interface declarations and the implementation steps.
