# Issue #119 — Implementation Notes

**Issue:** #119 — PUA coverage MPAR must be 0  
**Date:** 2026-07-27  
**Release:** **v58.43**  
**Status:** Implemented — Validation PASS

---

## Change summary

PUA rider rows now force `quikridr.MPAR = "0"` in `_apply_pua_rider_inheritance`, matching Robert’s QLAdmin rule (PA add sets participating to 0). Base coverages keep Issue #105 product-PAR authority.

---

## Code touched

| File | Change |
|------|--------|
| `app.py` / `QLA_Migration/app.py` | `MPAR="0"` at start of PUA inheritance; log `PUA_MPAR=0`; **v58.43** |
| `tools/validators/validate_issue105_mpar.py` | v1.1 → **v1.2** — PUA expect `MPAR=0` (no base inherit) |
| `tools/validators/validate_issue119_pua_mpar.py` | **New** issue validator |
| `QLA_Migration/_validate_issue119_pua_mpar.py` | Wrapper |
| `tools/validators/validate_issue_log_accountability.py` | v1.3 — `#119` spot-check; `#105` excludes PUA from base-match |
| `tools/_build_pua_omaha_briefing.py` | §10 check text aligned with §7.2 |
| `Issue_Log_Items/PUA_CSO_Conversion_Briefing.docx` | Regenerated |

---

## Output impact

| Metric | Before | After |
|--------|-------:|------:|
| PUA rows `MPAR=1` | 493 | **0** |
| PUA rows `MPAR=0` | 1 | **494** |
| Non-PUA `MPAR=1` | 2,897 | **2,897** (unchanged) |

Output `quikridr.csv` updated in-place to match emit (493 flips). Next full batch will emit the same via v58.43.

---

## Trace (after)

| MPOLICY | MPHASE | MPLAN | MPAR |
|---------|--------|-------|------|
| 9010310404C | 2 | 1960PA | **0** |
| 9010150910C | 3 | 221EPA | **0** |
| 9010360290C | 2 | 1708PA | **0** |
| 9010391228C | 2 | 1970PA | **0** |
| 9010143726C | 1 | 221END | **1** (control) |

---

## UAT reload

Partial reload: `QLA_Migration/Output/Test_Validation/quikridr.csv`
