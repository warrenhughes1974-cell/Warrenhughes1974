# Issue #32 — SME Questions Updated (Post-Screenshot)

**Issue:** #32 — Policy Loan Conversion  
**Prior version:** `Issue_32_Policy_Loan_Open_Questions.md` (2026-06-29)  
**Evidence added:** LifePRO screenshots — policy `9010331768`  
**Generated:** 2026-06-29

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | **Resolved** by screenshot + PLOAN trace |
| 🔶 | **Narrowed** — answer partially known; SME confirm fleet-wide |
| 🔴 | **Open** — still blocked |
| ➖ | **Unchanged** — no new evidence |

---

## Question Status Summary

| ID | Topic | Prior | Post-screenshot |
|----|-------|-------|-----------------|
| Q1 | STATUS_CODE filter | 🔴 | ➖ Open |
| Q2 | Zero-balance loans | 🔴 | ➖ Open |
| Q3 | Closed loans | 🔴 | ➖ Open |
| Q4 | MLOANPRIN definition | 🔴 | ✅ **LOAN_BALANCE** |
| Q5 | MLOANIDT source | 🔴 | 🔶 **ACCRUAL_DATE** (confirm) |
| Q6 | MLOANDATE source | 🔴 | ✅ **ACCRUAL_DATE** |
| Q7 | MLOANINT scale + MLOANINTX | 🔴 | 🔶 Scale ✅; INTX partial |
| Q8 | Special class fields | 🔴 | ➖ Open (still zero) |
| Q9 | MLOANBILL | 🔴 | ✅ Default **0.00** |
| Q10 | Multi-row handling | ✅ | ✅ Unchanged |
| **Q11** | **MLOANACCR source** | *(implicit in Q4/Q5)* | 🔴 **NEW CRITICAL** |
| **Q12** | **MLOANBAL net vs gross** | *(implicit)* | 🔴 **NEW CRITICAL** |
| **Q13** | **INT_METHOD meaning** | *(assumed daily)* | ✅ **Not A/R; reject for MLOANINTX** |

---

## ✅ Resolved Questions

### Q4 — MLOANPRIN (RESOLVED)

**Answer:** `MLOANPRIN ← LOAN_BALANCE` (latest snapshot).

**Evidence:** Screen Principal 3,707.11 = PLOAN `LOAN_BALANCE`. Not `ORIG_LOAN_AMOUNT` (3,522.25).

**SME action:** None required unless QLAdmin Help defines principal differently.

---

### Q6 — MLOANDATE (RESOLVED)

**Answer:** `MLOANDATE ← ACCRUAL_DATE`.

**Evidence:** Last Accrued Date 07/25/2025 = `ACCRUAL_DATE` 20250725.

---

### Q7a — MLOANINT scale (RESOLVED)

**Answer:** `MLOANINT = INTEREST_RATE × 100` → `.0500` loads as **5.00**.

**Evidence:** Screen 5.00000% vs PLOAN .0500.

**SME action:** Confirm QLAdmin N(5,2) displays 5.00 as 5% (not 500%).

---

### Q9 — MLOANBILL (RESOLVED — default)

**Answer:** Default **0.00**; no PLOAN or screenshot source.

---

### Q13 — INT_METHOD vs Advance (RESOLVED — negative)

**Answer:** `INT_METHOD = D` on **100%** of PLOAN rows. **Does not encode Advance/Arrears.** Do not use for `MLOANINTX`.

**Evidence:** Fleet profile + screenshot shows Advance under separate label from PLOAN `INT_METHOD`.

---

## 🔶 Narrowed Questions (SME Confirm)

### Q5 — MLOANIDT (NARROWED)

**Proposed answer:** `MLOANIDT ← ACCRUAL_DATE` (matches Last Accrued Date on trace policy).

**Also valid on trace:** `LAST_REPAY_DATE` and `CAPITALIZED_DATE` equal same date.

**Fleet caveat:** 109 active policies missing `LAST_REPAY_DATE` — ACCRUAL_DATE first in precedence reduces gaps.

**SME question:** Is Last Accrued Date the correct QLAdmin "interest paid-to" date fleet-wide?

---

### Q7b — MLOANINTX (NARROWED)

**Proposed answer:** `MLOANINTX = A` (Advance) via **config default**, not PLOAN column.

**Evidence:** Loan Quotes screenshot shows Interest Method = Advance.

**Rejected sources:**

- `INTEREST_TYPE = F` → Fixed rate label only  
- `INT_METHOD = D` → not A/R in extract  

**SME question:** Confirm **all** policies in scope use interest-in-advance. If mixed, provide plan-level rule.

---

## 🔴 Open Questions (Critical)

### Q11 — MLOANACCR source (NEW — CRITICAL)

**Problem:** LifePRO screen Interest = **18.19**; PLOAN `ACCRUED_INT_AMT = 0.00` on all rows.

**SME must answer:**

1. Does QLAdmin **recalculate** accrued interest when loan screen opens from MLOANPRIN + MLOANINT + MLOANINTX + dates?  
   - If **YES** → emit `MLOANACCR = 0.00` at conversion (Option A)  
   - If **NO** → provide formula or alternate LifePRO source (Option B)

2. What is the **as-of date** for interest calculation (extract date vs policy quote date)?

3. Is advance interest for ~36 days on trace policy consistent with product rules?

**Without answer:** Development cannot correctly populate MLOANACCR or net MLOANBAL.

---

### Q12 — MLOANBAL net vs gross (NEW — CRITICAL)

**Problem:** Screen Balance **3,688.92** ≠ `LOAN_BALANCE` **3,707.11**.

**Proven relationship:** Balance = Principal − Interest = 3,707.11 − 18.19.

**SME must answer:**

1. Should QuikLoan `MLOANBAL` store **net** balance (after accrued interest)?  
2. If yes, is net balance derived by QLAdmin or must converter calculate it?

**Dependency:** Q11.

---

## ➖ Unchanged Open Questions

### Q1 — STATUS_CODE filter

No screenshot evidence. 57 active policies have latest STATUS `H`.

**SME question unchanged:** Filter by STATUS or date-only selection?

---

### Q2 — Zero-balance loans

528 policies held. Screenshot is active loan only.

**SME question unchanged:** Emit paid-off loans?

---

### Q3 — Closed loan definition

**SME question unchanged:** Zero balance vs STATUS vs policy master?

---

### Q8 — Special class fields

Still zero fleet-wide.

**SME question unchanged:** Any product requiring SPEC_CLS_*?

---

## Data Quality (Unchanged)

| ID | Issue | Status |
|----|-------|--------|
| DQ1 | Policy 9011190668 blank ACCRUAL_DATE | Open |
| DQ2 | ACCRUAL_DATE outlier 2218 | Open |
| DQ3 | PLOAN-only vs PACTG | Open |
| DQ4 | Loan History future scope | Open |

---

## Updated Decision Checklist

Before Development:

- [x] MLOANINT scale — **5.00 percent**  
- [x] MLOANPRIN — **LOAN_BALANCE**  
- [x] MLOANDATE — **ACCRUAL_DATE**  
- [ ] **MLOANACCR — QLAdmin calc vs converter calc (Q11)** ← **primary blocker**  
- [ ] **MLOANBAL net formula (Q12)** ← **primary blocker**  
- [ ] MLOANINTX = A fleet-wide (Q7b)  
- [ ] MLOANIDT = ACCRUAL_DATE precedence (Q5)  
- [ ] Zero-balance / STATUS scope (Q1–Q3)  

---

## Recommended SME Wording (Copy/Paste)

> For policy 9010331768, LifePRO shows Principal 3,707.11 (= PLOAN LOAN_BALANCE), Interest 18.19 (not in PLOAN ACCRUED_INT_AMT), and Balance 3,688.92 (= Principal − Interest).  
>   
> **Please confirm:**  
> 1. Should QuikLoan MLOANACCR be loaded at conversion, or does QLAdmin calculate it from principal/rate/dates?  
> 2. Should MLOANBAL be net balance (3688.92) or gross LOAN_BALANCE (3707.11)?  
> 3. Is MLOANINTX = A (Advance) correct for all policies?  
> 4. Is Last Accrued Date (= PLOAN ACCRUAL_DATE) the correct MLOANIDT?

---

**Route:** Ownership Decision Agent after Q11/Q12 answered.
