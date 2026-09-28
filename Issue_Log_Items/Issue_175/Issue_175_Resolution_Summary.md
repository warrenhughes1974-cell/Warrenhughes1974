# Issue 175 — Resolution Summary

**Issue:** 175 — Res Cat Unique Field
**Framework stage:** Closure
**Final status:** **Closed**
**Engine version:** v59.26. `app.py` was not changed. The filler is in `qla_core`.
**Closed date:** 2026-09-28
**Owner:** Eric / Warren

---

## Resolution (issue log — paste-ready)

09/28/2026 Resolution: Policies on graded death and single premium L17 now show reserve category 13, 13, and 12 on the policy, instead of the letter L. Examples: 9011210337C reserve category 13; 9011216680C reserve category 13; 9011217014C reserve category 12.

---

## Problem Statement

Policies on products 1L15GD, 1L16GD, and 1L17SP showed the letter L as the reserve category. Eric said those categories should be 13, 13, and 12. The plan product code was already those numbers. The policy spec field was the letter from LifePRO.

## Root Cause

**Category:** Mapping error

Issue 141 copies LifePRO product type onto `quikspec.RESRVCAT`. L15, L16, and L17 BASE are stored as product type L. Warren approved an exception for those three coverages on 2026-09-28.

## Resolution

Those three coverages now load as 13, 13, and 12. Other product types, including other coverages stored as L, stay as they are. The plan file was not changed. Thirty-three policy rows were corrected in the current package. Vanish, resident state, and source policy number on those rows did not change.

### Files changed

| File | Change |
|------|--------|
| `qla_core/quikspec_resrvcat.py` | L15 and L16 emit 13. L17 BASE emits 12. |
| `QLA_Migration/_validate_issue141_resrvcat.py` | Accepts that exception. |
| `tools/validators/validate_issue175_resrvcat.py` | Fail-closed check. |
| `tools/validators/validate_release_closed_issues.py` | Always-on smoke. |
| `tools/validators/validate_issue_log_accountability.py` | #175 required job. |
| `QLA_Migration/Output/quikspec.csv` | 33 cells. Not in git. |
| `QLA_Migration/Output/Test_Validation/quikspec.csv` | Partial reload copy. |

## Evidence

| Artifact | Path |
|----------|------|
| Validation | `Issue_175_Validation_Report.md` — PASS |
| Regression | `Issue_175_Regression_Report.md` — PASS |
| Full Output validator | `python tools/validators/validate_issue175_resrvcat.py` — PASS |
| Accountability | #175 registered. Validator PASS on full Output = IN_DATA. |
| Smoke | `#175 L15/L16/L17 reserve category` PASS inside `--smoke-only` on 2026-09-28. Issue 141 also PASS. The full suite is still blocked by #59, #160, and #167, which read the 8/31 valuation or a missing archive. This change did not touch those fields. |

## Trace Policy Confirmation

| Policy | Expected | Emitted | Match |
|--------|----------|---------|-------|
| 9011210337C | 13, vanish F, Kentucky | 13, F, KY | Yes |
| 9011216680C | 13, vanish F, Indiana | 13, F, IN | Yes |
| 9011217014C | 12, vanish F, Louisiana | 12, F, LA | Yes |

## Explicitly Not Changed

- Plan product codes
- ISWL plan tags
- Other reserve categories
- Vanish, resident state, and source policy number
- Premium and policy number width

## Fleet Impact

| Metric | Value |
|--------|------:|
| Spec rows changed | 33 |
| Reserve category L remaining | 0 |
| Other columns changed | 0 |
| Other tables rewritten | 0 |

## Production Readiness

| Check | Status |
|-------|--------|
| Validator PASS on full Output | Yes |
| Test_Validation published | `quikspec.csv` |
| Completed Issues guide | Row 175 added. Row 141 notes the exception. |
| Always-on smoke | `#175 L15/L16/L17 reserve category` |
| Git | Close commit on the current branch. Push was not requested. |

`Output/` is not in git. The 33-cell correction is already in the local package. A later batch on this filler keeps the same three-coverage map.

## Residual Risks

The vanish and resident-state checks still fail when they read the 8/31 extract against this 6/30 package. Those six policies were not part of this change.

## Rollback

Remove the three-coverage map from `reserve_category()` and set the 33 reserve categories back to L.
