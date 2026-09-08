# Issue #160 — Resolution Summary

**Issue:** #160 — PUA phase stays Expired (56) instead of following base terminal status
**Framework stage:** Closure Agent
**Final status:** **Closed**
**Engine version:** v59.09
**Closed date:** 2026-09-08
**Owner:** Conversion

---

## Resolution (issue log — paste-ready)

**Resolution:** On policies with Paid Up Additions, the PUA phase now follows the base coverage's terminal status (Surrendered, Terminated/Death, Matured, Suspended) instead of keeping its own status, which often showed Expired.

---

## Problem Statement

Brianna reported that on surrendered policies with Paid Up Additions, QLAdmin showed the PUA phase as Expired (56) instead of Surrendered (55) like the base coverage. Investigation found the same defect on every other terminal base status the PUA inheritance rule didn't already cover — Terminated/Death (53), Matured (57), and Suspended (50) — so the fix was generalized to all of them at Warren's direction.

---

## Root Cause

**Category:** [x] Mapping/scope gap (intentional, previously unaddressed)

`_apply_pua_rider_inheritance` (Issue #60) only overrode a PUA rider's status when the base was active (`< 50` → forced to 41) or ETI/RPU (44/45 → forced to 54, Issue #108D). Every other terminal base status fell through with no override, so the PUA phase kept its own PPBEN-mapped status — frequently 56 (Expired) or, in one case, 22 (Active). This was a locked, intentional gap (**SD-60-12**, Issue #60 Risk stage), not an accidental regression.

---

## Resolution

Warren approved carving out an exception to SD-60-12 (recorded as **SD-60-13**) and approved generalizing the fix to all terminal base statuses, not just Surrendered. `_apply_pua_rider_inheritance` now has a third branch: when the base phase's status is any terminal code ≥50 other than 44/45, the PUA phase's `MPHSTAT` is forced to match the base phase's own status exactly. Current Output was remapped (239 PUA rows). Rate tables, premiums, dates, age, `MPAR`, and non-PUA riders were not changed.

### Files changed

| File | Change |
|---|---|
| `app.py` / `QLA_Migration/app.py` | new `else` branch in `_apply_pua_rider_inheritance` + v59.09 |
| `QLA_Migration/Output/quikridr.csv` | PUA `MPHSTAT` remap (239 rows, gitignored) |
| `tools/validators/validate_issue160_pua_terminal_status.py` | new fail-closed validator |
| `tools/validators/validate_release_closed_issues.py` | `SMOKE_JOBS` — registered #160 |
| `tools/validators/validate_issue_log_accountability.py` | registered #160 |
| `Issue_Log_Items/Issue_60/Issue_60_Scope_Decisions.md` | added SD-60-13 (approval record) |
| `Issue_Log_Items/Issue_160/tools/apply_issue160_pua_terminal_status_remap.py` | scoped remap script |

### Rulebook changes

None.

### Engine changes

One added `else` branch (status inheritance only); version bump v59.08 → v59.09.

---

## Evidence

| Artifact | Path |
|---|---|
| Discovery | `Issue_160_Discovery_Notes.md` |
| Intake / Planning / Dependency Gate / Risk | `Issue_160_Intake_Summary.md`, `Issue_160_Planning_Report.md`, `Issue_160_Dependency_Gate.md`, `Issue_160_Risk_Review_Report.md` |
| Implementation | `Issue_160_Implementation_Notes.md` |
| Validation | `Issue_160_Validation_Report.md` — **PASS** (independent re-derivation) |
| Regression | `Issue_160_Regression_Report.md` — **PASS** |
| Validator | `python tools/validators/validate_issue160_pua_terminal_status.py` |
| Accountability | #160 **IN_DATA** — `Issue_Log_Items/Issue_Log_Data_Accountability_20260714.md` line 67 |
| Test_Validation | `Output/Test_Validation/quikridr.csv` |
| Guide | `Completed_Issues_Release_Validation_Guide.md` row 160 |

---

## Trace Policy Confirmation

| Policy | Base MPHSTAT | PUA MPLAN | Before | After | Match |
|---|---|---|---|---|---|
| 9010360289C | 55 | 1708PA | 56 | **55** | Yes |
| 9010367705C | 55 | 1708PA | 56 | **55** | Yes |
| 9010376522C | 55 | 1960PA | 56 | **55** | Yes |
| 9010379405C | 55 | 1960PA | 56 | **55** | Yes |
| 9010391228C | 55 | 1970PA | 56 | **55** | Yes |
| 9010521213C | 50 | 1708PA | 22 | **50** | Yes |
| 9010150910C | 53 | 221EPA | 56 | **53** | Yes |
| 9010235370C | 57 | 280EPA | 56 | **57** | Yes |

---

## Output accountability (G7)

1. Issue validator **PASS** on full `QLA_Migration/Output/quikridr.csv` (independently re-derived, zero mismatches — see Validation Report).
2. Accountability **IN_DATA** for `#160` (`validate_issue_log_accountability.py`). Other catalog GAPs (#76, #114, #59:9010521213C, #135) are pre-existing, unrelated cut items — same set already documented as pre-existing in Issue #159's Closure.
3. `Test_Validation/quikridr.csv` published (hash-confirmed identical to Output).
4. Always-on smoke registered in `SMOKE_JOBS`. `--smoke-only`: **#160 PASS**. Suite overall RELEASE_BLOCKED on the pre-existing #59 MSTATUS gap (`9010521213C` / `901ML8250C`, 8/31 T/DC vs stale Output), first documented in Issue #159's Regression Report (2026-09-02) — not caused by, or worsened by, #160.

---

## Explicitly Not Changed

- [x] Base phase 1 `MPHSTAT` (already correct)
- [x] PUA `MPAR=0` (Issue #119)
- [x] PUA `MEFFDATE` / `MAGE` / `MPAYUP` / `MEXPRY` inheritance (Issue #60 SD-60-4/5/6/7)
- [x] Base 44/45 → PUA 54 (Issue #108D)
- [x] Base `< 50` → PUA 41 (Issue #60 SD-60-3)
- [x] Non-PUA riders (ADB, WP, term, etc.)
- [x] Rate tables, PVO, premiums, MPOLICY
- [x] `quikmstr`, `quikplan`, `quikclid`, `quikclnt`, and every other Output table (row counts unchanged, mtimes unchanged)

---

## Residual risks / follow-ups

- The pre-existing #59 MSTATUS gap on `9010521213C` (base phase currently 50, source now implies 53) means this policy's PUA phase will automatically re-follow to 53 once that base-phase refresh happens — no #160 code change will be needed when that occurs.
- This closes out the same defect class previously flagged only in **Issue #133's discovery notes** (base=50 case) as a side effect of the broader scope; no #133 artifact was modified.

---

## Rollback

Restore `QLA_Migration/Archive/issue160_pre_remap/quikridr_pre_issue160.csv` over `QLA_Migration/Output/quikridr.csv` and revert the added `else` branch in both `app.py` files (leave the 44/45 and `< 50` branches as they were).

---

## Git release

Issue-scoped files staged and committed; see commit hash recorded after `git push -u origin HEAD` below. `Output/` is gitignored — network machines keep v59.09 and the remapped `quikridr.csv` (or re-run a full policy batch, which now carries the fix natively).
