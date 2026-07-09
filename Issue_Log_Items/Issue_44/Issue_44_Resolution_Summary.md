# Issue #44 — Resolution Summary

**Issue:** #44 — QuikLoan stale PLOAN latest-row (`LAST_CHG_TIME` sort)  
**Framework stage:** Closure Agent  
**Final status:** **Closed**  
**Engine version:** **v57.60**  
**Closed date:** 2026-07-09  
**Owner:** Conversion

---

## Resolution (issue log — paste-ready)

**Resolution:** QuikLoan now sorts PLOAN `LAST_CHG_TIME` as HHMMSS so same-day zero-balance clears win the latest-row pick; stale loan balances no longer emit (v57.60). Phase B ETI/RPU status suppress was withdrawn.

> Copy the line above into tracking sheets and client readouts.

---

## Problem Statement

BA reported ETI policies (`MSTATUS` 44) with non-zero `quikloan.MLOANBAL`. For five of six sample policies, LifePRO already had a same-day `.00` clear that conversion was missing.

---

## Root Cause

**Category:** [x] Mapping error (latest-row selection)

`select_latest_ploan_row_per_policy` fed `LAST_CHG_TIME` (HHMMSS) through `parse_ploan_date`, which mis-ordered same-day twins so the pre-clear balance was emitted.

---

## Resolution

Phase A only: normalize and sort `LAST_CHG_TIME` as a time string. Zero latest balance continues to use existing `ZERO_BALANCE_HELD` (no QuikLoan row). Phase B (suppress by ETI/RPU status) was implemented briefly then **withdrawn** per project lead — open PLOAN on ETI (e.g. 011226579C) still emits.

### Files changed

| File | Change |
|------|--------|
| `qla_core/quikloan_converter.py` | Phase A HHMMSS sort |
| `plan_governance/config/quikloan_derivation_rules.json` | v1.3 notes; no Phase B flag |
| `app.py` / `QLA_Migration/app.py` | **v57.60** |
| `Issue_Log_Items/Issue_44/*` | Framework artifacts |

### Engine changes

- Surgical QuikLoan latest-row selection only (Phase A)

---

## Evidence

| Artifact | Path |
|----------|------|
| Intake | `Issue_44_Intake_Summary.md` |
| Planning | `Issue_44_Planning_Report.md` |
| Dependency Gate | `Issue_44_Dependency_Gate.md` |
| Risk | `Issue_44_Risk_Review_Report.md` |
| Implementation | `Issue_44_Implementation_Notes.md` |
| Validation | `Issue_44_Validation_Report.md` — PASS |
| Regression | `Issue_44_Regression_Report.md` — PASS |
| BA matrix | `evidence/issue44_ba_sample_matrix.csv` |
| Emit delta | `evidence/issue44_regression_delta.csv` |

---

## Trace Policy Confirmation

| Policy | Expected | Emitted | Match |
|--------|----------|---------|-------|
| 010391876C | No QuikLoan row | Held | Yes |
| 010404602C | No QuikLoan row | Held | Yes |
| 010456751C | No QuikLoan row | Held | Yes |
| 010510671C | No QuikLoan row | Held | Yes |
| 010525250C | No QuikLoan row | Held | Yes |
| 011226579C | Still emit (open PLOAN) | 1236.48 | Yes |

---

## Explicitly Not Changed

- [x] quikmstr.MSTATUS / Issue #13  
- [x] Issue #26 MPREM  
- [x] Issue #25 MPOLICY padding (verified)  
- [x] Phase B status suppress (withdrawn)

---

## Fleet Impact

| Metric | Value |
|--------|------:|
| QuikLoan emit rows removed (correct clears) | 30 |
| QuikLoan emit rows added | 0 |
| Schema drift | 0 |

---

## Production Readiness + Git Release (G7)

| Check | Status |
|-------|--------|
| Validators PASS (G5 + G6) | PASS |
| `app.py` version bumped | **v57.60** (both copies) |
| Commit + push | Recorded below after push |
| Network re-run | Re-emit QuikLoan with `QLA_ENABLE_QUIKLOAN_EMIT=1` after pull |

### Git release

| Field | Value |
|-------|-------|
| Branch | `issue-34-pr7-quikisrr` |
| Commit | `beadddf731d79e2796140d1ed7aa38e19ed015e7` |
| Remote | origin |

---

## Client UAT note

Restart converter (**v57.60**), re-run QuikLoan emit, confirm BA five policies have no loan row. Policy **011226579C** still has a loan because LifePRO PLOAN latest balance remains open.
