# Issue #70 — Intake Summary

**Issue:** #70 — QuikPlan `LOANINTX` Advance/Arrears authority (CSO guidance needed)  
**Framework stage:** Intake Agent (G0)  
**Status after intake:** Open — Awaiting CSO  
**Generated:** 2026-07-14  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Client / CSO (decision) · Conversion (emit once decided)  
**Priority:** Go-No Go — drives plan-file loan interest timing and QuikLoan `MLOANINTX`  
**Reporter chain:** Chris (invalid plan value) → conversion analysis 2026-07-14  

---

## Client symptom (normalized)

Chris reported QuikPlan `LOANINTX` cannot be `2` (invalid). QLAdmin accepts only **`A`** (Interest in Advance) or **`R`** (Interest in Arrears).

---

## Current conversion posture

- QuikPlan rulebook defaults `LOANINTX` to **`A`**.
- QuikLoan `MLOANINTX` looks up QuikPlan `LOANINTX`; if missing/invalid, falls back to **`A`**.
- **LifePRO extract does not supply Advance/Arrears.** PLOAN `INTEREST_TYPE=F` (Fixed) and `INT_METHOD=D` (daily) fleet-wide — not A/R codes. Product LN segment is loan **rate**, not timing.
- Sample LifePRO UI (policy `9010331768`) shows Interest Method = Advance, but that is UI/product semantics, not an extractable field in the delivered ZIP.
- Historical bad value `22` was a mistranslation of default `A` through status map `A→22` (Active), which truncates to `2` in a C(1) field — not a deliberate A/R code.

**Interim:** conversion is setting (or correcting to) **`A` for all plans** so the plan file loads. **CSO guidance is required** before treating that as final product truth (especially if any plans should be Arrears / `R`).

---

## Example policies / evidence

| Item | Reference |
|------|-----------|
| Sample UI Advance | `9010331768` / `010331768C` (Issue #32 screenshot) |
| Prior analysis | `Issue_Log_Items/Issue_32/Issue_32_MLOANINTX_Source_Review.md` |
| Governance | `QLA_Migration/Data_Goverence.txt` — LOANINTX must be A or R, default A |
| Current Output | `QLA_Migration/Output/quikplan.csv` — LOANINTX = A (fleet) |

---

## In scope / out of scope (first pass)

| In scope | Out of scope |
|----------|----------------|
| Confirm fleet Advance vs any Arrears plans | Changing loan balances / QuikLoan principal math |
| Decide plan-level `LOANINTX` source of truth | Reopening Issue #32 balance rules |
| After CSO decision: emit correct A/R on QuikPlan (+ QuikLoan lookup) | Inventing Adv/Arr from PLOAN F/D |

---

## Related issues

- **#32** — QuikLoan mapping; documented LOANINTX fallback A and invalid staged `22`
- **#44** — QuikLoan latest-row selection (closed; unrelated to A/R)

---

## Immediate blockers

- No LifePRO extract field maps to `LOANINTX` A/R
- Need CSO confirmation: all plans Advance (`A`), or plan list for Arrears (`R`)

---

## Gate Criteria (G0 — Intake Complete)

- [x] Issue folder created under `Issue_Log_Items/Issue_70/`
- [x] Intake summary written
- [x] Example policies listed
- [x] Owner and priority assigned
- [x] No code or rulebook changes made
