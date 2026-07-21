# Enterprise Conversion Engine API Contract (Citizens)

**Status:** PINNED (Stage 4D)  
**Distribution package:** `qla-enterprise-conversion-engine`  
**Import package:** `qla_core`  
**Exact version:** `0.1.0`  
**API compatibility version:** `1`  

Citizens requires the following Enterprise Engine surface.

## Required modules

| Module | Import path | Citizens callers | Usage status |
|--------|-------------|------------------|--------------|
| rate_dbf_schema | `qla_core.rate_dbf_schema` | `cfic_reserve_build.py` | Active |
| rate_factor_loader | `qla_core.rate_factor_loader` | `cfic_reserve_build.py` | Active |
| rate_key_setup | `qla_core.rate_key_setup` | `cfic_reserve_build.py` | Active |
| rate_member_setup | `qla_core.rate_member_setup` | `cfic_reserve_build.py` | Active |
| rate_dbf_writer | `qla_core.rate_dbf_writer` | `cfic_rate_publish.py` | Active |

## Required symbols (validated Stage 4D)

| Module | Symbols |
|--------|---------|
| rate_dbf_schema | MAX_AGE, source_duration_to_ql, duration_to_cntl_col, KEY_TABLE |
| rate_factor_loader | LoaderConfig, build_factor_grid, grid_to_factor_rows |
| rate_key_setup | AssumptionProvider, build_key_rows |
| rate_member_setup | build_member_rows |
| rate_dbf_writer | emit_all_rate_tables_csv |

## Integration rules

1. Import only via installed package — no `sys.path` injection.
2. Validate with `tools/engine/check_engine_compatibility.py` (must PASS).
3. Pin recorded in `config/engine_version.yaml` and `config/engine_artifact.yaml`.
4. Editable installs and monorepo source fallback are prohibited.

## Compatibility validation

```bash
.venv/Scripts/python tools/engine/check_engine_compatibility.py
```

Expected: `compatible: true`, `engine_status: PINNED`.

## External artifact

Wheel SHA-256: `320165544a8fc63d882508fb478ae77b911c2d6e4de5647a7408414b299ff674`

Internal artifact repository recommended for long-term distribution.
