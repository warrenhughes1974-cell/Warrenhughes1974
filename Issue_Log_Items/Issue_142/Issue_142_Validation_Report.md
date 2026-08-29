# Issue 142 — Validation Report

**Issue:** 142 — SL Policies (Active SL rider as 9SUBLF)  
**Framework stage:** Validation Agent  
**Engine version:** v59.04  
**Validation script:** `tools/validators/validate_issue142_sl_rider.py` v1.0  
**Output directory:** `QLA_Migration/Output/`  
**Source package:** `PPBEN_PolicyBenefit_Extract_20260630.csv` (`QLA_VALUATION_DATE=20260630`)  
**Before snapshot:** N/A (surgical apply on current Output)  
**Generated:** 2026-08-29  
**Verdict:** **PASS**

---

## Commands Run

```bash
python Issue_Log_Items/Issue_142/tools/apply_issue142_9sublf.py
python tools/validators/validate_issue142_sl_rider.py --publish-test-validation
```

Apply: quikplan 141 → 142; 22 Active SL rows from 06/30 PPBEN; 22 9SUBLF quikridr rows written (total 6956).  
Validator: exit 0.

---

## 1. Trace Policy Results

| Policy | Phase | Field | Expected | Actual | Result |
|--------|------:|-------|----------|--------|--------|
| 9010886099C | 2 | MPLAN / MUNIT / MVPU / MPREM | 9SUBLF / 100 / 0 / 26.34 | 9SUBLF / 100 / 0 / 26.34 | PASS |
| 9010469666C | 2 | MPLAN / MUNIT / MVPU / MPREM | 9SUBLF / 10 / 0 / 2.50 | 9SUBLF / 10 / 0 / 2.50 | PASS |
| 9011201237C | 2 | MPLAN / MUNIT / MVPU / MPREM | 9SUBLF / 25 / 0 / 11.935 | 9SUBLF / 25 / 0 / 11.935 | PASS |
| 9010497264C | 4 | MUNIT / MPREM | 5 / 5.03 | 5 / 5.03 | PASS |
| 9010987095C | 3 | MUNIT / MPREM | 25 / 0.1952 | 25 / 0.1952 | PASS |
| 9011185537C | 2 | MUNIT / MPREM | 25 / 4.96 | 25 / 4.96 | PASS |
| 9011193243C | 2 | MUNIT / MPREM | 5 / 22.22 | 5 / 22.22 | PASS |
| 9011203457C | 2 | MUNIT / MPREM | 15 / 3.28 | 15 / 3.28 | PASS |
| 9010782078C | 2 | MPREM | 0 | 0 | PASS |

All 22 Active SL policies have a 9SUBLF phase. All 22 9SUBLF rows have MVPU=0.

---

## 2. Acceptance Criteria (from Risk checklist)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | 22 Active SL rows emit as 9SUBLF | PASS |
| 2 | Every 9SUBLF MVPU=0 (no insured-amount duplication) | PASS |
| 3 | 8 red-font premiums match source ANN_PREM_PER_UNIT | PASS |
| 4 | 9010782078C outlier MPREM=0 | PASS |
| 5 | quikplan one 9SUBLF row, PAR=0 | PASS |
| 6 | Non-active SL remain suppressed (engine path; apply did not emit them) | PASS |

---

## 3. Source Alignment

| Check | Result |
|-------|--------|
| Populated source → emitted target | 8 red rows: units + APU from PPBEN |
| Fallback rows (blank/zero) | 14 zero-APU + outlier emit MPREM=0 |
| Orphan policies skipped | None of the 22 lacked a base quikridr row |

---

## 4. Untouched Fields Confirmed

| Field / table | Check | Result |
|---------------|-------|--------|
| quikmstr | not written by apply | PASS |
| Existing quikridr non-9SUBLF rows | apply replaces only 9SUBLF; prior phases kept | PASS |
| MPOLICY width (#2) | source + C, width 11 | PASS |
| MPREM (#26) on non-scope rows | unchanged | PASS |

---

## 5. Row Counts

| Table | Count | Before | Match? |
|-------|------:|-------:|--------|
| quikplan | 142 | 141 | +1 9SUBLF |
| quikridr | 6956 | 6934 | +22 |
| quikmstr | unchanged | — | yes |

---

## 6. Impact Summary

| Metric | Value |
|--------|------:|
| Target field rows changed | 22 new quikridr + 1 quikplan |
| Rows unchanged | all other Output tables / existing rider phases |

---

## 7. Failures

None.

---

## 8. Test_Validation publish

Copied `quikplan.csv` and `quikridr.csv` to `QLA_Migration/Output/Test_Validation/`.

---

## Gate (G5)

- [x] Trace policies pass
- [x] Validator exit 0
- [x] Untouched tables/fields confirmed for issue scope
- [x] Validation report published
- Status: **Ready for Regression**

Smoke registration in `SMOKE_JOBS` is deferred to Closure (Framework rule 14). The fail-closed script is already at `tools/validators/validate_issue142_sl_rider.py`.
