# ENG-PKG-001 Repository Authority Report

**Date:** 2026-07-12  
**Verdict:** AUTHORITATIVE OWNER CONFIRMED  

## Authoritative repository

| Field | Value |
|-------|-------|
| Repository root | `C:\Users\warren\Documents\GitHub\Warrenhughes1974` |
| qla_core path | `qla_core/` (direct child of repository root) |
| Branch | `issue-34-pr7-quikisrr` |
| Commit | `0ed59cdc472c10c0189d5328883460fdc5fb0189` |

## Required modules confirmed

All five Citizens-required modules exist in this repository:

- `qla_core/rate_dbf_schema.py`
- `qla_core/rate_factor_loader.py`
- `qla_core/rate_key_setup.py`
- `qla_core/rate_member_setup.py`
- `qla_core/rate_dbf_writer.py`

## Ownership analysis

| Candidate | Role | Authoritative? |
|-----------|------|----------------|
| `Warrenhughes1974/qla_core/` | Primary engine source (~60 modules) | **Yes** |
| `Citizens_Product_Rate_Conversion/` | Client project; no qla_core copy | No |
| `QLA_Migration/` | CSO client conversion app | No (consumer) |
| `CFIC_Rates/` | Citizens legacy audit source | No |

## Existing metadata (prechange)

- No engine `pyproject.toml` at repository root (pre-Stage 4C)
- No package version in `qla_core.__init__.py`
- No repository tags for qla_core distribution
- No dedicated qla_core test suite

## Client usage

`qla_core` is shared reusable engine code consumed by:

- CSO full-system conversion (`QLA_Migration`, `app.py`, plan governance runners)
- Citizens Product and Rate Conversion (installed package boundary from Stage 4B)
- Monorepo validators and data governance tools

## Client-specific code in qla_core

Some modules contain **path resolver defaults** referencing `QLA_Migration/` or `plan_analysis/` (e.g. `plan_source_paths.py`, `lifepro_source_resolver.py`). These are runtime path helpers, not packaged client data. No Citizens plan codes, mappings, or source files are embedded in qla_core.

`CSOAssumptionProvider` in `rate_key_setup.py` is a reusable adapter class — not CSO client configuration.

## Conclusion

Packaging proceeds from `Warrenhughes1974/qla_core` only. Citizens and CSO repositories are not packaging sources.
