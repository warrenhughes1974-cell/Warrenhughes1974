# Issue #143 — Resolution Summary

**Issue:** #143 — Units Incorrect (RPU)  
**Framework stage:** Closure Agent (G7)  
**Final status:** **Closed**  
**Engine version:** **v58.96**  
**Closed date:** 2026-08-18  
**Owner:** Conversion · **Reporter:** Eric  
**Validation:** **PASS**  
**Regression:** **PASS**  
**Smoke:** **PASS 9/9**  
**Authorized #124 reseed:** **COMPLETE**  
**Accountability:** **IN_DATA** (issue validator PASS on full `QLA_Migration/Output/`)

---

## Resolution (issue log — paste-ready)

**Resolution:** Issue #143 is Closed in v58.96. The 23 SME-authorized BF Reduced Paid-Up policies now derive MUNIT from BF_CURRENT_DB / VALUE_PER_UNIT so QLAdmin Amount Ins reproduces the LifePRO paid-up death benefit. Validation, Regression, and final Smoke testing passed. The existing Issue #124 QuikIswl emit was subsequently executed, and all 23 affected ISWL records now store MDB = corrected MUNIT × 1000. Gold policy 9010757606C now contains MUNIT 19.10196 and MDB 19101.96. No unauthorized or unexplained differences remain.

> Copy the line above into tracking sheets and client readouts. Long-form detail follows.

---

## Problem Statement

Some Reduced Paid-Up policies still showed original-issue units in LifePRO while Column DD held the paid-up death benefit. QLAdmin copied those units, so Amount Ins was overstated.

---

## Root Cause

**Category:** [x] Mapping error  [x] Source extract defect  [ ] Scope gap  [ ] Client definition  [ ] QLAdmin behavior

`NUMBER_OF_UNITS` is not always reduced on RPU. The converter mapped it straight to `MUNIT`. On 23 BF rows, `BF_CURRENT_DB` is the authority for death benefit.

---

## Resolution (detail)

Post-map override: if RU + BF + DD>0 and units differ from DD/VPU by more than 0.01, set `MUNIT = BF_CURRENT_DB / VALUE_PER_UNIT`, then existing #55 emit. Engine **v58.96**.

### Files changed

| File | Change |
|------|--------|
| `qla_core/issue143_rpu_munit.py` | Locked rule |
| `app.py` / `QLA_Migration/app.py` | v58.96 hook before #55 |
| `tools/validators/validate_issue143_rpu_munit.py` | Issue validator |

### Rulebook changes

None (`NUMBER_OF_UNITS → MUNIT` default kept).

---

## Evidence

| Artifact | Path |
|----------|------|
| Closure summary | `Issue_143_Closure_Summary.md` |
| Validation | PASS — `Issue_143_Validation_Report.md` |
| Regression | PASS — `Issue_143_Regression_Report.md` |
| Validator | `python tools/validators/validate_issue143_rpu_munit.py` → PASS |
| Dedicated smoke | `python tools/validators/validate_issue143_smoke.py` → **PASS 9/9** |
| Release smoke | `python tools/validators/validate_release_closed_issues.py --smoke-only` → **RELEASE_OK** (captured 2026-08-18T08:48:36) |
| Accountability | **IN_DATA** (validator PASS on full Output) |
| Test_Validation | `QLA_Migration/Output/Test_Validation/quikridr.csv` |
| Status | `Issue_143_Status.md` |
| Completed Issues guide | Row 143 (reseed COMPLETE) |

---

## Trace Policy Confirmation

| Policy | Client expected | Emitted | Match |
|--------|-----------------|---------|-------|
| 9010757606C | 19.10196 / $19,101.96 | 19.10196 / 19101.96 | Yes |
| 9010766847C | 5.16341 | 5.16341 | Yes |
| 9010826422C | 9.65590 | 9.65590 | Yes |

---

## Explicitly Not Changed

- `MPREM`, `MVPU`, `MSAVEUNIT` (#108A blank on RPU)
- MPOLICY (#2 extra-C behavior)
- #55 floor
- #124 formula `MDB = MUNIT × 1000` (reseed COMPLETE; formula unchanged)

---

## Residual / operational

Authorized #124 reseed is **COMPLETE**. Gold `9010757606C` now stores MUNIT 19.10196 and MDB 19101.96. Outstanding #143 downstream dependencies: **0**.

---

## Rollback

Restore `evidence/quikridr_pre_issue143_20260818T130527Z.csv`; remove the v58.96 #143 hook.
