# Issue 155 — Regression Report

**Issue:** 155 — Val File Value Per Unit Wrong (ISWL)  
**Framework stage:** Regression Agent  
**Engine version:** v59.24 (app.py unchanged by the history rebuild)  
**Baseline:** `QLA_Migration/Archive/issue155_history_rebuild_20260924_130000`  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-09-24  
**Verdict:** PASS

## 1. Scope of Change (expected)

| Component | Expected impact |
|---|---|
| QuikIswl | Rebuilt from LifePRO monthly history. Month-0 rows removed. 545,150 rows. |
| quikprmh, QuikIsrr | MISWL stamp only. Row counts unchanged. |
| quikmstr, quikridr, quikplan, rates | Not rebuilt. |

## 2. Row Count Comparison

| Table | Before (archive or untouched) | After | Delta | OK? |
|---|---:|---:|---:|---|
| QuikIswl.csv | 617,829 bytes (conversion-date seed) | 79,338,283 bytes, 545,150 rows | Intentional | Yes |
| quikprmh.csv | 20,181,820 bytes | 20,181,820 bytes | 0 | Yes |
| QuikIsrr.csv | 3,568 bytes | 3,568 bytes | 0 | Yes |
| quikmstr, quikridr, quikplan, quikclid, quikclnt | Not in the history-rebuild archive | Unchanged by this rebuild | 0 | Yes |

## 3. Non-target fields

QuikIswl schema is the existing 26 fields in the same order. No new columns. MISWL was already on quikprmh and QuikIsrr before this rebuild. Plan and rate files were not rewritten.

## 4. Prior-fix checks

`python tools/validators/validate_release_closed_issues.py --smoke-only` with `QLA_VALUATION_DATE=20260630` after the history rebuild:

- PASS: #155, #124, #21F, #133, #143, #145B, #146, #151, #152, #172, newest plan/rates kept, and the rest of the smoke list.
- FAIL: #160 only, missing `QLA_Migration/Archive/issue160_pre_remap/quikridr_pre_issue160.csv`. Pre-existing since 2026-09-13. Live #160 checks are not what failed. Warren already accepted this as the only smoke failure.

Issue #124 now asserts the month-0 row is gone. That is the Warren 2026-09-24 override of the Closed month-0 seed. The validator passed.

## 5. Fleet impact

2,244 ISWL policies received monthly history. Non-ISWL policies were not given QuikIswl rows. 24 ISWL policies with no LifePRO fund summary still have no rows.

## Gate G6

Row counts stable except the intentional QuikIswl rebuild. Unrelated tables unchanged. Overlapping Closed smokes passed except the known #160 archive gap. Verdict PASS. Status moves to Ready for Client UAT.

Closure is not started. 9010801730C is still an active policy with no history row, and the Completed Issues guide row, Test_Validation copy, and accountability check are still owed before Closed.
