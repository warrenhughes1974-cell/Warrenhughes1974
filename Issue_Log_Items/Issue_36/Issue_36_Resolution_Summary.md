# Issue #36 — Resolution Summary

**Issue:** #36 — Modal Premium factors at policy level (`quikmstr`)  
**Framework stage:** Closure Agent  
**Final status:** **Closed** (Client UAT recommended on Names tab)  
**Engine version:** **v57.62**  
**Closed date:** 2026-07-09  
**Owner:** Conversion  
**Git commit:** `243860154086ff46a88bfef3f6d10cead09a3dc7`  
**Remote branch:** `origin/issue-34-pr7-quikisrr`

---

## Resolution (issue log — paste-ready)

**Resolution:** quikmstr now receives plan-level modal factors (MSEMI/MQTRL/MMTHD/MMTHB) from quikplan, with PAC GL85 quarterly=25 and semiannual=50 overrides, so Names-tab Modal Premiums work (v57.62).

> Copy the line above into tracking sheets and client readouts.

---

## Problem Statement

When policy-level modal factors were blank on `quikmstr`, QLAdmin Names-tab Modal Premiums did not work (fell back to crude mode division). Related to Issue #21J, which fixed plan-level factors and PAC overrides but did not copy factors onto every policy.

---

## Root Cause

**Category:** [x] Scope gap (mapping incomplete)

`Sync_Rulebook_quikmstr.csv` never mapped `MSEMI`/`MQTRL`/`MMTHD`/`MMTHB`. Issue #21J populated `quikplan` factors and PAC-only overrides; fleet policy-level copy was left undone. LifePRO extracts do not contain policy-level quote factors.

---

## Resolution

Post-`quikridr` emit enrichment (v57.62):

1. Copy phase-1 `MPLAN` → `quikplan` SEMI/QTRL/MTHD/MTHB → `quikmstr` MSEMI/MQTRL/MMTHD/MMTHB (MMTHD/MMTHB independent).
2. Apply existing PAC GL85 special modes: mode 3 → `MQTRL=25.0000`; mode 6 → `MSEMI=50.0000` on plans `170858`/`17085M`.
3. Fallback to `Modal_Premium_Factors_By_Plan.csv` if `quikplan.csv` is missing.

### Files changed

| File | Change |
|------|--------|
| `qla_core/modal_premium_factors.py` | `apply_plan_modal_factors_to_quikmstr`; shared phase-1 lookup |
| `app.py` / `QLA_Migration/app.py` | Wire plan copy before PAC; **v57.62** |
| `tools/validators/validate_issue36_quikmstr_modal_factors.py` | New validator |
| `Issue_Log_Items/Issue_36/*` | Framework artifacts G0–G7 |

### Engine changes

- Surgical post-emit `quikmstr` factor enrichment only

---

## Evidence

| Stage | Artifact | Result |
|-------|----------|--------|
| G5 | `Issue_36_Validation_Report.md` | **PASS** |
| G6 | `Issue_36_Regression_Report.md` | **PASS** |
| Validator | `validate_issue36_quikmstr_modal_factors.py` | **PASS** — 5083/5083 |
| Prior | #21J / #25 validators | **PASS** |

---

## Trace policies

| Policy | Result |
|--------|--------|
| 010148856C | 51.0140 / 26.0010 / 8.9964 / 8.9989 |
| 010713704C | 52.5000 / 27.0000 / 9.1999 / 8.8018 |
| 010560185C | PAC Q — MQTRL=**25.0000** |
| 010442216C | PAC S — MSEMI=**50.0000** |

---

## Non-changes (preserved)

- `MMODEPREM` / Issue #26 `MPREM`
- Issue #25 MPOLICY padding
- Issue #21J `quikplan` factor overlay (read source only)
- `quikridr` fee columns (`M*FEE`)
- Row counts on all quik* tables

---

## Residual risks / follow-ups

- **Client UAT:** Confirm Names-tab Modal Premiums display correctly after DBF load (runtime dollar math is QLAdmin).
- Network machines: `git pull` → re-run full batch at **v57.62** (`Output/` is gitignored).

---

## Rollback

1. Revert commit for Issue #36 (or restore `modal_premium_factors.py` + both `app.py` to v57.61).
2. Re-run batch — factor columns return to blank (pre-#36 behavior).

---

## Production ready / network pull

1. Pull branch containing this commit.
2. Confirm `APP_VERSION` = **v57.62** in root `app.py`.
3. Run `QLA_Migration/run_converter.bat` (full batch).
4. Spot-check Names tab on `010148856C`, `010560185C`, `010442216C`.
5. Optional: `python tools/validators/validate_issue36_quikmstr_modal_factors.py`

---

## Gate G7 checklist

- [x] `Resolution:` one-line published
- [x] Resolution summary published
- [x] Tracking sheets → **Closed** + Resolution
- [x] Validators PASS; version bumped
- [x] Git commit + push completed
- [x] Commit hash recorded: `243860154086ff46a88bfef3f6d10cead09a3dc7` on `origin/issue-34-pr7-quikisrr`
