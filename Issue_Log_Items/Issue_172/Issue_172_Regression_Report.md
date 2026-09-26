# Issue 172 — Regression Report

**Issue:** 172 — Fleet-wide shared underwriting-class rate key completion  
**Framework stage:** Regression (Stage 7 / G6)  
**Date:** 2026-09-22  
**Verdict:** **PASS**

---

## Comparison

Before state: `Issue_Log_Items/Issue_172/evidence/validation/off_rates` (copy of the package before the Preferred keys).  
After state: full `QLA_Migration/Output/rates` after publishing the approved rows.

| Table | Before | After | Removed | Changed existing rows | Added |
|-------|-------:|------:|--------:|----------------------:|-------|
| QuikCvs.csv | 40,950 | 42,032 | 0 | 0 | 1,082 `1659C2` / PR |
| QuikPlCv.csv | 260 | 262 | 0 | 0 | 2 `1659C2` / PR |
| quikridr.csv | not rewritten | unchanged | — | — | — |
| quikplan.csv | not rewritten | unchanged | — | — | — |
| quikmstr.csv | not rewritten | unchanged | — | — | — |

`UWVARYCV` for `1659C2` remains `N`. `1658C1` Preferred and Standard cash values remain different (738 of 1,032 shared keys differ).

## Prior fixes

| Check | Result |
|-------|--------|
| #136 Plan Values Options | PASS on full Output |
| #159 plan-aware MUWCLASS | PASS on full Output |
| #168 L14 four-class equality | PASS on full Output |
| #172 shared cash-value keys | PASS on full Output |
| #25 / #26 policy tables | Not rewritten by this publish |

## Fleet impact

Only `1659C2` cash-value factor and key rows were added. No existing cash-value value was edited. Policy underwriting class was not remapped.
