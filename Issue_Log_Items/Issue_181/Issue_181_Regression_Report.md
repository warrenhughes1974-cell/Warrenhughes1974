# Issue 181 — Regression Report

**Issue:** 181 — 658/659 QuikTvs Duration Shift
**Framework stage:** Regression
**Engine version:** v59.28
**Baseline:** `QLA_Migration/Archive/issue181_pre_shift/QuikTvs.csv` (taken immediately before the shift on 2026-09-30)
**Output directory:** `QLA_Migration/Output/`
**Generated:** 2026-09-30
**Verdict:** **PASS**

Warren confirmed Robert's Store Means change is in. The hold is lifted. This regression covers the rate-table shift only.

## 1. Scope of Change

| Component | Expected impact |
|---|---|
| QuikTvs for 1658C1, 1658CS, 1659C2, 1659CR, 1659CS, 1659SR | Factors one year earlier. Same row count. |
| QuikTvs for every other plan | Byte-identical |
| QuikNps, QuikCvs, QuikDvs, QuikPlTv, policy tables | Not written |

## 2. Row Count Comparison

| Table | Before | After | Delta | OK? |
|---|---:|---:|---:|---|
| QuikTvs lines (including header) | 104,329 | 104,329 | 0 | Yes |
| QuikTvs rows on the six plans | 7,644 | 7,644 | 0 | Yes |
| quikmstr, quikridr, quikplan, quikprmh, quikclid, quikclnt | Not opened by this fix | Same files | 0 | Yes |

Of the 7,644 in-scope lines, 7,520 changed text and 124 were already equal to the shifted values. Every line outside the six plans matches the archive byte for byte. The header is unchanged.

## 3. Non-Target Field Diff

| Table | Column | Rows changed | OK? |
|---|---|---:|---|
| QuikTvs | PLAN, AGE, CNTL, GENDER, UWCLASS, BAND, ISSCNTRY, ISSUEST, EFFDATE | 0 | Yes |
| QuikTvs | TV cells outside the six plans | 0 | Yes |
| QuikPlTv | STOREMEANS | 0 (still N on the six plans) | Yes |

## 4. Prior Issue Fix Regression

| Issue | Check | Result |
|---|---|---|
| 106 | `validate_issue106_quiktvs_duration.py` | PASS. 170858, 17085M, 170588, 221END, and 1960OL still match. 1659C2 is exempt under Warren's 2026-09-30 approval and is checked by Issue 181. |
| 168 | L14 class replication | PASS |
| 169-TV | 667 ART terminal reserves | PASS |
| 172 | 1659C2 Preferred cash-value key | PASS. Cash values were not shifted. |
| 176 | 9010715467C Preferred cash value 761.00 / 774.00 | PASS |
| CEN NP | 1658C1 and 1659CR net premium still the issue-year rate | PASS |
| PLAN-KEEP | Manifest matches the current package date 20260831 | PASS (same-or-newer cut, hash check not required) |
| 25 / 2 | Sample `quikmstr` MPOLICY `9010158001C` is 11 characters and ends in C | Preserved. This issue did not write quikmstr. |
| 26 | `validate_issue26_mprem.py` | Not run to a result. It still looks for the May 30 extracts, which are not in Source. quikridr was not written. |

## 5. Schema Integrity

| Check | Result |
|---|---|
| QuikTvs field order | Unchanged |
| Number format | Existing text kept (`764.00`, `.00`) |
| Blank MRIDRID | Not applicable. No policy table written. |
| Row count | Unchanged |

## 6. Verdict

**PASS.** Ready to close. The shifted table is in full Output and in `Output/Test_Validation/rates/QuikTvs.csv`.
