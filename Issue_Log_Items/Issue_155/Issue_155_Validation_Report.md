# Issue 155 — Validation Report

**Stage:** 6 — Validation  
**Date:** 2026-09-24  
**Verdict:** PASS  
**Valuation date:** 20260630  
**Environment:** `Q:\CSO\CSO_Test_6_30_2026` after anniversary through 6/30 and valuation at 6/30  
**Output under test:** `QLA_Migration/Output/QuikIswl.csv` (545,150 rows, 2,244 policies) loaded to `QuikIswl.dbf`

## What was proven

LifePRO fund balance against the last QLAdmin history row that has an amount, and against QuikValf phase-1 account value (`MACCTBAL`) on ISWL plans.

| Check | Result |
|---|---|
| History account value matches LifePRO | 2,199 of 2,326 LifePRO fund policies |
| History differs | 45 — anniversary wrote one newer month than LifePRO's snapshot |
| No QLAdmin history row | 82 |
| Negative LifePRO funds loaded as 0.00 | 247 |
| Valuation account matches LifePRO | 1,216 |
| Value per unit on those matches | $1,000.00 |
| Valuation account differs | 40 |
| No phase-1 ISWL valuation row | 1,069 (1,034 are QuikValf extension Z, loan or dividend only; 35 are plan A1E11668SP) |

## Trace policies

| Policy | LifePRO account | QLAdmin account | Valuation account | Value per unit |
|---|---:|---:|---:|---:|
| 9010713704C | 45,551.94 at 20260619 | 45,551.94 | 45,551.94 | 1,000.00 |
| 9010713705C | 26,251.74 at 20260619 | 26,251.74 | 26,251.74 | 1,000.00 |
| 9010713707C | 8,146.88 at 20260619 | 8,146.88 | 8,146.88 | 1,000.00 |

Prior comparison (2026-09-02) had ISWL reserves about $5.2 million higher in QLAdmin than LifePRO. On this run, where both reserves are present, QLAdmin is about $84,000 higher on $17.6 million. 9010779727C moved from a QLAdmin reserve of $190,500 against LifePRO $128,000 to $127,250 against the same $128,000.

## Commands

- `python tools/validators/validate_issue155_iswl_seed.py` with `QLA_VALUATION_DATE=20260630` — PASS (545,150 rows, 0 month-0 rows, 0 policies whose last loaded balance missed LifePRO, gold traces pass).
- Q anniversary and valuation compared in `Issue_155_630_QLAdmin_vs_LifePRO.txt` and `Issue_155_630_Account_Value_Simple.txt`.

## Documented exceptions (do not block this PASS)

- **9010801730C** is active, premium paying, LifePRO fund $11,799.87, and has no history row because the LifePRO snapshot date is 20260709. Valuation account is $0.00. Warren chose to test first and fix after. This remains open before Closure.
- Reserve method is unchanged as a product rule: LifePRO `RV_MEAN_RV` is net level; QLAdmin `MRESERVE` is CRVM. The dollar gap collapsed because the account value is now LifePRO's.
- #160 release smoke still fails only on a missing archive snapshot from 2026-09-13. Every other release smoke run after the history rebuild passed.

## Gate G5

Trace policies pass. Validator exits 0. Report published. Status moves to Ready for Regression.
