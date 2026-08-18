# Issue #143 — Implementation Notes

**Issue:** #143 — Units Incorrect (RPU)  
**Engine:** v58.96  
**Date:** 2026-08-18  
**Stage:** Development  

## Change

After the normal `NUMBER_OF_UNITS → MUNIT` map, remap phase-1 `MUNIT` when:

```text
PAID_UP_TYPE = RU
AND TYPE_CODE = BF
AND BF_CURRENT_DB > 0
AND abs(NUMBER_OF_UNITS - BF_CURRENT_DB / VALUE_PER_UNIT) > 0.01
THEN MUNIT = BF_CURRENT_DB / VALUE_PER_UNIT
```

Issue #55 decimal emit still runs after the override. `MPREM`, `MVPU`, `MSAVEUNIT` (#108A), MPOLICY, and Issue #124 `MDB = MUNIT × 1000` are unchanged.

## Files

| File | Change |
|------|--------|
| `qla_core/issue143_rpu_munit.py` | Locked rule + PPBENTYP/PPOLC cache loaders |
| `app.py` / `QLA_Migration/app.py` | v58.96 post-map hook before #55 emit |
| `Issue_143/tools/apply_issue143_output_remap.py` | Surgical Output apply for the 23 |
| `tools/validators/validate_issue143_rpu_munit.py` | A–G evidence |
| `QLA_Migration/_validate_issue143_rpu_munit.py` | Thin wrapper |

## Population (20260630)

| Cohort | Count | Action |
|---|---:|---|
| BF RPU mismatch | 23 | Remap `MUNIT` |
| BF RPU already aligned | 82 | Unchanged |
| Traditional BA RPU | 199 | Unchanged |

Gold `9010757606C`: `25.00000` → `19.10196` (Amount Ins $19,101.96).

## Output apply (2026-08-18)

`python Issue_Log_Items/Issue_143/tools/apply_issue143_output_remap.py`

- Backup vs current `quikridr.csv`: **23 rows**, **MUNIT only**.
- Published `Output/Test_Validation/quikridr.csv`.
- QuikIswl not rewritten. All 23 are ISWL (`1658C1` / `1659C2` / `1659CR`); next #124 seed will lower `MDB = MUNIT × 1000`.

Validator: `python tools/validators/validate_issue143_rpu_munit.py` → **PASS**.
