# Issue #159 — Validation Report

**Issue:** #159 — L10/L14 traditional-life reserves at $0 (UW key mismatch)  
**Framework stage:** Validation Agent  
**Engine version:** v59.08  
**Validation script:** `tools/validators/validate_issue159_muwclass_plan_aware.py`  
**Output directory:** `QLA_Migration/Output/`  
**Before snapshot:** `QLA_Migration/Archive/issue159_pre_remap/quikridr_pre_issue159.csv`  
**Generated:** 2026-09-02  
**Verdict:** **PASS**

---

## Commands Run

```text
python tools/validators/validate_issue159_muwclass_plan_aware.py
python tools/validators/validate_issue118_uwclass.py
python tools/validators/validate_issue59_muwclass.py
python tools/publish_test_validation.py quikridr --issue Issue_159
```

---

## 1. Trace Policy Results

| Policy | Phase | Field | Expected | Actual | Result |
|---|---:|---|---|---|---|
| 9011189929C | 1 | MUWCLASS | BL | BL | PASS |
| 9011190516C | 1 | MUWCLASS | SM | SM | PASS |
| 9011193156C | 1 | MUWCLASS | PR | PR | PASS |
| 9011059291C | 1 | MUWCLASS | ST | ST | PASS |
| 9011206462C | 1 | MUWCLASS | NT | NT | PASS |
| 9011208194C | 1 | MUWCLASS | ST | ST | PASS |
| 9011207210C | 1 | MUWCLASS | PQ | PQ | PASS |

---

## 2. Acceptance Criteria (from Risk checklist)

| # | Criterion | Result |
|---|---|---|
| 1 | #159 validator PASS | PASS |
| 2 | #118 UAT anchors PASS | PASS |
| 3 | #59 samples PASS (L10 SM / L14 PQ) | PASS |
| 4 | 1L1095 / 1L10OD / 1L10PR phase-1 ST = 0 | PASS |
| 5 | 1L14SC 00 = 0 | PASS |
| 6 | Non-L10 S stays ST (`5L0110`) | PASS |
| 7 | quikridr row count 6,956 | PASS |
| 8 | Non-MUWCLASS fields identical vs before | PASS (0 drift) |
| 9 | QuikTvs not edited | PASS |
| 10 | Test_Validation/quikridr.csv published | PASS |

---

## 3. Source Alignment

| Check | Result |
|---|---|
| PPBEN letter → MUWCLASS with plan= | 616 rows remapped from `PPBEN_PolicyBenefit_Extract_20260831.csv` |
| Blank / 0 → 00 | Unchanged path |
| Already-correct BL/PR | Unchanged |

---

## 4. Untouched Fields Confirmed

| Field / table | Check | Result |
|---|---|---|
| MPOLICY / MPREM / MBAND / MUNIT | byte-compare vs backup | PASS 6956/6956 |
| All non-MUWCLASS columns | drift rows | 0 |
| QuikTvs / QuikNps | not written | PASS |

---

## 5. Row Counts

| Table | Count | Before | Match? |
|---|---:|---:|---|
| quikridr | 6,956 | 6,956 | Yes |

---

## 6. Impact Summary

| Metric | Value |
|---|---|
| MUWCLASS rows changed | 616 |
| Rows unchanged | 6,340 |
| L10 ST→SM | 384 |
| L14 00→NT/PQ/PR/ST | 232 (101/111/13/7) |

#118 WARN: 95 L10 rider rows (e.g. 9JPO10) now SM and are not yet on that plan's QuikPlUw. Membership-only; those plans have no TV grid. Next rate emit `ensure_members_for_rider_uw` will add SM. Not a #159 FAIL.

---

## 7. Failures

None.

---

## 8. Recommendation

- [x] Validation **PASS** — stop for readout (Regression/Closure on request)
- [ ] QuikValf $0 will not move until CSO reloads `quikridr` and revalues

---

## Appendix

- Trace CSV: `Issue_Log_Items/Issue_159/evidence/issue159_uat_before_after.csv`
- Validator stdout: #159 / #118 / #59 all RESULT: PASS
