## 1. Constants

- [x] 1.1 Add `EXCEL_SOURCES` list to `src/constants.py`: `SRC02_sales_target_plan.xlsx`, `SRC04_product_master.xlsx`, `SRC05_distributor_orders.xlsx`, `SRC07_employee_master.xlsx`, `SRC08_territory_mapping.xlsx`, `SRC10_promotion_program.xlsx`

## 2. Extract function

- [x] 2.1 Add `read_excel_sources(raw_dir: str = "data/raw") -> dict[str, pl.DataFrame]` to `src/extract.py`, mirroring `read_csv_sources()`'s dict-comprehension shape
- [x] 2.2 Read each file with `pl.read_excel(os.path.join(raw_dir, name))`, then force all columns to `pl.String` via `.select(pl.all().cast(pl.String))`
- [x] 2.3 Let missing-file errors propagate naturally (no try/except)

## 3. Tests

- [x] 3.1 Test: returns one DataFrame per `EXCEL_SOURCES` file, `.height` matches source row count
- [x] 3.2 Test: every column dtype is `pl.String` across all returned DataFrames
- [x] 3.3 Test: missing Excel file raises `FileNotFoundError`

## 4. Verification

- [x] 4.1 Run `uv run pytest tests/test_extract.py -v`, confirm new tests pass and existing CSV tests still pass
- [x] 4.2 Run `uv run ruff check src/extract.py src/constants.py tests/test_extract.py`
