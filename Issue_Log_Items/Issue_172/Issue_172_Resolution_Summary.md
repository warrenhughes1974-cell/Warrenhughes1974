# Issue 172 — Resolution Summary

**Issue:** 172 — Fleet-wide shared underwriting-class rate keys  
**Framework stage:** Closure  
**Final status:** **Closed**  
**Engine version:** v59.20  
**Closed date:** 2026-09-22  
**Owner:** Warren

---

## Resolution (issue log — paste-ready)

09/22/2026 Resolution: Preferred policies on plans that share one cash-value grid now have their own cash-value rate key, copied from Standard, so QLAdmin can find the rate. The policy underwriting class was not changed, and plans with different class rates were left alone. Examples: 9011006697C Preferred cash-value key present; 9010713704C Preferred cash-value key present; 9010718276C Standard unchanged.

---

## Problem Statement

Policy 9011006697C is plan 1659C2 and Preferred. QLAdmin looks up cash value by the policy's exact underwriting class. The cash-value table had a Standard key only, so Preferred policies could not find a rate even though LifePRO uses one shared cash-value grid for that plan.

## Root Cause

**Category:** Scope gap

LifePRO stores 659 CEN II cash values under class S only. Conversion emitted that grid as Standard only. Preferred policies had no matching key.

## Resolution

The rate emit now copies a proven shared grid onto each approved class and changes only the class label. For this close, that is 1659C2 cash value, Standard copied to Preferred: 1,082 cash-value rows and 2 plan-value keys. `UWVARYCV` stays N because the values are the same. The policy class is unchanged. Plans whose classes have different rates were not copied.

The same rows are in full `QLA_Migration/Output/rates` and in `QLA_Migration/Output/Test_Validation/rates`.

### Files changed

| File | Change |
|------|--------|
| `qla_core/issue172_shared_uw_keys.py` | Approved-manifest replication |
| `qla_core/rate_emit.py` | Hook after equal-class collapse |
| `app.py`, `QLA_Migration/app.py` | v59.20 |
| `tools/validators/validate_issue172_shared_uw_keys.py` | Fail-closed check |
| `tools/validators/validate_release_closed_issues.py` | Always-on smoke |
| `QLA_Migration/Output/rates/QuikCvs.csv` | +1,082 Preferred rows |
| `QLA_Migration/Output/rates/QuikPlCv.csv` | +2 Preferred keys |

## Evidence

| Artifact | Path |
|----------|------|
| Validation | `Issue_172_Validation_Report.md` — PASS |
| Regression | `Issue_172_Regression_Report.md` — PASS |
| Full Output validator | `python tools/validators/validate_issue172_shared_uw_keys.py` — PASS |
| Accountability | #172 registered; validator PASS on full Output = IN_DATA |

## Trace Policy Confirmation

| Policy | Expected | Emitted | Match |
|--------|----------|---------|-------|
| 9011006697C | PR, Preferred cash-value key equals Standard | PR; 1,082 matching rows | Yes |
| 9010713704C | PR | PR | Yes |
| 9010718276C | ST unchanged | ST | Yes |

## Explicitly Not Changed

- Policy underwriting class
- `UWVARYCV` (stays N)
- 1658C1 and other plans whose class rates differ
- Premium, reserve, and policy-header tables

## Fleet Impact

| Metric | Value |
|--------|------:|
| QuikCvs rows added | 1,082 |
| QuikPlCv rows added | 2 |
| Existing cash-value rows edited | 0 |

## Production Readiness

| Check | Status |
|-------|--------|
| Validator PASS on full Output | Yes |
| Test_Validation published | QuikCvs.csv, QuikPlCv.csv |
| Completed Issues guide | Row 172 added |
| Always-on smoke | `#172 shared UW-class cash-value keys` |
| Git commit / push | Not run. Close was a log update; `rate_emit.py` also contains unrelated uncommitted work, so it was not committed from this step. |

`Output/` is not in git. The next rate generation on v59.20 rebuilds these keys from the manifest. The current package hash in `QLA_Migration/Reports/rates/newest_plan_rate_package.json` includes the Preferred keys.

## Residual Risks

Sister plans that also share one cash-value grid were not added. They stay out until each plan is proven the same way.

## Rollback

Set `QLA_ISSUE172_SHARED_UW_KEYS=0` and regenerate rates, or restore the pre-close `QuikCvs.csv` and `QuikPlCv.csv` from `Issue_Log_Items/Issue_172/evidence/validation/off_rates`.
