# Issue #104 — Intake Summary

**Issue:** #104 — Loan Handling (claim/surrender loan payoff interest)  
**Date:** 2026-07-24  
**Framework stage:** Intake complete (G0)  
**Status:** Proceed to Planning  
**Owner:** Conversion (Warren) + Client/SME (interest authority at payout)  
**Business status:** No-Go (Eric 7/23/2026) — client blocker

---

## Client / business symptom (verbatim)

> The loans are being handled differently in the systems when paying claim and surrender. For example in QLAdmin for policy 010331768C, the loan principal balance is $3,707.11 and accrued interest of $194.01 is being added for a total loan of $3,901.12 at payout whereas LifePRO has a loan principal balance of $3707.11, however it is removing $18.19 in interest for a total loan of $3,688.92 at payoff.

---

## Normalized finding

At **claim/surrender payout**, QLAdmin and LifePRO agree on **loan principal** ($3,707.11) but apply **opposite interest treatment**:

| System | Principal | Interest | Payoff / payout loan total |
|--------|----------:|---------:|---------------------------:|
| **LifePRO** | 3,707.11 | **−18.19** (unearned / advance) | **3,688.92** |
| **QLAdmin** | 3,707.11 | **+194.01** (accrued) | **3,901.12** |

Delta between systems: **$212.20** (= 194.01 + 18.19).

Policy identity:

| Form | Value |
|------|-------|
| Client citation | `010331768C` |
| LifePRO source | `9010331768` |
| Current Output MPOLICY (#2) | `9010331768C` |

Current converter emit (`QLA_Migration/Output/quikloan.csv`):

```text
9010331768C,3707.11,3707.11,5.00,A,20250725,20250725,0.00,0.00
```

That matches the **approved Issue #32** design: gross `LOAN_BALANCE` into `MLOANPRIN`/`MLOANBAL`, `MLOANACCR=0`, `MLOANINTX=A`, dates from `ACCRUAL_DATE`. #32 UAT expected QLAdmin to calculate ~**$18.19 advance unearned** (subtract). Client now reports QLAdmin **adding $194.01** at payout — opposite sign and different magnitude.

---

## Example policies

| Client ID | Output MPOLICY | Plan | Role |
|-----------|----------------|------|------|
| 010331768C | 9010331768C | 1960PO | Primary trace (same as #32 / #54) |

No additional policies supplied. Fleet impact TBD in Planning/Risk after fix path is chosen.

---

## Suspected domain

**Policy loan settlement math — `quikloan` + QuikPlan loan interest setup (`LOANINT` / `LOANINTX`) + QLAdmin runtime accrual at claim/surrender.**

Not primarily QuikBenh loan history (#54 already closed for this policy). Not `quikclms`/`quikclmp` for this policy (no claim CSV rows; 0412 pseudo-surrenders correctly held as loan accounting).

---

## Related issues

| Issue | Relationship |
|-------|--------------|
| **#32** | Same policy; approved QuikLoan mapping (gross + MLOANACCR=0 + INTX=A). UAT required ~18.19 advance. **#104 may be failed #32 UAT at payout.** |
| **#44** | QuikLoan latest-row sort — closed; not the interest-sign defect |
| **#54** | Loan History via QuikBenh — closed; footer balance closes to QuikLoan gross |
| **#70** | Fleet QuikPlan `LOANINTX` → `A`; still awaiting CSO list of any true Arrears (`R`) plans |
| **#2** | MPOLICY form `9010331768C` vs client `010331768C` |
| Claims Item 14 / 18 | Loan accounting ≠ surrender claims; death amount includes loan — separate from QuikLoan interest calc |

---

## In scope / out of scope (first pass)

| In scope | Out of scope |
|----------|--------------|
| Align claim/surrender **loan payoff total** with LifePRO for UAT policies | Recalculating LifePRO loan history |
| Diagnose why QLAdmin adds interest while LifePRO subtracts unearned | Changing QuikBenh history grain (#54) unless proven coupled |
| QuikLoan / QuikPlan loan interest fields if conversion is root cause | Emitting held 0412 loan-accounting rows as surrenders |
| SME lock: acceptance target + whether #32 MLOANACCR=0 rule reopens | #25/#26 premium/MPOLICY paths |

---

## Immediate blockers visible at intake

1. **Root cause not yet classified:** conversion load vs QLAdmin runtime/config vs plan `LOANINTX` semantics at payout.
2. **#32 business rule conflict:** approved “QLAdmin calculates; do not load UI interest” may be producing the wrong sign/magnitude at settlement.
3. **Acceptance target** for claim/surrender must be confirmed as LifePRO **$3,688.92** (vs some other QLAdmin convention).

---

## Artifact inventory

| Provided | Missing |
|----------|---------|
| Symptom + dollar proof on one policy | Screenshots of QLAdmin claim/surrender loan panel showing +194.01 |
| LifePRO side already evidenced in #32 (Principal / Interest 18.19 / Balance 3688.92) | Explicit SME: reopen #32 load rule vs fix QLAdmin calc only |
| Measurable before-state in `quikloan.csv` | Second/third policies if fleet-wide |
| Related #32/#54/#70 docs in repo | Payout as-of date used in QLAdmin for the $194.01 calc |

---

## Severity / owner

| Item | Value |
|------|-------|
| Severity | **High** — money at claim/surrender payout; client No-Go |
| Owner | Conversion + Client/SME |
| Priority | **No-Go** (Eric) |
| Recommended tracking status | **Intake → Planning** (Pre-Dev chain) |
