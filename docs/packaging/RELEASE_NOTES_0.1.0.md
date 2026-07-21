# Release Notes — qla-enterprise-conversion-engine 0.1.0

**Release date:** 2026-07-12  
**Type:** Packaging-only initial distribution  

## Summary

`qla_core` is now available as an installable Python package for client projects including Citizens Product and Rate Conversion.

| Field | Value |
|-------|-------|
| Distribution name | `qla-enterprise-conversion-engine` |
| Import name | `qla_core` |
| Version | `0.1.0` |
| API compatibility version | `1` |

## Required public modules

- `qla_core.rate_dbf_schema`
- `qla_core.rate_factor_loader`
- `qla_core.rate_key_setup`
- `qla_core.rate_member_setup`
- `qla_core.rate_dbf_writer`

## What changed

- Package metadata, build configuration, version interface, packaging tests, documentation

## What did not change

- Conversion logic
- Rate calculations
- Output schemas
- Missing-value behavior
- Client configurations

## Installation

```bash
pip install qla_enterprise_conversion_engine-0.1.0-py3-none-any.whl
```

Record wheel SHA-256 from `reports/packaging/ENG-PKG-001_Release_Manifest.json`.

## Known gaps

- License metadata marked proprietary/unresolved — release review required
- Internal artifact repository not yet configured — controlled wheel + SHA-256 acceptable for Citizens Stage 4D
