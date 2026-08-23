# Issue #145B — Resolution Summary

**Issue:** 145B — Vanish 0561s Out of ISRR  
**Framework stage:** Closure Agent  
**Final status:** **Closed**  
**Engine version:** v59.01  
**Closed date:** 2026-08-23  
**Owner:** Conversion

---

## Resolution (issue log — paste-ready)

**Resolution:** Vanish-policy 0561 history is no longer loaded as a surrender, so anniversary does not cut those units. Non-vanish leftovers stay.

> Copy the line above into tracking sheets and client readouts. Long-form detail follows.

---

## Problem Statement

QLAdmin anniversary treated LifePRO 0561 history on vanishing policies as cash surrenders and reduced units. LifePRO never reduced those units — the 0561s are vanish premium taken from the policy.

---

## Root Cause

**Category:** [x] Mapping error  [ ] Source extract defect  [ ] Scope gap  [ ] Client definition  [x] QLAdmin behavior

Issue #34 correctly sends ISWL 0561s to QuikIsrr. On vanish (VB) policies those 0561s are not surrenders. #145 set the vanish flag only and left the history in place.

---

## Resolution

VB 0561 events are excluded from the #34 emit using `PPOLC.BILLING_REASON = VB`. Current Output was stripped the same way on QuikIsrr and the matching PS- / phase-0 / type-8 companions. LifePRO PACTG was not deleted. Non-VB leftovers (#146) remain.

### Files changed

| File | Change |
|------|--------|
| `qla_core/issue145b_vb_isrr.py` | PPOLC VB join |
| `qla_core/quikisrr_loader.py` | Drop VB events |
| `Issue_34/tools/quikisrr_pr7_emit.py` | Fail on VB leak; no stale 3657 floor |
| `tools/validators/validate_issue145b_vb_isrr_exclude.py` | Fail-closed |
| `app.py` / `QLA_Migration/app.py` | v59.01 |

### Rulebook changes

None.

---

## Evidence

| Artifact | Path |
|----------|------|
| Validation | `Issue_145B_Validation_Report.md` PASS |
| Regression | `Issue_145B_Regression_Report.md` PASS |
| Validator | `python tools/validators/validate_issue145b_vb_isrr_exclude.py` PASS on full Output |
| Accountability | `#145B` **IN_DATA** (validator PASS). Fleet run also had pre-existing GAP on #72 / #114 — not this issue. |
| Test_Validation | quikisrr / quikclms / quikclmp / quikbenh |
| Smoke | `SMOKE_JOBS` #145B; `--smoke-only` includes this job |

---

## Trace Policy Confirmation

| Policy | Client expected | Emitted | Match |
|--------|-----------------|---------|-------|
| 9010815236C | 0 QuikIsrr; units 25 | 0 / 25 | Yes |
| 9011050114C | 0 QuikIsrr; units 25 | 0 / 25 | Yes |
| 9011069610C | 0 QuikIsrr; units 50 | 0 / 50 | Yes |
| 9010761639C | keep $271 | 1 / $271 | Yes |
| 9010760840C | keep $716.40 | 2 / $716.40 | Yes |

---

## Explicitly Not Changed

- [x] quikmstr.MMODPREM
- [x] Issue #26 MPREM
- [x] Issue #25 / #2 MPOLICY padding
- [x] quikridr.MUNIT
- [x] quikspec.VANISH (#145)
- [x] PACTG source
- [x] quikbenh loan types 10/11/12 (#54)

---

## Residual / follow-up

After they load this cut, run anniversary and confirm the three vanish golds stay at 25 / 25 / 50. #146 leftovers are still open.

---

## Rollback

Remove the VB filter in `quikisrr_loader.py` and restore the four Output tables from a pre-apply copy / re-run #34 emit on a clean claims book.
