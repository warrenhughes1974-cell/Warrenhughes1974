# Issue #32 — Policy Loan Open Questions

**Issue:** #32 — Policy Loan Conversion  
**Generated:** 2026-06-29  
**Status:** Awaiting SME / BA confirmation  
**Blocks:** Production QuikLoan emit and default batch integration

---

## Summary

| # | Question | Priority | Staging default | SME owner |
|---|----------|----------|-----------------|-----------|
| 1 | STATUS_CODE emit filter | **High** | No filter (date-driven) | LifePRO / BA |
| 2 | Zero-balance loans | **High** | Exclude (528 held) | BA / Operations |
| 3 | Closed loans | **High** | Implicit via zero balance | BA |
| 4 | MLOANPRIN definition | **Critical** | = LOAN_BALANCE | BA / QLAdmin SME |
| 5 | MLOANIDT source | **High** | LAST_REPAY → CAPITALIZED | BA |
| 6 | MLOANDATE source | **Medium** | ACCRUAL_DATE | BA |
| 7 | INTEREST_TYPE → MLOANINTX | **Critical** | Blank | BA / Product |
| 8 | Special class fields | **Low** | Ignored (all zero) | Product |
| 9 | MLOANBILL source | **Medium** | 0.00 | Billing / BA |
| 10 | Multiple rows per policy | **Resolved** | Latest snapshot | — |

---

## Q1 — Which STATUS_CODE values should convert?

### Evidence

| STATUS (latest row) | All policies | Non-zero balance |
|--------------------|-------------:|-----------------:|
| H (history) | 576 | 57 |
| A (active) | 240 | 240 |
| R (repaid-related) | 97 | 88 |

Staging selects by **date**, not STATUS. Non-zero loans with latest STATUS `H` (57 policies) would emit under current rules.

### Question

Should emit require STATUS `A` only? Should `H` with non-zero balance be included? What does STATUS `R` mean for an outstanding balance?

### Options

| Option | Effect |
|--------|--------|
| A — No STATUS filter (current) | 385 active candidates |
| B — STATUS = A only | ~240 candidates (estimate) |
| C — STATUS in (A, R) | ~328 candidates (estimate) |

---

## Q2 — Should zero-balance loans be converted?

### Evidence

- 528 policies have latest `LOAN_BALANCE = 0`  
- Staging holds all with `ZERO_BALANCE_HELD`  
- Many retain `INTEREST_RATE` and dates — loan history exists  

### Question

Does QLAdmin require a QuikLoan row for paid-off loans (for history/display), or only outstanding balances?

### Options

| Option | Emit count |
|--------|----------:|
| Exclude zero balance (current) | 384 |
| Include zero balance | ~912 (minus date blocks) |

---

## Q3 — Should closed loans be excluded?

### Evidence

Zero-balance latest rows correlate with STATUS `H` (576) and blank `TYPE_CODE` (351).

### Question

Is "closed loan" defined by zero balance, STATUS code, or a policy status on PPOLC/quikmstr?

### Dependency

Answer may subsume Q2. Confirm against policy master status if available.

---

## Q4 — What should MLOANPRIN represent?

### Evidence

- Staging: `MLOANPRIN = LOAN_BALANCE`  
- `ORIG_LOAN_AMOUNT` on latest row = row-open principal, not inception principal  
- `ORIG + LOAN_AMT_ADDED = LOAN_BALANCE` on 100% of latest rows  
- QLAdmin Help: "Loan principal" — semantic definition needed  

### Question

Which LifePRO value populates QLAdmin Loan Principal?

| Candidate | Description |
|-----------|-------------|
| A | `LOAN_BALANCE` (current outstanding) |
| B | `ORIG_LOAN_AMOUNT` on latest row |
| C | `ORIG_LOAN_AMOUNT` on first PLOAN history row |
| D | `LOAN_BALANCE − ACCRUED_INT_AMT` (equals balance today) |
| E | Other LifePRO field |

**Impact:** Financial display on QLAdmin loan screen; principal vs balance reporting.

---

## Q5 — What LifePRO value should populate MLOANIDT (interest paid-to date)?

### Evidence

- Staging precedence: `LAST_REPAY_DATE` → `CAPITALIZED_DATE`  
- 118 latest rows missing `LAST_REPAY_DATE`; 586 missing `CAPITALIZED_DATE`  
- **12 emit candidates** have blank `MLOANIDT` with non-zero balance  

### Question

What date should QLAdmin show as "interest paid-to"?

| Candidate | Notes |
|-----------|-------|
| LAST_REPAY_DATE | 12 active loans lack it |
| CAPITALIZED_DATE | Often zero on non-capitalizing rows |
| INT_START_DATE | Always populated on sample — fallback candidate? |
| ACCRUAL_DATE | Duplicates MLOANDATE |
| Blank acceptable | 12 rows — validate in QLAdmin UI |

---

## Q6 — What LifePRO value should populate MLOANDATE (loan balance date)?

### Evidence

- Staging: `ACCRUAL_DATE`  
- 1 policy blocked: blank `ACCRUAL_DATE` with $621.78 balance  
- Future outlier dates exist (max 2218-01-11)  

### Question

Is accrual date the correct "loan balance as-of" date, or should `INT_START_DATE` / `LAST_CHG_DATE` be used?

---

## Q7 — How should INTEREST_TYPE map to MLOANINTX (A/R)?

### Evidence

- 100% of policies: `INTEREST_TYPE = F` (fixed)  
- 100% of policies: `INT_METHOD = D` (daily)  
- QLAdmin expects `A` (advance) or `R` (arrears)  
- Staging leaves `MLOANINTX` blank  

### Question

For fixed-rate LifePRO loans, what should QLAdmin `MLOANINTX` be?

| Option | Action |
|--------|--------|
| A | Leave blank |
| B | Default from QuikPlan `LOANINTX` by plan |
| C | Map F → A or F → R per product rule |
| D | Default `R` (arrears) fleet-wide |

**Also:** Confirm `MLOANINT` scale — `.0500` → `0.05` vs `5.00`.

---

## Q8 — Should special class loan fields be included or ignored?

### Evidence

All zero in extract:

- `SPEC_CLS_LOAN_BAL`
- `SPEC_CLS_INT_RATE`
- `SPEC_CLS_CAPD_AMT`
- `SPEC_CLS_LOAN_CHNG`

No QuikLoan target fields exist.

### Question

Are special-class loans expected in this block of business? If yes, is a different extract or table required?

---

## Q9 — Should loan billing payment (MLOANBILL) be populated?

### Evidence

- No PLOAN column maps to billing payment  
- Staging default: `0.00`  
- QLAdmin Help references MLOANBILL on loan screen  

### Question

Is `MLOANBILL` required at conversion?

| Source candidate | Feasibility |
|------------------|-------------|
| PACTG 0413 payment amount | Transaction — not snapshot |
| LifePRO billing extract | Not in current ZIP |
| QLAdmin post-load billing | Zero at conversion acceptable? |

---

## Q10 — How should multiple loan rows for the same policy be handled?

### Status: **Resolved for planning**

| Finding | Decision |
|---------|----------|
| 913/913 policies have multiple PLOAN rows | History table — not duplicates |
| QuikLoan keyed on MPOLICY | One row per policy |
| Proposed rule | Latest snapshot by ACCRUAL_DATE + LAST_CHG_DATE + LAST_CHG_TIME |

### Residual question

Does any policy have **multiple concurrent loans** (not history)? Profile shows single balance thread per policy — no evidence of concurrent loans. **Confirm with SME.**

---

## Additional Data Quality Questions

| ID | Question |
|----|----------|
| DQ1 | Policy `9011190668` — active balance but blank ACCRUAL_DATE — correct in LifePRO or extract defect? |
| DQ2 | ACCRUAL_DATE max 2218-01-11 — valid or corrupt? |
| DQ3 | Is PLOAN-only authority acceptable when PACTG loan transactions exist separately? |
| DQ4 | Is snapshot-only QuikLoan sufficient, or is loan **history** table load required later? |

---

## Decision Gate Checklist

Before Development Agent proceeds, SME must sign off:

- [ ] Q4 — MLOANPRIN definition  
- [ ] Q7 — MLOANINT scale + MLOANINTX rule  
- [ ] Q2/Q3 — Zero-balance and closed-loan emit policy  
- [ ] Q1 — STATUS_CODE filter (if any)  
- [ ] Q5 — MLOANIDT fallback for blank cases  
- [ ] Q9 — MLOANBILL required or defer  
- [ ] DQ1–DQ4 — Data quality disposition  

---

## Recommended SME Session Agenda

1. Review 3 sample traces: active (`9010331768`), zero-balance paid (`9010300689`), blank-IDT (`9010381745`)  
2. Walk QLAdmin loan screen field definitions (Help p.827-828)  
3. Confirm emit scope: 384 vs 912 policies  
4. Document signed mapping sheet → update `quikloan_derivation_rules.json`  

---

**Route:** Dependency Gate Agent — collect written answers → Ownership Decision → Development (if PASS).
