# Issue #146 — Discovery Notes (Search & Discuss)

**Issue:** #146 — Non-VB Unit Reductions  
**Date:** 2026-08-18  
**Framework stage:** Stage 0 Discovery (G-D)  
**Code:** None  

---

## Client ask (verbatim)

After vanish is flipped for the VB book (#145), what do we do with the leftover policies where QLAdmin / QuikIsrr anniversary processing still reduces units for PACT 0561 “withdrawals,” but LifePRO never reduced the unit field?

---

## Verdict

This is the **exception book after #145**, not a second vanish emit.

QLAdmin anniversary processing loads original units, brings PACT 0561 history into QuikIsrr (plus matching claim-payment rows), and subtracts those amounts from face (units × $1000). LifePRO often keeps the original unit count and stores the 0561 as accounting only.

On the 8/18 call Eric concluded most of those 0561 rows on **VB** policies are **internal vanish premium deductions**, not true partial surrenders. #145 is the fix for that population.

#146 is only policies that still drop units **and are not VB**. #145 Discovery already counted about **50** 0561 policies that are not VB, including **9010761639** and **9010760840**.

Do **not** delete 0561 history to force units back to 25. Anniversary processing will recalculate from history every run.

---

## How the unit drop happens (call)

1. Conversion loads original units (example: 25 = $25,000 at $1000/unit).
2. QuikIsrr receives PACTG / PACT debit **0561** (partial withdrawal) plus matching claim-payment history.
3. Anniversary processing: new face = original face − 0561 amount; new units = new face / 1000.

Call examples (pattern; first two may be VB and belong to #145, not this leftover):

| Pattern | LifePRO units | QLAdmin units | 0561 |
|---|---:|---:|---|
| One 0561 | 25 | 24.729 | $271 posted 09/04/2018 |
| One 0561 | 25 | 24.864 | $136 |
| 9010815236 (VB — #145) | original | 25,000 − ~$1,532 | 8 non-reversed 0561s totaling $1,402.56; 9th reversed and not brought over |

---

## Related issues

| Issue | Relationship |
|---|---|
| **#145 Vanish Flag (VB)** | Fixes the vanish majority. Do not set VANISH=TRUE here. |
| **#34 QuikIsrr** | 0561 is the locked QuikIsrr source. Do not reopen the 0561 emit rule. |
| **#22 Vanish Option** | Research / New Era. Not the leftover non-VB unit rule. |
| **#143 Units Incorrect (RPU)** | Closed. Different population (BF RPU vs current DB). See #147. |

---

## Proposed work list (Planning will refine)

1. Take Eric’s Teams comparison list and split VB (#145) vs non-VB leftover.
2. Confirm 9010761639 and 9010760840 (and any others) against PPOLC BILLING_REASON and PACT 0561.
3. SME rule: keep LifePRO units, or honor 0561 as a true partial surrender.
4. Do not invent a vanish flag for blank billing reason.

---

## Open questions

1. Are the leftover 0561s legitimate partial surrenders (units should drop) or LifePRO data mistakes (units should stay)?
2. Where is the full exception list from the Teams file?
3. If units must stay at 25, what anniversary-safe method exists besides deleting history?

---

## Stop

Discovery complete. Awaiting **Proceed to Intake**.
