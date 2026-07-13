# Issue #55 — Resolution Summary

**Issue:** #55 — Unit Issues (MUNIT floor + leading-zero decimal emit)  
**Framework stage:** Closure Agent  
**Final status:** **Closed**  
**Engine version:** v57.78  
**Closed date:** 2026-07-13  
**Owner:** Conversion  
**Git:** `842274a` · branch `issue-34-pr7-quikisrr`

---

## Resolution (issue log — paste-ready)

```text
Resolution: quikridr MUNIT values below 0.001 are floored to zero and all rider decimal fields emit with a leading digit (0.53000 not .53000) so DBF load preserves correct units; MPREM mapping and MPOLICY padding unchanged.
```

---

## Problem Statement

Client reported wrong units in QLAdmin for RPU policies (e.g. `018495BC`, `018499CC`, `018510C`). LifePRO `NUMBER_OF_UNITS` mapped correctly in CSV, but leading-dot decimals (`.53000`) corrupted on DBF append (stored as `3000`). Fleet also had 148 rows with tiny Phase 1 units (`0.00001`) that should display as zero.

---

## Root Cause

**Category:** [x] QLAdmin behavior  [x] Client definition  [ ] Mapping error  [ ] Source extract defect

Two issues: (1) DBF/CSV numeric packing drops the first digit when values start with `.` (e.g. `.53000` → `3000`); (2) business rule: `0 < MUNIT < 0.001` should emit as `0`. QLAdmin Edit Phase showing Units `3000` from NFO×VPU/plan INITVAL is a separate display path — not fixed in this slice.

---

## Resolution

Post-map hook `apply_quikridr_decimal_emit()` floors sub-mill MUNIT and formats all QUIKRIDR numeric decimal fields with a leading zero per QLAdmin Help layout. MPREM (#26) keeps numeric value; only leading-dot prefix fixed. Full UAT batch at v57.78; validation and regression PASS.

### Files changed

| File | Change |
|------|--------|
| `qla_core/quikridr_decimal_emit.py` | New — floor + leading-zero format |
| `app.py` / `QLA_Migration/app.py` | v57.78 — hook before quikridr row append |
| `tools/validators/validate_issue55_munit_floor.py` | Fleet + trace validator |
| `QLA_Migration/_validate_issue55_munit_floor.py` | Thin wrapper |
| `Issue_Log_Items/Issue_55/*` | Framework artifacts G0–G7 |

### Rulebook changes

None — mapping `NUMBER_OF_UNITS → MUNIT` unchanged.

### Engine changes

- `MUNIT`: if `0 < x < 0.001` → `0` (formatted `0.00000`)
- Decimal fields: `f"{num:.{decimals}f}"` (never `.53000`)
- PUA pending-row path included

---

## Evidence

| Artifact | Path |
|----------|------|
| Intake | `Issue_55_Intake_Summary.md` |
| Planning | `Issue_55_Planning_Report.md` |
| Dependency Gate | `Issue_55_Dependency_Gate.md` |
| Risk review | `Issue_55_Risk_Review_Report.md` |
| Implementation | `Issue_55_Implementation_Notes.md` |
| Validation report | `Issue_55_Validation_Report.md` — **PASS** |
| Regression report | `Issue_55_Regression_Report.md` — **PASS** |
| Validation script | `QLA_Migration/_validate_issue55_munit_floor.py` |
| UAT partial reload | `QLA_Migration/Output/Test_Validation/quikridr.csv` |

---

## Trace Policy Confirmation

| Policy | Phase | Expected MUNIT | Emitted | Match |
|--------|------:|---------------:|---------|:-----:|
| `018495BC` | 1 | 0 | `0.00000` | Yes |
| `018495BC` | 2 | 0.53 | `0.53000` | Yes |
| `018499CC` | 1 | 0 | `0.00000` | Yes |
| `018499CC` | 2 | 1.05 | `1.05000` | Yes |
| `018510C` | 1 | 0 | `0.00000` | Yes |
| `018510C` | 2 | 0.647 | `0.64700` | Yes |
| `010434419C` | 2 (PUA) | 0 | `0.00000` | Yes |

---

## Explicitly Not Changed

- Issue #25 `format_qladmin_mpolicy()` — MPOLICY 10-char padding preserved
- Issue #26 `ANN_PREM_PER_UNIT` → MPREM + MODE_PREMIUM fallback
- Issue #49 MSTATUS / phase-1 MPHSTAT inherit
- `quikmstr.MNFOPT` / NFO display logic
- MVPU mapping (`VALUE_PER_UNIT`)
- QLAdmin Edit Phase Units `3000` display (out of scope)

---

## Fleet Impact

| Metric | Value |
|--------|------:|
| MUNIT floor rows | 148 |
| MUNIT format-only (leading zero) | 145 |
| Unexpected numeric changes | 0 |
| quikridr row count delta | 0 (6934) |

---

## Production Readiness + Git Release (G7)

| Check | Status |
|-------|--------|
| Validators PASS (G5 + G6) | Yes |
| `app.py` version v57.78 | Yes (both root + QLA_Migration) |
| Issue-scoped git commit | `842274a` |
| **`git push` to remote** | branch `issue-34-pr7-quikisrr` |
| Network batch note | `Output/` gitignored — pull then run full batch or `tools/batch_tests/run_full_batch_test.py`; re-append `quikridr.csv` with DBF Append Tool v1.5 |

---

## Client UAT

| Item | Status |
|------|--------|
| Conversion batch v57.78 | Pass |
| Validator / regression | Pass |
| QLAdmin reload + Coverage Units spot-check | Pending client |
| Client sign-off | Pending |

---

## Residual Risks / Follow-ups

| Item | Owner | Notes |
|------|-------|-------|
| QLAdmin Units `3000` on Edit Phase | Client / separate issue | NFO×VPU / plan INITVAL — not converter |
| DBF Append Tool | User desktop v1.5 | Leading-digit packing fix separate from engine |

---

## Rollback

1. Revert closure commit or restore pre-v57.78 `app.py` / remove `qla_core/quikridr_decimal_emit.py`
2. Re-run batch from baseline Source
3. Confirm `quikridr` reverts to pre-floor leading-dot format

---

## Issue Log Entry (paste-ready)

> **Issue #55 — Unit Issues — CLOSED (2026-07-13).**  
> **Resolution:** quikridr MUNIT values below 0.001 are floored to zero and all rider decimal fields emit with a leading digit (0.53000 not .53000) so DBF load preserves correct units; MPREM mapping and MPOLICY padding unchanged.  
> **Evidence:** Validation and regression PASS; trace policies 018495BC, 018499CC, 018510C, 010434419C confirmed. **Preserved:** MPOLICY padding (#25), MPREM mapping (#26), MSTATUS (#49). **Follow-ups:** QLAdmin false `3000` Units display (out of scope); client UAT reload.

---

## Framework Checklist

- [x] Intake
- [x] Planning
- [x] Dependency Gate PASS
- [x] Risk Conditional Go
- [x] Development (v57.78)
- [x] Validation PASS
- [x] Regression PASS
- [x] Closure — Resolution + tracking Closed
- [x] Git commit + push (G7)
