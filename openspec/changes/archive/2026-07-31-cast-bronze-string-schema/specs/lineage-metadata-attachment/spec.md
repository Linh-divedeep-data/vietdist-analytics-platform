## ADDED Requirements

### Requirement: All columns String-typed before Bronze write
The system SHALL provide `cast_to_string(df: pl.DataFrame) -> pl.DataFrame` in `src/extract.py` that casts every column of the given DataFrame to `pl.String`, and `main()` SHALL call it on each source's DataFrame immediately after `attach_lineage()`.

#### Scenario: Non-String lineage column becomes String
- **WHEN** `cast_to_string()` is called on a DataFrame produced by `attach_lineage()` (whose `_ingested_at` column is `pl.Datetime`)
- **THEN** every column in the returned DataFrame, including `_ingested_at`, has dtype `pl.String`

#### Scenario: Already-String columns are unaffected
- **WHEN** `cast_to_string()` is called on a DataFrame where every column is already `pl.String`
- **THEN** the returned DataFrame has the same values and dtypes, unchanged
