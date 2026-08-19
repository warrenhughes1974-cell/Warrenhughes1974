# Issue 139 — Policy fees withheld for ISWL / UNKNOWN only

**Issue:** 139 — Remove policy fees (ISWL/UNKNOWN)  
**Framework stage:** Closure Agent  
**Final status:** **Closed**  
**Engine version:** v58.99  
**Closed date:** 2026-08-19  
**Owner:** Conversion

---

## Resolution (issue log — paste-ready)

**Resolution:** ISWL policy fees are withheld on the load (annual and modal fees set to zero, and billed premium no longer includes that fee). Traditional policies still keep their fees.

> Copy the line above into tracking sheets and client readouts. Long-form detail follows.

---

## Problem Statement

ISWL policies were loading LifePRO policy fees onto QuikRidr (typically $25 annual) and keeping that fee inside mode premium. Warren directed conversion to withhold those fees for ISWL only. The withhold ran once (v58.91), then a later `quikridr` rebuild put the fees back because root `app.py` (the file the converter actually launches) no longer called the withhold.

---

## Root Cause

**Category:** [x] Mapping error  [ ] Source extract defect  [ ] Scope gap  [ ] Client definition  [ ] QLAdmin behavior  [x] Other — converter copy drift / missing always-on smoke

`QLA_Migration/app.py` still called `suppress_policy_fees`. Root `app.py` imported it and did not call it. `run_converter.bat` launches root `app.py`. Issue 139 was never Closed and was not on `SMOKE_JOBS`, so the drop shipped.

---

## Resolution

Withhold is applied again on current Output: 2,266 ISWL fee rows zeroed; 2,249 mode premiums reduced; 2,191 traditional fee rows kept. Root `app.py` now calls the same withhold after modal fee load. Convert-time abort and release-gate smoke fail if ISWL fees come back.

### Files changed

| File | Change |
|------|--------|
| `app.py` | Restore withhold + #89 non-ISWL wipe guard + convert-time smoke; v58.99 |
| `QLA_Migration/app.py` | Convert-time smoke; v58.99 |
| `qla_core/issue139_fee_smoke.py` | Fail-closed floors + gold traces |
| `tools/validators/validate_issue139_policy_fee_suppression.py` | Fail-closed (no SKIP / no flag-off PASS) |
| `tools/validators/validate_release_closed_issues.py` | `SMOKE_JOBS` #139 |
| `QLA_Migration/Output/quikridr.csv` / `quikmstr.csv` | ISWL fees 0; traditional fees kept |

### Rulebook changes

None.

### Engine changes

- Call `suppress_policy_fees` after `#58` modal fee load on **both** `app.py` copies.
- `#89` FATAL on non-ISWL fee wipe when withhold is on (not on intentional ISWL zeros).

---

## Evidence

| Artifact | Path |
|----------|------|
| Validator | `tools/validators/validate_issue139_policy_fee_suppression.py` PASS 2026-08-19 |
| Bank Acct regression | `validate_issue75_mbankno.py` PASS |
| Non-ISWL fees | `validate_issue58_quikridr_modal_fees.py` PASS |
| Test_Validation | `quikmstr.csv` + `quikridr.csv` |

---

## Trace Policy Confirmation

| Policy | Client expected | Emitted | Match |
|--------|-----------------|---------|-------|
| 9010713704C | ISWL fees off; mode premium without fee | fees 0.0000; MMODEPREM 41.71 | Yes |
| 9010367131C | Traditional fees kept | MANNLFEE 10.4400 | Yes |

---

## Explicitly Not Changed

- [x] quikmstr.MMODPREM / modal premium totals (only ISWL MMODEPREM reduced by the withheld fee)
- [x] Issue #26 MPREM mapping on unrelated logic
- [x] Issue #25 MPOLICY padding
- [x] Issue #75 PAC Bank Acct
- [x] Traditional #21C/#58 fees

---

## Closed-issue override (#89)

#89 still restores fees on every `quikridr` emit and still blocks a **non-ISWL** fee wipe. ISWL zeros are #139 (Warren 2026-08-11; re-locked 2026-08-19 after the drop).

---

## Always-on smoke

Registered in `SMOKE_JOBS`. Convert-time abort after `quikridr` write. Disable only with `QLA_ISSUE139_FEE_SMOKE=0` (debug).
