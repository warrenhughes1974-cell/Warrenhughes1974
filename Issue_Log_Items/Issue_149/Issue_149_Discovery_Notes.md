# Issue #149 — Discovery Notes (Search & Discuss)

**Issue:** #149 — Single Premium Not Pulling  
**Date:** 2026-08-18  
**Framework stage:** Stage 0 Discovery (G-D)  
**Code:** None  

---

## Client ask (verbatim)

On the evaluation comparison, single premium policies are not pulling in (units / values). Eric flagged the group at the end of the units discussion and said he would look at them.

---

## Verdict

Logged as its own issue so it is not lost inside the ISWL vanish/unit work.

The call did not lock policy numbers, the blank field, or the plan list. Conversion already has a single-premium plan list (`QLA_Migration/Configs/single_premium_plans.csv`) and Issue A single-prem rules (Prem Years = 1; S/Q/M mode factors = 0.00). This may be a conversion gap, a valuation-file join, or a plan that is not on the SP list.

Do not change SP plan setup until the Teams list says what is blank.

---

## Related issues

| Issue | Relationship |
|---|---|
| **Issue A / A1** | Single prem plan-setup checks. Different from “not pulling.” |
| **#148 / #150** | Same call, other “not pulling” groups. |

---

## Proposed work list (Planning will refine)

1. Get the Teams comparison rows labeled single premium.
2. Name the blank target (MUNIT, MPREM, MMODEPREM, Val X, other).
3. Match those plans to `single_premium_plans.csv`.

---

## Open questions

1. Which policies / plans?
2. Units blank, premium blank, or both?
3. Is this conversion Output or only the evaluation file?

---

## Stop

Discovery complete. Awaiting **Proceed to Intake**.
