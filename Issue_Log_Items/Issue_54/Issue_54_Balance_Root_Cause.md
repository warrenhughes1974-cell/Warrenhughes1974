# Issue #54 — Balance Column Root Cause (UAT dig)

**Date:** 2026-07-14  
**Policy:** `010822238C` / `9010822238`  
**Status:** Root cause confirmed — fix requires Development (side-aware 0412)

---

## Symptom

Loan History grid loads (seed + PACTG), footer **Current Balance $9,731.08** is correct, but **Balance** on first row is **−$77,560.45** instead of **$8,373.99**.

---

## How QLAdmin computes Balance

Balance is **not stored** in QuikBenh. UI formula (proven on this policy):

> **Balance after row *i* = QuikLoan Current Balance − sum(effects of all later rows)**  
> Effect: MBENTYP **10/11 = +Amount**, **12 = −Amount**

So Balance is reconciled **backward from Current Balance**, not forward from 0.  
For the first row’s Balance to equal the seed **$8,373.99**, the net of all later Type/Amount effects must equal **$9,731.08 − $8,373.99 = $1,357.09**.

---

## Root cause

We emit every PACTG **0412** as MBENTYP **11** (Interest Added) with **absolute** amount — both when 0412 is on the **debit** side and when it is on the **credit** side.

| PACTG pattern (example 2018-01-22) | LifePRO meaning | Correct balance effect | What we emit today |
|------------------------------------|-----------------|------------------------|--------------------|
| Debit **0412** / Credit 0451 | Interest capitalized onto loan | **+** $647.05 | Type 11 +$647.05 ✓ |
| Credit **0412** / Debit 0451 | Interest taken off loan (offset) | **−** $656.84 | Type 11 +$656.84 ✗ |
| Credit **0413** | Loan payment | **−** $125.00 | Type 12 −$125.00 ✓ |

PLOAN same day: **−656.84**, **−125.00**, **+647.05** — matches side-aware PACTG, not abs-0412 emit.

### Proof on `010822238C`

| Ledger | Ending balance |
|--------|---------------:|
| Seed $8,373.99 + **side-aware** PACTG (debit +, credit −) | **$9,731.08** (exact QuikLoan) |
| Seed + current abs emit (all 0412 as +) | **$95,665.52** (gap ~$85,934) |

That gap is exactly why early Balance goes largely negative under the backward formula.

### Fleet (556 seed policies ∩ QuikLoan)

| Method | Closes to QuikLoan (±$0.02) |
|--------|----------------------------:|
| Side-aware debit/credit on 0411/0412/0413 | **213 / 238** |
| Map CREDIT 0412 → type 12 (same math) | **210 / 238** |

---

## Why seed alone did not fix Balance

Option 1 seed correctly supplies mid-stream opening **Amount**.  
QLAdmin still backs Balance from Current Balance through **every later row**.  
If later rows overstate interest (CREDIT 0412 treated as +), early Balance stays largely negative — seed row included.

---

## Recommended fix (Development)

1. When emitting PACTG loan codes, determine whether the loan code is on **DEBIT** or **CREDIT**.  
2. **DEBIT 0411/0412** → MBENTYP 10/11 (increase).  
3. **CREDIT 0413** → MBENTYP 12 (decrease) — unchanged.  
4. **CREDIT 0412** → must **decrease** Balance:
   - **Preferred for math:** emit as MBENTYP **12** (same as payment), *or*  
   - Confirm with Eric/New Era if another MBENTYP means “interest credit / reversal” (label accuracy).  
5. Re-validate `010822238C`: first Balance ≈ **$8,373.99**; chain nets to **$9,731.08**.  
6. Re-stage `quikbenh.csv` → Append Tool → `Q:\CSO\CSO_Test`.

**Do not change QuikLoan.** Footer stays #32/#44.

---

## UAT expectation after fix

| Row | Transaction | Date | Amount | Balance (expected) |
|-----|-------------|------|-------:|-------------------:|
| 1 | Loans Granted (seed) | 12/20/2017 | 8,373.99 | **≈ 8,373.99** |
| 2 | Interest Added | 01/15/2018 | 669.20 | ≈ 9,043.19 |
| … | … | … | … | … |
| Footer | Current Balance | | | **9,731.08** |

---

## Related artifacts

- Emit: `QLA_Migration/Output/quikbenh.csv`  
- This note: `Issue_54_Balance_Root_Cause.md`
