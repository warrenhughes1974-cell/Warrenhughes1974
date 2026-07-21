# Enterprise Engine Boundary

**Owner:** Project Lead + Enterprise Engine maintainers  
**Status:** Documented dependency only — no engine code in this repository

## Purpose

Define how the Citizens project references the separately owned Enterprise Conversion Engine without copying or modifying engine source.

## Documented Dependencies (Legacy CFIC_Rates)

The following `qla_core` modules are referenced by legacy conversion scripts in `CFIC_Rates` (read-only audit source):

| Module | Usage |
|--------|-------|
| `qla_core.rate_dbf_schema` | QLAdmin physical schema, paging, factor format |
| `qla_core.rate_factor_loader` | Factor grid construction |
| `qla_core.rate_key_setup` | Rate key row generation |
| `qla_core.rate_member_setup` | Dimension member rows |
| `qla_core.rate_dbf_writer` | CSV publish writer |

## Integration Model (Future — Not Implemented in Stage 2A)

- Engine version pinned in `config/engine_boundary/engine_version.yaml` (to be created at Development gate)
- Citizens orchestration calls engine APIs; does not vendor-copy modules
- Citizens-specific logic remains in `conversion/client_extensions/`

## Prohibited

- Copying `qla_core/` or other engine trees into this repository
- Modifying Enterprise Engine from Citizens issues without explicit ownership decision
- Treating CSO conversion patterns as Citizens business rules

## Update Instructions

Record engine version pin and integration contract here when Development is authorized.
