# Issue #13 — Resolution Summary

**Resolution:** When `CONTRACT_CODE=T`, `quikmstr.MSTATUS` now follows `CONTRACT_REASON` (termination) instead of `PAID_UP_TYPE` (non-forfeiture); 607 policies corrected (v57.48).

**Issue:** #13 — Incorrect QL Status  
**Framework stage:** Closure Agent (G7)  
**Final status:** **Closed**  
**Engine version:** **v57.48**  
**Closed date:** 2026-07-04  
**Owner:** Conversion (Warren) · Reporter: Eric

---

## Production Readiness (G7 gate)

| Check | Status |
|-------|--------|
| G5 validation PASS | **Done** |
| G6 regression PASS | **Done** |
| `app.py` / `QLA_Migration/app.py` **v57.48** | **Done** |
| Issue-scoped git commit | Pending below |
| Git push to remote | Pending below |
| Network batch after pull | Re-run full batch at v57.48 (`Output/` gitignored) |

---

## Problem Statement

Eric reported policies showing **non-forfeiture** QLAdmin statuses (Paid Up 41, Extended Term 44) while LifePRO benefit extract showed **Terminated** with reasons such as Expired or Lapsed. Examples: **010516211C** (T/LP → was 44), **011101663C** (T/EX → was 41).

---

## Root Cause

**Category:** Business precedence / mapping rule

The MSTATUS composite interceptor prioritized **`PAID_UP_TYPE`** (PU, LE, ET, etc.) over **`CONTRACT_CODE` / `CONTRACT_REASON`** when both were present on terminated contracts. LifePRO stores both dimensions; the converter favored non-forfeiture outcome codes.

---

## Fix Summary

**Option A (approved):** When `CONTRACT_CODE = T`, build MSTATUS from termination reason only; ignore `PAID_UP_TYPE`. Non-terminated contracts unchanged.

### Files changed

| File | Change |
|------|--------|
| `app.py` | v57.48; MSTATUS interceptor |
| `QLA_Migration/app.py` | Mirror |
| `plan_analysis/status_analysis/status_analysis_runner.py` | Parity helper |
| `tools/validators/validate_issue13_mstatus.py` | New validator |
| `Issue_Log_Items/Issue_13/*` | Framework artifacts |

### Rulebook changes

**None**

---

## Evidence

| Artifact | Path |
|----------|------|
| Intake | `Issue_13_Intake_Summary.md` |
| Planning | `Issue_13_Planning_Report.md` |
| Dependency Gate | `Issue_13_Dependency_Gate.md` |
| Risk | `Issue_13_Risk_Review_Report.md` |
| Implementation | `Issue_13_Implementation_Notes.md` |
| Validation (G5) | `Issue_13_Validation_Report.md` |
| Regression (G6) | `Issue_13_Regression_Report.md` |
| Simulation | `Issue_13_Risk_Simulation.csv` |
| Validator | `tools/validators/validate_issue13_mstatus.py` |

---

## Trace Policy Confirmation

| Policy | LifePRO | Before | After | Match |
|--------|---------|-------:|------:|-------|
| 010516211C | T / LP / LE | 44 | **54** | Yes |
| 011101663C | T / EX / PU | 41 | **56** | Yes |
| 010397318C | T / DC / RU | 45 | **53** | Yes |
| 010464590C | T / DC / RU | 45 | **53** | Yes |
| 010784054C | T / EX | 56 | **56** | Yes |

---

## Explicitly Not Changed

- Issue #25 MPOLICY 10-char padding
- Issue #26 MPREM / quikmstr.MMODPREM
- Issue #21A MNFOPT / MDIVOPT cache
- `Master_Value_Translation.csv` ST_* keys
- Claim `CLAIMSTAT` derivation
- quikmstr row count (5,083)

---

## Fleet Impact

| Metric | Value |
|--------|------:|
| Policies with MSTATUS change | 607 |
| Unchanged | 4,477 |
| quikridr MPHSTAT inherit | Automatic on phase-1 rows |

---

## Git Release

| Item | Value |
|------|-------|
| Commit | *(recorded after push)* |
| Branch | `issue-34-pr7-quikisrr` |

**Network batch:** Pull latest branch, confirm **v57.48** in `app.py`, run **`QLA_Migration/run_converter.bat`** or `tools/batch_tests/run_full_batch_test.py`. Regenerate `quikmstr.csv` on network machine (`Output/` gitignored).

---

## Rollback

1. Revert MSTATUS interceptor to PAID_UP_TYPE-first logic (v57.47).
2. Re-run full batch.
3. `validate_issue13_mstatus.py` will fail on Eric sample policies (expected).

---

## Issue Log Entry (paste-ready)

> **Issue #13 — Incorrect QL Status — CLOSED (2026-07-04).** Terminated LifePRO policies were emitting non-forfeiture QLAdmin statuses because PAID_UP_TYPE took precedence over contract termination. **Fix:** v57.48 uses CONTRACT_REASON when CONTRACT_CODE=T; 607 policies updated. **Evidence:** Validation and regression PASS; 010516211C→54, 011101663C→56. **Preserved:** MPOLICY (#25), MPREM (#26), MNFOPT (#21A).

---

## Framework Checklist

- [x] Intake
- [x] Planning
- [x] Dependency Gate PASS
- [x] Risk GO
- [x] Development (v57.48)
- [x] Validation PASS
- [x] Regression PASS
- [x] Closure
- [ ] Git commit + push (G7 — in progress)
