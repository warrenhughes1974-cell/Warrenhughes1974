# Issue 145 — Implementation Notes

**Issue:** #145 — Vanish Flag (VB)  
**Engine:** v59.00  
**Date:** 2026-08-19  

Surgical post-emit on `quikspec` after #141 RESRVCAT. `PPOLC.BILLING_REASON = VB` → `VANISH=T`; else `F`. `VANISHDT` / `RESSTATE` / `RESRVCAT` not rewritten.

Also restored the general `to_csv` after the quikspec block on **root** `app.py` (it had been indented inside the quikspec `if`, so other tables would not write on EXECUTE FULL BATCH).

## Files

| File | Change |
|------|--------|
| `qla_core/quikspec_vanish.py` | New enricher |
| `app.py` / `QLA_Migration/app.py` | Hook + v59.00 |
| `QLA_Migration/Configs/Sync_Rulebook_quikspec.csv` | VANISH note |
| `QLA_Migration/_validate_issue145_vanish.py` | Fail-closed validator |

## Output apply (this session)

`apply_quikspec_vanish` on current `QLA_Migration/Output/quikspec.csv`: 636 T / 4,447 F / 0 missing.

## Traces

| Policy | VANISH |
|--------|--------|
| 9010815236C | T |
| 9011050114C | T |
| 9011069610C | T |
| 9010761639C | F |
| 9010760840C | F |

Do not register `SMOKE_JOBS` until Closure.
