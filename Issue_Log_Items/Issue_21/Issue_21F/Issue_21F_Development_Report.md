# Issue 21F — Development Report

**Issue:** Truncated Premium History — conversion premium adjustment  
**Framework stage:** Development (v57.72)  
**Date:** 2026-07-11  
**Status:** **IMPLEMENTED** — validator PASS  
**Engine:** v57.72  

---

## Summary

Implemented additive Conversion Adjustment rows on `quikprmh` for eligible non-ISWL policies. LifePRO four-component totals from PPBENTYP are reconciled against converted premium-history sums; positive gaps load a single row dated **20171231** marked **CONV_ADJ / QLA21F**.

---

## Code changes

| File | Change |
|------|--------|
| `qla_core/issue21f_premium_adjustment.py` | **New** — totals, eligibility, row build, reports, idempotency |
| `app.py` / `QLA_Migration/app.py` | Wire after quikprmh DataFrame (batch); **v57.72** |
| `tools/validators/validate_issue21f_premium_adjustment.py` | **New** — golden + ISWL + idempotency + regression |
| `Issue_21F/_rebatch_quikprmh_21f.py` | Offline rebatch helper |

---

## Marker literals

| Field | Value |
|-------|--------|
| `DATEPAID` | `20171231` |
| `MSOURCE` | `CONV_ADJ` |
| `USER_ID` | `QLA21F` |
| `MBATCH` | `21F-ADJ` |

---

## Validation results

| Check | Result |
|-------|--------|
| Golden 010310404C adjustment | **$15,193.85** @ 20171231 PASS |
| LifePRO total reconcile | $17,040.05 PASS |
| ISWL 010713704C excluded | PASS |
| Load candidates | **2,622** rows |
| Idempotency (re-run) | 0 new rows; 2,622 already_loaded |
| Existing history unchanged | PASS (vs archive snapshot) |
| Schema order | PASS |
| Test_Validation publish | `quikprmh.csv` published |

---

## Reports

- `QLA_Migration/Reports/issue21f_premium_adjustment_validation.csv`
- `QLA_Migration/Reports/issue21f_premium_adjustment_exceptions.csv`

---

## Next

Validation Agent (Cursor Grok 4.5) → Regression Agent → Closure Agent.
