# Issue #159 — Resolution Summary

**Issue:** #159 — L10/L14 traditional-life reserves at $0 (UW key mismatch)  
**Framework stage:** Closure Agent  
**Final status:** **Closed**  
**Engine version:** v59.08  
**Closed date:** 2026-09-02  
**Owner:** Conversion

---

## Resolution (issue log — paste-ready)

**Resolution:** Policy underwriting class is mapped with the plan again so L10 smokers use SM and L14 uses NT/PQ/ST, matching the rate files after the UW-class remap.

---

## Problem Statement

Traditional life valuation showed QLAdmin reserve at $0 on L10 LP95, L10 PRE97, and L14 while LifePRO held about $2.53M on those rows. The client said the same policies had matched after the underwriting-class remap.

---

## Root Cause

**Category:** [x] Mapping error

Issue #118 remapped UW keys on the rate files (L10 S→SM, L14 N→NT). Policy emit called `map_rider_uwclass(val)` without the plan, so a later batch put L10 smokers back on ST and every L14 rider on 00. QLAdmin could not attach the TV tables.

---

## Resolution

Both `app.py` copies pass `plan=MPLAN` into the mapper. Current `quikridr` was remapped from PPBEN letters (616 MUWCLASS rows). Rate tables, premiums, and policy numbers were not changed.

### Files changed

| File | Change |
|---|---|
| `app.py` / `QLA_Migration/app.py` | plan= + v59.08 |
| `QLA_Migration/Output/quikridr.csv` | MUWCLASS remap (gitignored) |
| `tools/validators/validate_issue159_muwclass_plan_aware.py` | fail-closed smoke |
| `tools/validators/validate_release_closed_issues.py` | SMOKE_JOBS |
| `tools/validators/validate_issue_log_accountability.py` | #159 job |

### Rulebook changes

None.

### Engine changes

One-line `map_rider_uwclass` argument; version bump.

---

## Evidence

| Artifact | Path |
|---|---|
| Validation | `Issue_159_Validation_Report.md` PASS |
| Regression | `Issue_159_Regression_Report.md` PASS |
| Validator | `python tools/validators/validate_issue159_muwclass_plan_aware.py` |
| Accountability | #159 IN_DATA via that validator |
| Test_Validation | `Output/Test_Validation/quikridr.csv` |
| Guide | `Completed_Issues_Release_Validation_Guide.md` row 159 |

---

## Trace Policy Confirmation

| Policy | Client expected | Emitted | Match |
|---|---|---|---|
| 9011190516C | SM | SM | Yes |
| 9011206462C | NT | NT | Yes |
| 9011207210C | PQ | PQ | Yes |
| 9011059291C | ST | ST | Yes |

---

## Output accountability (G7)

1. Issue validator PASS on full `QLA_Migration/Output/quikridr.csv`.
2. Accountability **IN_DATA** for `#159` (validator PASS). Other catalog GAPs (#59/#76/#114/#135) are pre-existing cut items, not this issue.
3. `Test_Validation/quikridr.csv` published.
4. Always-on smoke registered. `--smoke-only`: **#159 PASS**. Suite overall RELEASE_BLOCKED on pre-existing #59 MSTATUS (8/31 T/DC), not on this job.

---

## Explicitly Not Changed

- [x] quikmstr.MMODPREM
- [x] Issue #26 MPREM
- [x] Issue #2 / #25 MPOLICY
- [x] QuikTvs / QuikNps values
- [x] PLANVALOPT / *VARY*
- [x] #107 LP9595 source
- [x] Invented L14 PQ/ST reserve grids

---

## Residual risks / follow-ups

- CSO must reload `quikridr` and revalue before QuikValf $0 moves.
- L14 Q/T have no LifePRO RV grid (N-only).
- Some L10 rider plans (9JPO10) now have SM on the rider but not yet on QuikPlUw; next rate emit adds membership.

---

## Rollback

Restore `QLA_Migration/Archive/issue159_pre_remap/quikridr_pre_issue159.csv` and revert the `plan=` argument in both `app.py` files.

---

## Git release

Commit `03cc569` on `issue-34-pr7-quikisrr`. `Output/` is gitignored — network machines keep v59.08 and the remapped `quikridr` (or re-run a full policy batch).
