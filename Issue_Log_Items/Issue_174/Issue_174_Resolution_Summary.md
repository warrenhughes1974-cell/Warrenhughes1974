# Issue 174 — Resolution Summary

**Issue:** 174 — Pending Death Benefit Policies
**Framework stage:** Closure
**Final status:** **Closed**
**Engine version:** v59.26
**Closed date:** 2026-09-28
**Owner:** Eric / Warren

---

## Resolution (issue log — paste-ready)

09/28/2026 Resolution: Policies in pending death now keep the policy at Death Claim Pending and the coverage Active, so the beneficiary can be edited. Examples: 9011085655C policy 50 and phase 22; 9010521213C policy 50 and both phases 22; 9010772919C policy 50 and phase 22.

---

## Problem Statement

On policy 9011085655C the policy and the coverage phase were both status 50. QLAdmin then blocked beneficiary edits with a message that the policy status was not in sync with the coverage status. Brianna showed that a pending death claim should leave the phase Active (22). Return of premium is calculated in QLAdmin once the phase is Active. It is not a loaded amount.

## Root Cause

**Category:** Mapping error

After the policy was set to Death Claim Pending (50), the phase-1 rule copied that status onto the coverage. LifePRO still had the benefit Active. A paid-up addition on the same policy was also being moved off Active by the paid-up and terminal-status rules.

## Resolution

Death Claim Pending stays on the policy. The coverage phase, including a paid-up addition, stays Active. Surrendered, terminated death, matured, extended term, and reduced paid-up still copy onto the phase as before. Warren approved this exception to the closed paid-up and terminal-status rules on 2026-09-28.

The 6/30 package was corrected in place: 17 coverage rows, status and save status only. The policy file was not rewritten. Sixteen policies stay at 50 with every phase at 22.

### Files changed

| File | Change |
|------|--------|
| `app.py`, `QLA_Migration/app.py` | v59.26. Do not copy status 50 onto the phase. Paid-up addition stays Active when the policy is 50. |
| `qla_core/quikmstr_active_phase_status.py` | Same block list, so the policy header stays 50. |
| `tools/validators/validate_issue174_pending_death_phase.py` | Fail-closed check against the current cut. |
| `tools/validators/validate_issue160_pua_terminal_status.py` | Status 50 is the exception. |
| `tools/validators/validate_release_closed_issues.py` | Always-on smoke. |
| `tools/validators/validate_issue_log_accountability.py` | #174 required job. |
| `QLA_Migration/Output/quikridr.csv` | 17 rows, not in git. |
| `QLA_Migration/Output/Test_Validation/quikridr.csv` | Partial reload copy. |

## Evidence

| Artifact | Path |
|----------|------|
| Validation | `Issue_174_Validation_Report.md` — PASS |
| Regression | `Issue_174_Regression_Report.md` — PASS |
| Full Output validator | `python tools/validators/validate_issue174_pending_death_phase.py` — PASS |
| Accountability | #174 registered. Validator PASS on full Output = IN_DATA. |
| Smoke | `#174 pending death keeps coverage Active` PASS inside `--smoke-only` on 2026-09-28. The full suite is still blocked by #59, #160, and #167. Those three read the 8/31 valuation or a missing archive against this 6/30 package. This change did not touch those fields. |

## Trace Policy Confirmation

| Policy | Expected | Emitted | Match |
|--------|----------|---------|-------|
| 9011085655C | Policy 50, phase 22, premium 52.656708 | Policy 50, phase 22, premium 52.656708 | Yes |
| 9010521213C | Policy 50, base and paid-up addition 22 | Policy 50, both phases 22 | Yes |
| 9010772919C | Policy 50, phase 22 | Policy 50, phase 22 | Yes |

## Explicitly Not Changed

- Policy status on `quikmstr`
- Premium, units, plan, and policy number
- Any status other than 50
- Plan and rate tables

## Fleet Impact

| Metric | Value |
|--------|------:|
| Coverage rows changed | 17 |
| Policies at status 50 | 16 |
| Other columns changed | 0 |
| Other tables rewritten | 0 |

## Production Readiness

| Check | Status |
|-------|--------|
| Validator PASS on full Output | Yes |
| Test_Validation published | `quikridr.csv` |
| Completed Issues guide | Row 174 added. Rows 160 and 133-PS updated. |
| Always-on smoke | `#174 pending death keeps coverage Active` |
| Git | Close commit on the current branch. Push was not requested. |

`Output/` is not in git. The 17-row correction is already in the local 6/30 package. A later batch on this engine keeps the same rule. An 8/31 batch must not freeze a policy at phase 22 after LifePRO has moved it to a real death.

## Residual Risks

Return of premium still has to be confirmed in QLAdmin after the phase is Active. Issue 59's validator reads the 8/31 extract against this 6/30 package and expects `9010521213C` to be 53. That mismatch predates this close. Do not change that policy on the 6/30 package.

## Rollback

Restore the phase-1 copy list and the paid-up addition branch in both `app.py` files, and put status 50 back on the 17 coverage rows.
