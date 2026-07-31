## ADDED Requirements

### Requirement: Read all 4 CSV sources into DataFrames
The system SHALL read the 4 CSV sources (SRC01_sales_transactions.csv, SRC03_customer_master.csv, SRC06_distributor_master.csv, SRC09_return_transactions.csv) from a raw data directory into Polars DataFrames, using `pl.read_csv()`, and return them keyed by source filename.

#### Scenario: All 4 CSV files present in raw directory
- **WHEN** `read_csv_sources()` is called with a raw directory containing all 4 CSV source files
- **THEN** it returns a dict with exactly the 4 source filenames as keys, each mapped to a Polars DataFrame

#### Scenario: Row count matches source file
- **WHEN** a CSV source file has N data rows (excluding header)
- **THEN** the corresponding returned DataFrame has height N, and N is greater than 0 for a non-empty source file

### Requirement: Raw directory is configurable
The system SHALL accept the raw data directory as a parameter (defaulting to `data/raw`) rather than hardcoding the path, so callers (including tests) can point at an alternate directory.

#### Scenario: Custom raw directory
- **WHEN** `read_csv_sources()` is called with `raw_dir` set to a directory other than `data/raw`
- **THEN** it reads the 4 CSV source files from that directory instead of `data/raw`
