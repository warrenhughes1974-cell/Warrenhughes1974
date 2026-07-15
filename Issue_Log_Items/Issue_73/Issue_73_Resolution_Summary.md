# Issue #73 — Resolution Summary

**Issue:** #73 — Country code (`MISSCNTRY`) must be `0000` for all policies  
**Framework stage:** Closure Agent  
**Final status:** **Closed**  
**Release:** Rulebook-only (no `app.py` version bump)  
**Closed date:** 2026-07-15  
**Owner:** Conversion

---

## Resolution (issue log — paste-ready)

**Resolution:** quikmstr.MISSCNTRY (Issue Country) now defaults to `0000` (ALL) for all policies, aligning policy keys with rate segmentation ISSCNTRY=0000.

> Copy the line above into tracking sheets and client readouts. Long-form detail follows.

---

## Problem Statement

Client required Issue Country = **`0000`** on every policy (“country date must be 0000 for all policies”). Conversion was emitting **`USA`** on all **5,083** policy masters via Sync Rulebook default, while rate tables already use **`ISSCNTRY=0000`** (ALL). Data governance **POL-025** also expects `MISSCNTRY=0000`.

---

## Root Cause

**Category:** Mapping error (rulebook default)

`Sync_Rulebook_quikmstr.csv` hard-defaulted blank-source `MISSCNTRY` to **`USA`** instead of QLAdmin’s standard ALL key **`0000`**. No LifePRO source column drives this field.

---

## Resolution (long-form)

Changed rulebook default **`USA` → `0000`**, refreshed fleet `quikmstr.csv`, validated **5,083 / 5,083** policies, and published `Test_Validation/quikmstr.csv` for partial UAT reload. No engine or rate pipeline changes.

### Files changed

| File | Change |
|------|--------|
| `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv` | `MISSCNTRY` Default_Value `0000` |
| `tools/validators/validate_issue73_misscntry.py` | Issue validator (new) |
| `Issue_Log_Items/Issue_73/scripts/validate_issue73_misscntry.py` | Wrapper |
| `Issue_Log_Items/Issue_73/scripts/regression_issue73.py` | Regression checks (new) |
| `QLA_Migration/Output/quikmstr.csv` | Fleet refresh |
| `QLA_Migration/Output/Test_Validation/quikmstr.csv` | UAT publish |

### Rulebook changes

| Rulebook | Before | After |
|----------|--------|-------|
| `Sync_Rulebook_quikmstr.csv` MISSCNTRY | `USA` | **`0000`** |

### Engine changes

None — rulebook-only fix.

---

## Evidence

| Artifact | Path |
|----------|------|
| Intake | `Issue_Log_Items/Issue_73/Issue_73_Intake_Summary.md` |
| Planning | `Issue_Log_Items/Issue_73/Issue_73_Planning_Report.md` |
| Dependency Gate | `Issue_Log_Items/Issue_73/Issue_73_Dependency_Gate.md` |
| Risk review | `Issue_Log_Items/Issue_73/Issue_73_Risk_Review_Report.md` |
| Implementation | `Issue_Log_Items/Issue_73/Issue_73_Implementation_Notes.md` |
| Validation report | **PASS** — `Issue_Log_Items/Issue_73/Issue_73_Validation_Report.md` |
| Regression report | **PASS** — `Issue_Log_Items/Issue_73/Issue_73_Regression_Report.md` |
| Validation script | `tools/validators/validate_issue73_misscntry.py` |

---

## Trace Policy Confirmation

| Policy | Field | Expected | Actual | Match |
|--------|-------|----------|--------|-------|
| 010143726C | MISSCNTRY | `0000` | `0000` | Yes |
| 010143726C | MISSUEST | `CA` | `CA` | Yes |
| 010148272C | MISSCNTRY | `0000` | `0000` | Yes |
| 010148856C | MISSCNTRY | `0000` | `0000` | Yes |
| 010149295C | MISSCNTRY | `0000` | `0000` | Yes |
| 010157076C | MISSCNTRY | `0000` | `0000` | Yes |

---

## Explicitly Not Changed

- `quikclnt.MCOUNTRY` (mailing/address country)
- `MISSUEST` / `MRESSTATE`
- Rate `ISSCNTRY` emit (already `0000`)
- Issue #25 MPOLICY 10-char padding
- Issue #26 MPREM / MMODPREM mapping
- Issue #72 MNFOPT force for ETI/RPU (still PASS on same quikmstr)
- quikridr / quikprmh / quikclnt row counts

---

## Fleet Impact

| Metric | Value |
|--------|------:|
| quikmstr rows updated | 5,083 |
| MISSCNTRY USA → 0000 | 5,083 |
| Other table row deltas | 0 |

---

## Production Readiness + Git Release (G7)

| Check | Status |
|-------|--------|
| Validators PASS (G5 + G6) | **Yes** |
| `app.py` version bumped | **N/A** (rulebook-only) |
| Issue-scoped git commit | **Pending** — user may commit when ready |
| Network batch note | After pull: run full batch (or rulebook-driven quikmstr emit); `Output/` gitignored — reload `Test_Validation/quikmstr.csv` for partial UAT |

---

## Client UAT

| Item | Status |
|------|--------|
| Validation / regression | **PASS** (user confirmed) |
| QLAdmin Policy Display Issue Country | Reload `Test_Validation/quikmstr.csv` → expect **`0000`** |

---

## Residual Risks / Follow-ups

| Item | Owner | Notes |
|------|-------|-------|
| Full network batch after git pull | Conversion | Regenerates quikmstr from rulebook on batch machines |
| OBQ-73-1 | Client | If UAT meant `MCOUNTRY` not `MISSCNTRY`, reopen — scope was Issue Country only |

---

## Rollback

1. Revert `Sync_Rulebook_quikmstr.csv` line: `MISSCNTRY` Default_Value back to `USA`
2. Re-run batch or refresh quikmstr
3. Confirm `validate_issue73_misscntry.py` fails

---

## Issue Log Entry (paste-ready)

> **Issue #73 — Country code must be 0000 — CLOSED (2026-07-15).**  
> **Resolution:** quikmstr.MISSCNTRY (Issue Country) now defaults to `0000` (ALL) for all policies, aligning policy keys with rate segmentation ISSCNTRY=0000.  
> **Evidence:** Validation and regression PASS; 5083/5083 fleet; trace policies confirmed. **Preserved:** MPOLICY padding (#25), MPREM mapping (#26), MNFOPT force (#72), MCOUNTRY. **Follow-ups:** network batch after pull.

---

## Framework Checklist

- [x] Intake
- [x] Planning
- [x] Dependency Gate PASS
- [x] Risk Go
- [x] Development
- [x] Validation PASS
- [x] Regression PASS
- [x] Closure — **`Resolution:`** one-line + long-form summary
- [ ] Git commit + push (optional — rulebook + docs; no app.py bump)
