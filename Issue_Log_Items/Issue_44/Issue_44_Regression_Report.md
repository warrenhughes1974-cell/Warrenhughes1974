# Issue #44 — Regression Report (G6)

**Issue:** QuikLoan PLOAN latest-row sort (Phase A only)  
**Date:** 2026-07-09  
**Engine:** **v57.60**  
**Status:** **PASS**

---

## Scope

| In scope | Out of scope |
|----------|--------------|
| `qla_core/quikloan_converter.py` latest-row sort | Phase B ETI/RPU status suppress (**withdrawn**) |
| QuikLoan emit population delta | `quikmstr.MSTATUS`, product setup, other tables |

---

## QuikLoan emit comparison

Baseline: existing `QLA_Migration/Output/quikloan.csv` (pre–Phase A)  
After: re-run `convert_quikloan_from_ploan` with v57.60 rules

| Metric | Before | After | Delta |
|--------|-------:|------:|------:|
| Emit rows | 386 | 356 | **−30** |
| Added policies | — | — | 0 |
| Removed (correct zero latest) | — | — | **30** |

Evidence: `evidence/issue44_regression_delta.csv`

All **30** removals are policies whose latest PLOAN row is now correctly `.00` (same-day clear wins). No unexpected adds.

---

## BA sample regression

| Policy | Before | After | OK? |
|--------|--------|-------|-----|
| 010391876C | In emit | Held ZERO_BALANCE | Yes |
| 010404602C | In emit | Held ZERO_BALANCE | Yes |
| 010456751C | In emit | Held ZERO_BALANCE | Yes |
| 010510671C | In emit | Held ZERO_BALANCE | Yes |
| 010525250C | In emit | Held ZERO_BALANCE | Yes |
| 011226579C | In emit 1236.48 | **Still in emit 1236.48** | Yes (open PLOAN) |

---

## Schema / prior fixes

| Check | Result |
|-------|--------|
| QuikLoan column order = `QUIKLOAN_SCHEMA` | **PASS** |
| Issue #25 MPOLICY 10-char on emit | **PASS** (0 short) |
| Phase B `ETI_RPU_STATUS_HOLD` absent | **PASS** (0) |
| Sample active loan fields (INT/INTX/ACCR) | Unchanged pattern (5.00 / A / 0.00) |
| `LAST_CHG_TIME` no longer date-parsed for sort | **PASS** (`212540` < `212541` as HHMMSS) |

---

## Untouched surfaces (by design)

- `quikmstr` / `quikridr` / Issue #13 status mapping — not modified  
- Issue #26 MPREM — not modified  
- QuikLoan field mapping formulas (balance/interest/dates) — unchanged except latest-row selection  

---

## G6 gate: **PASS**

**Next:** Closure Agent (G7) — resolution summary + commit/push.
