# Issue #59 — MUWCLASS Status Mistranslation (Cash Values Blank)

**Status:** Development fix shipped **v57.83**  
**Date:** 2026-07-14

## Problem

`quikridr.MUWCLASS` was rewritten by bare `Master_Value_Translation` status rows:

| LifePRO UW | Wrong emit | Correct |
|------------|------------|---------|
| S | 55 | SM |
| P | 41 | PR |
| N | T | NS |
| T | 56 | T (pass-through) |
| Q | Q | NS (L14 rates are N→NS) |

~67% of phase-1 riders had non-rate UW codes → QuikPlCv/QuikCvs lookup failed → Cash Values **0.00**.

## Fix (surgical)

1. `app.py` / `QLA_Migration/app.py` **v57.83**: `MUWCLASS` uses `map_rider_uwclass()` — **never** bare status map.
2. `qla_core/rate_dbf_schema.py`: `RIDER_UWCLASS_MAP` + `map_rider_uwclass()`.
3. Remapped `QLA_Migration/Output/quikridr.csv` from PPBEN (backup: `QLA_Migration/Archive/quikridr_pre_issue59_v5782.csv`).

## UAT

Reload **`quikridr`** (CSV→DBF), rebuild indexes, verify:

- `011208260C` / `011208334C` → UW **SM**, cash values populate  
- `011207563C` → UW **NS**, cash values populate  

Validator: `tools/validators/validate_issue59_muwclass.py`
