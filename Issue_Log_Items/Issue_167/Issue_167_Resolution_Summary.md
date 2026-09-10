# Issue #167 — Resolution Summary

**Issue:** #167 — Dividend Premium Payment
**Framework stage:** Closure Agent
**Final status:** **Closed**
**Engine version:** v59.12
**Closed date:** 2026-09-10
**Owner:** Conversion

---

## Resolution (issue log — paste-ready)

**Resolution:** Duration on rider coverages now uses the policy anniversary month and day against the valuation date, so QLAdmin will process anniversaries that have not occurred yet.

---

## Problem Statement

Eric reported that policy 9010397528C did not show the 9/1/2026 anniversary dividend. The option is Reduce Premium, and the dividend is larger than the annual premium with the remainder paid in cash.

---

## Root Cause

**Category:** [x] Mapping error

`quikridr.MLASTANN` used calendar year only (`valuation year − issue year`). On an 8/31/2026 valuation that made a 9/1/1971 issue look like duration 55, so QLAdmin treated the 9/1/2026 anniversary as already processed. LifePRO PACTG on the 8/31 extract has no 9/1/2026 dividend posting; the last real anniversary is 9/1/2025. There is no standing duration field on PPBEN/PPOLC to copy.

---

## Resolution

Duration now counts completed years through the issue anniversary month and day, the same month/day test as Issue #108B. Current 8/31 Output was remapped (2,142 rows, all −1). ETI/RPU phase 1 stays on Issue #76 paid-to math. We did not invent a 20260901 `quikbenh` row and did not map `EXCESS_DIVIDEND`.

### Files changed

| File | Change |
|---|---|
| `app.py` / `QLA_Migration/app.py` | `_compute_quikridr_mlastann` anniversary math + v59.12 |
| `QLA_Migration/Output/quikridr.csv` | MLASTANN remap (2,142 rows, gitignored) |
| `tools/validators/validate_issue167_mlastann.py` | fail-closed validator |
| `tools/validators/validate_release_closed_issues.py` | `SMOKE_JOBS` — registered #167 |
| `tools/validators/validate_issue_log_accountability.py` | registered #167 |
| `Issue_Log_Items/Issue_167/tools/remap_issue167_mlastann.py` | scoped remap script |

### Rulebook changes

None.

### Engine changes

One formula change in `_compute_quikridr_mlastann`; version bump to v59.12.

---

## Evidence

| Artifact | Path |
|---|---|
| Discovery | `Issue_167_Discovery_Notes.md` |
| Intake / Planning / Dependency Gate / Risk | `Issue_167_Intake_Summary.md`, `Issue_167_Planning_Report.md`, `Issue_167_Dependency_Gate.md`, `Issue_167_Risk_Review_Report.md` |
| Implementation | `Issue_167_Implementation_Notes.md` |
| Validation | `Issue_167_Validation_Report.md` — **PASS** |
| Regression | `Issue_167_Regression_Report.md` — **PASS** |
| Validator | `python tools/validators/validate_issue167_mlastann.py` |
| Accountability | #167 **IN_DATA** (same validator job) |
| Test_Validation | `Output/Test_Validation/quikridr.csv` |
| Guide | `Completed_Issues_Release_Validation_Guide.md` row 167 |

---

## Trace Policy Confirmation

| Policy | Phase | Before | After | Match |
|---|---|---|---|---|
| 9010397528C | 1 | 55 | **54** | Yes |
| 9010397528C | 2 | 55 | **54** | Yes |
| 9010367704C | 1 | 56 | 56 | Yes |
| 9010412641C | 1 | 54 | 54 | Yes |
| 9010149295C | 1 ETI | 33 | 33 | Yes |
| 9010374099C | 1 ETI | 16 | 16 | Yes |

---

## Output accountability (G7)

1. Issue validator **PASS** on full `QLA_Migration/Output/quikridr.csv`.
2. Accountability **IN_DATA** for `#167`. Other catalog GAPs (#76, #114, #59:010521213C) are pre-existing on this 8/31 cut.
3. `Test_Validation/quikridr.csv` published.
4. Always-on smoke registered in `SMOKE_JOBS`. `--smoke-only`: **#167 PASS**. Suite may still be RELEASE_BLOCKED on the pre-existing #59 MSTATUS gap.

---

## Explicitly Not Changed

- [x] ETI/RPU phase-1 `MLASTANN` (Issue #76 / #108B)
- [x] `quikmstr.MDIVOPT` / `MPREM` / `MPOLICY`
- [x] `quikbenh` (no invented 20260901 dividend row)
- [x] `EXCESS_DIVIDEND`
- [x] QuikIswl.MLASTANNV
- [x] `quikplan` / `rates/` (older-cut keep-newest package)

---

## Residual risks / follow-ups

- Eric should run a zero-day cycle in QLAdmin so the 9/1/2026 Reduce-Premium / cash-excess dividend generates from the corrected duration.
- `EXCESS_DIVIDEND=1` remains unmapped (two policies; out of scope).

---

## Rollback

Restore `Issue_Log_Items/Issue_167/evidence/quikridr_pre_issue167_20260910T081723Z.csv` over `QLA_Migration/Output/quikridr.csv` and revert `_compute_quikridr_mlastann` in both `app.py` files to year-only math.

---

## Git release

Commit pending on this close (issue-scoped files only). `Output/` is gitignored — network machines keep v59.12 and the remapped `quikridr.csv` (or re-run a full policy batch, which now carries the fix natively). Not pushed unless Warren asks.
