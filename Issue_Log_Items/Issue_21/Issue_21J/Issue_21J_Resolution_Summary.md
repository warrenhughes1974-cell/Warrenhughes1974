# Issue #21J — Resolution Summary

**Issue:** #21J — Modal Premium Factors  
**Framework stage:** Closure (G7)  
**Final status:** **Closed**  
**Engine version:** **v57.46**  
**Closed date:** 2026-07-04  
**Owner:** Conversion (Warren) · Reporter: Eric

---

## Production Readiness (G7 gate)

| Check | Status |
|-------|--------|
| G5 validation PASS | **Done** — `Issue_21J_Validation_Report.md` |
| G6 regression PASS | **Done** — `Issue_21J_Regression_Report.md` |
| `app.py` / `QLA_Migration/app.py` **v57.46** | **Done** |
| Issue-scoped git commit | **Done** — `5cacd68` |
| Git push to remote | **Done** — `origin/issue-34-pr7-quikisrr` @ `612b6e5` |
| Network batch after pull | Re-run full batch at v57.46 (`Output/` gitignored) |

---

## Problem Statement

QLAdmin Coverage Detail modal premium quotes did not match LifePRO because every plan used generic modal factors (100 / 51 / 26.5 / 9.25 / 9.25). Monthly amounts appeared as Annual ÷ 12 instead of product-specific factors (e.g. `010713704C` on plan `1659C2`). The billed draft premium (`MODE_PREMIUM` → `MMODEPREM`) was already correct; the defect was plan setup and governance visibility.

---

## Root Cause

**Category:** Product setup / mapping — plan-level modal factors not loaded from client authority

The converter applied rulebook defaults to all `quikplan` rows and did not overlay per-plan factors from LifePRO/QLA product definitions. Policy-level PAC quarterly/semiannual exceptions for plans `170858` / `17085M` were not applied to `quikmstr.MSEMI` / `MQTRL`. No fleet memo documented factors for Customer Service.

---

## Resolution (v57.46)

1. **Client mapping** — `QLA_Migration/Mapping/Modal_Premium_Factors_By_Plan.csv` (141 plans from `docs/Policy Form Modal Premium Factors.xlsx`; Excel decimal × 100 → QLAdmin percent).
2. **quikplan overlay** — `qla_core/modal_premium_factors.py` + hook in `quikplan_converter.py` and batch `app.py` after CSO enrichment.
3. **PAC GL85 overrides** — After `quikridr` emit, set `quikmstr.MQTRL=25` (PAC + quarterly) or `MSEMI=50` (PAC + semiannual) for plans `170858` / `17085M`; detects translated `MBILLFRM=2` (BF_PAC).
4. **QUIKMEMO governance** — Fleet-wide `[CONVERSION]` segment per policy (5,083 rows) with plan factors, `MMODEPREM`, PAC override note when applicable, and CS recalculation warning. PNOTE/PENSE preserved after `\n---\n` (#21M-FU).

### Files changed

| File | Change |
|------|--------|
| `qla_core/modal_premium_factors.py` | New — overlay, PAC overrides, memo append |
| `qla_core/quikplan_converter.py` | Modal factor post-step |
| `app.py` / `QLA_Migration/app.py` | v57.46; quikplan + quikridr + quikmemo hooks |
| `QLA_Migration/Mapping/Modal_Premium_Factors_By_Plan.csv` | Client factor table |
| `tools/validators/validate_issue21j_modal_factors.py` | New |
| `tools/validators/validate_issue21m_quikmemo.py` | Baseline 5,083 rows (21J) |
| `tools/validators/validate_issue21m_dbf_packaging.py` | 5,083 rows; `[CONVERSION]` prefix |

---

## Evidence

| Artifact | Path |
|----------|------|
| Validation (G5) | `Issue_21J_Validation_Report.md` |
| Regression (G6) | `Issue_21J_Regression_Report.md` |
| Client factors source | `docs/Policy Form Modal Premium Factors.xlsx` |
| Validator | `tools/validators/validate_issue21j_modal_factors.py` |

---

## Trace Policy Confirmation

| Policy | MPLAN | quikplan SEMI/QTRL | MMODEPREM | PAC override |
|--------|-------|-------------------|-----------|--------------|
| 010713704C | 1659C2 | 52.5 / 27.0 | 43.91 | — |
| 010560185C | 170858 | 52.0 / 26.5 | 15.00 | MQTRL=25 |
| 010818663C | 1659C2 | 52.5 / 27.0 | (LifePRO draft) | — |

---

## Explicit Non-Changes

- `PPOLC.MODE_PREMIUM` → `quikmstr.MMODEPREM` (#26)
- `PPBEN.ANN_PREM_PER_UNIT` → `quikridr.MPREM` (#26)
- MPOLICY padding (#25)
- quikridr / quikprmh row counts and schema
- Rulebook crosswalks (except new mapping CSV)

---

## Residual / Follow-Up

- **Client UAT:** Confirm Coverage Detail modal grid on sample policies in QLAdmin after reload.
- **Clean batch:** Re-run full batch at v57.46 on network pull so PAC overrides and memos emit in one pass (no manual post-process).
- **34 rider plans** in Excel not in quikplan catalog — ignored per client approval.

---

## Rollback

1. Revert commit on branch (see hash below after push).
2. Remove `append_issue21j_conversion_memos` call and quikplan overlay hook.
3. Delete or bypass `Modal_Premium_Factors_By_Plan.csv` overlay.
4. Re-run batch — quikmemo returns to 4,380 PNOTE/PENSE-only rows; quikplan modal fields revert to rulebook defaults.

---

## Git Release Record

| Field | Value |
|-------|-------|
| Branch | `issue-34-pr7-quikisrr` |
| Commit | `5cacd68` |
| Message | `Close Issue #21J: Modal premium factors (v57.46)` |

---

**Issue #21J — Closed.** Modal factors applied per client mapping; PAC GL85 policy overrides and fleet governance memos in place at v57.46.
