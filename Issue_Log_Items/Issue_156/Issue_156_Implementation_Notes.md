# Issue #156 — Implementation Notes

**Issue:** #156 — Add Source Policy Number to User Defined  
**Engine version:** v59.02  
**Date:** 2026-08-26

---

## What changed

`quikspec.SOR_POL` now carries the LifePRO `PPOLC.POLICY_NUMBER` (trimmed / uppercased only). `MPOLICY` still uses Issue #2 (`source + C`, width 11).

The Append Tool master `QUIKSPEC.DBF` field is **C(10)** (client changed it from N(10,0) so ML/D/FG keys load).

## Files

| File | Change |
|------|--------|
| `app.py` / `QLA_Migration/app.py` | v59.02; `TABLE_SCHEMAS["quikspec"]` adds `SOR_POL` |
| `validation_config/schema_manifest.json` | Same column |
| `QLA_Migration/Configs/Sync_Rulebook_quikspec.csv` | `POLICY_NUMBER → SOR_POL` + `SKIP_TRANSLATION` |
| `QLA_Migration/_apply_issue156_sor_pol.py` | One-shot fill of current Output |
| `QLA_Migration/_validate_issue156_sor_pol.py` | Fail-closed validator |

## Not changed

- `MPOLICY` formatter (`format_qladmin_mpolicy`)
- `VANISH` / `VANISHDT` / `RESSTATE` / `RESRVCAT`
- Other `quik*` tables
