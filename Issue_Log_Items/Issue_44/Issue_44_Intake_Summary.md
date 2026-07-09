# Issue #44 — Intake Summary

**Issue:** #44 — ETI/RPU QuikLoan Balance Clear (stale PLOAN latest-row)  
**Date:** 2026-07-09  
**Framework stage:** Intake complete (G0)  
**Status:** Approved → Planning  
**Owner:** Conversion (Warren) · **Assigned:** Warren  
**Business status:** No-Go for Development until G1 + G2 + G3  

---

## 1. Client / business symptom (verbatim + normalized)

**BA report (verbatim):**

> FYI just saw a few policies on ETI that have a loan balance. Loan balance should be cleared on policies that are in RPU or ETI.

**Normalized:**

Policies with QLAdmin status **ETI (`MSTATUS`/`MPHSTAT` = 44)** or **RPU (45)** are showing a non-zero **`quikloan.MLOANBAL`**. Business expectation: loan balance should be **cleared** once the contract is on ETI or RPU.

**What the BA sees (screenshot sample):**

| MPOLICY | MSTATUS | MPLAN | MPHASE | MPHSTAT | MLOANBAL |
|---------|---------|-------|--------|---------|----------|
| 010391876C | 44 | 170858 | 1 | 44 | 1544.26 |
| 010404602C | 44 | 17085M | 1 | 44 | 1088.59 |
| 010456751C | 44 | 170858 | 1 | 44 | 534.89 |
| 010510671C | 44 | 2665ST | 1 | 44 | 7050.43 |
| 010525250C | 44 | 17085M | 1 | 44 | 1401.12 |
| 011226579C | 44 | 1L1095 | 1 | 44 | 1236.48 |

All six are **ETI** (not RPU). Fleet scan of current `Output/quikloan.csv`: **6 ETI** with `MLOANBAL > 0`; **0 RPU**.

---

## 2. Suspected domain

| Layer | Table / path | Role |
|-------|--------------|------|
| Policy status | `quikmstr.MSTATUS` / `quikridr.MPHSTAT` | 44 = ETI (`PUT_ET`); 45 = RPU (`PUT_RU` / `P_RPU`) |
| Loan emit | `quikloan.MLOANBAL` | From `PLOAN.LOAN_BALANCE` (Issue #32) |
| Source | `PLOAN_LoanInformation_Extract_*.csv` | Loan history; latest row per policy |
| Converter | `qla_core/quikloan_converter.py` → `select_latest_ploan_row_per_policy` | Picks which PLOAN row becomes QuikLoan |

**Domain:** Policy loan conversion (QuikLoan) — **not** product setup / `quikplan.LOANINT`.

---

## 3. Intake evidence (already measured — Planning will formalize)

### 3.1 Status authority (sample)

All six sample policies: `PPOLC.PAID_UP_TYPE = ET`, `CONTRACT_CODE = A` → composite `PUT_ET` → **MSTATUS 44**. `MNFOPT = 2` (ETI). Status mapping is **correct**.

### 3.2 LifePRO loan vs QuikLoan

| Policy | Latest PLOAN balance (correct sort) | PPOLC `TOTAL_LOAN_COUNT` | Emitted `MLOANBAL` |
|--------|-------------------------------------|-------------------------|--------------------|
| 010391876C | **0.00** (clear exists) | 0 | 1544.26 |
| 010404602C | **0.00** | 0 | 1088.59 |
| 010456751C | **0.00** | 0 | 534.89 |
| 010510671C | **0.00** | 0 | 7050.43 |
| 010525250C | **0.00** | 0 | 1401.12 |
| 011226579C | **1236.48 still open** | 0 | 1236.48 |

### 3.3 Suspected root cause (intake — not yet Planning-approved)

PLOAN often has **same-day twin rows**: non-zero balance then `.00` clear, differing by **1 second** on `LAST_CHG_TIME` (HHMMSS).

`select_latest_ploan_row_per_policy` sorts by `ACCRUAL_DATE` → `LAST_CHG_DATE` → `LAST_CHG_TIME`.  
`LAST_CHG_TIME` is sometimes passed through `parse_ploan_date`, which mis-parses HHMMSS (e.g. `212541` → fake date; `212540` → NaT). The **clear loses the tie-break** and the pre-clear balance is emitted.

**Pilot fix impact (string time sort):** ~**30** policies fleet-wide flip from non-zero → zero latest balance, including 5 of 6 BA samples. **011226579C** remains non-zero in source.

---

## 4. In scope / out of scope (first pass)

### In scope

- Correct **latest PLOAN row selection** so zero-balance clears win when they are chronologically later.
- Re-emit / validate QuikLoan for BA sample policies and fleet delta.
- Document whether an additional **status-based suppress** (ETI/RPU → no QuikLoan row / zero balance) is required when PLOAN still shows open balance.

### Out of scope (unless Planning expands)

- Changing ETI/RPU **status** mapping (`MSTATUS` 44/45) — already correct.
- `quikplan.LOANINT` product-setup enrichment (separate, already shipped v57.58).
- Inventing loan clears not present in PLOAN without BA/client rule confirmation.
- QuikPlSt state loan overrides.

---

## 5. Related issues

| Issue | Relationship |
|-------|----------------|
| **#32** | Parent QuikLoan / PLOAN mapping — this is a **defect in latest-row selection**, not a new table |
| **#13** | MSTATUS / `PAID_UP_TYPE` precedence — status path is OK; do not regress |
| Product LOANINT (v57.58) | Plan-level interest only — unrelated to policy `MLOANBAL` |

---

## 6. Artifact inventory

| Artifact | Status |
|----------|--------|
| BA screenshot (6 ETI + loan) | Provided |
| Sample policy list | Provided |
| PLOAN extract `..._20260630.csv` | Present in `QLA_Migration/Source/` |
| PPOLC extract (PAID_UP_TYPE / TOTAL_LOAN_COUNT) | Present |
| Current `Output/quikloan.csv` | Present (shows defect) |
| Client written rule: “always clear on ETI/RPU even if PLOAN open” | **Missing** — needed for 011226579C path |
| LifePRO UI screenshot of loan screen for sample | Optional / preferred |

---

## 7. Immediate blockers visible at intake

| Blocker | Blocks? | Notes |
|---------|---------|-------|
| Source extracts | No | PLOAN + PPOLC available |
| Field definitions | No | MLOANBAL = LOAN_BALANCE already approved (#32) |
| Sort-bug fix design | No for Planning | Evidence strong enough to plan |
| Client rule for open PLOAN on ETI (011226579C) | **Yes for full BA rule** | May be Conditional-Go: fix sort first; status-suppress as Phase B |

---

## 8. Severity / owner / priority

| Field | Value |
|-------|--------|
| Severity | **High** — incorrect loan liability on ETI policies in UAT |
| Owner | Conversion |
| Priority (Go/No-Go) | **Conditional Go** expected after Planning/Risk — sort fix is conversion-owned; status-suppress may need BA confirm |
| Recommended next status | **Planning** |

---

## 9. Gate G0 checklist

- [x] Issue folder created: `Issue_Log_Items/Issue_44/`
- [x] Intake summary written
- [x] Example policies listed
- [x] Owner and priority assigned
- [x] No code or rulebook changes made

---

## 10. Recommended next stage

**Planning Agent** — document:

1. Exact fix to `select_latest_ploan_row_per_policy` (HHMMSS as string / numeric time, never `parse_ploan_date`).
2. Emit rule interaction with `emit_zero_balance_loans=false` (zero latest → hold / no QuikLoan row).
3. Open question: suppress QuikLoan when `MSTATUS` in (44, 45) even if PLOAN latest ≠ 0?
4. Validation plan: BA 6 policies + fleet of ~30 flipped policies + regression on non-ETI loans.
