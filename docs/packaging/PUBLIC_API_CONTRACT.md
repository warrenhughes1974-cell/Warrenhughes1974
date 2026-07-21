# qla_core Public API Contract

**Distribution:** `qla-enterprise-conversion-engine`  
**Import package:** `qla_core`  
**API compatibility version:** 1  
**Stage:** ENG-PKG-001  

Symbols below are required by Citizens Product and Rate Conversion (Stage 4B contract).

## rate_dbf_schema

| Symbol | Stability | Purpose |
|--------|-----------|---------|
| `MAX_AGE` | PUBLIC_STABLE | Age cap for rate emit |
| `STANDARD_EFFDATE` | PUBLIC_STABLE | Default effective date |
| `KEY_TABLE` | PUBLIC_STABLE | Factor table → key table map |
| `duration_to_cntl_col` | PUBLIC_STABLE | QL duration → CNTL/COL |
| `source_duration_to_ql` | PUBLIC_STABLE | Source duration → QL duration |
| `format_factor` | PUBLIC_STABLE | CHAR(7) factor formatter |
| `factor_table_fields` | PUBLIC_STABLE | DBF field spec per factor table |
| `key_table_fields` | PUBLIC_STABLE | DBF field spec per key table |
| `member_table_fields` | PUBLIC_STABLE | Member table field spec |
| `assumption_field_names` | PUBLIC_STABLE | Assumption columns per key table |
| `dbf_spec` | PUBLIC_STABLE | DBF descriptor builder |

**Side effects:** None at import. DBF spec builders are pure.

## rate_factor_loader

| Symbol | Stability | Purpose |
|--------|-----------|---------|
| `LoaderConfig` | PUBLIC_STABLE | Externalized segment defaults |
| `load_plan_crosswalk` | PUBLIC_PROVISIONAL | Excel crosswalk loader (requires openpyxl at call time) |
| `transform_source` | PUBLIC_STABLE | Source row transform |
| `build_factor_grid` | PUBLIC_STABLE | Pivot to factor grid |
| `grid_to_factor_rows` | PUBLIC_STABLE | Grid → factor row dicts |

**Side effects:** `load_plan_crosswalk` reads Excel file when called.

## rate_key_setup

| Symbol | Stability | Purpose |
|--------|-----------|---------|
| `AssumptionProvider` | PUBLIC_STABLE | Externalized assumption mapping |
| `AssumptionProvider.from_rows` | PUBLIC_STABLE | Build provider from CSV rows |
| `build_key_rows` | PUBLIC_STABLE | Derive QuikPlxx key rows |

**Side effects:** None.

## rate_member_setup

| Symbol | Stability | Purpose |
|--------|-----------|---------|
| `build_member_rows` | PUBLIC_STABLE | Build QuikPl* member dimension rows |

**Side effects:** None.

## rate_dbf_writer

| Symbol | Stability | Purpose |
|--------|-----------|---------|
| `emit_all_rate_tables_csv` | PUBLIC_STABLE | Write PascalCase Quik*.csv package |
| `write_table_csv` | PUBLIC_STABLE | Generic CSV table writer |
| `write_factor_table_csv` | PUBLIC_STABLE | Factor table CSV writer |
| `write_key_table_csv` | PUBLIC_STABLE | Key table CSV writer |
| `write_member_table_csv` | PUBLIC_STABLE | Member table CSV writer |

**Side effects:** Writes CSV files when called. DBF writers require optional `dbf` package.

## Package metadata

| Symbol | Stability | Purpose |
|--------|-----------|---------|
| `qla_core.__version__` | PUBLIC_STABLE | Distribution version string |
| `qla_core.API_COMPATIBILITY_VERSION` | PUBLIC_STABLE | API contract generation |

## Existing callers

| Caller | Status |
|--------|--------|
| Citizens `cfic_reserve_build.py` | Active |
| Citizens `cfic_rate_publish.py` | Active |
| CSO `QLA_Migration` rate pipeline | Active (monorepo) |

## Test coverage

ENG-PKG-001 adds `tests/engine_packaging/` contract and import-safety tests.
