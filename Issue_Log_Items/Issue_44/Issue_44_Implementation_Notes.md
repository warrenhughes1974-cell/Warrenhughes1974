# Issue #44 — Implementation Notes

**Issue:** #44 — ETI/RPU QuikLoan Balance Clear  
**Framework stage:** Development Agent (G4)  
**Engine:** **v57.60** (Phase A only; Phase B withdrawn)  
**Date:** 2026-07-09  

---

## Scope decision

| Phase | Status |
|-------|--------|
| **A** — `LAST_CHG_TIME` HHMMSS sort | **IN FORCE** |
| **B** — Suppress QuikLoan when MSTATUS ∈ {44,45} | **WITHDRAWN** 2026-07-09 per project lead |

---

## Changes (current)

| File | Change |
|------|--------|
| `qla_core/quikloan_converter.py` | Phase A only: `normalize_ploan_chg_time` + latest-row sort; Phase B helpers/holds removed |
| `plan_governance/config/quikloan_derivation_rules.json` | v1.3; no `suppress_quikloan_on_eti_rpu` |
| `app.py` / `QLA_Migration/app.py` | **APP_VERSION = v57.60** |

---

## Behavior

1. Same-day PLOAN `.00` clear (later `LAST_CHG_TIME`) wins → zero balance → `ZERO_BALANCE_HELD` → no QuikLoan row.  
2. If PLOAN latest balance is still open (e.g. 011226579C on ETI), QuikLoan **still emits** the balance — status alone does not suppress.

---

## Explicitly not changed

- `quikmstr.MSTATUS` / Issue #13  
- `quikplan.LOANINT`  
- Issue #25 / #26  
- QuikLoan field formulas
