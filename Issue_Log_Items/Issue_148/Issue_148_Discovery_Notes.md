# Issue #148 — Discovery Notes (Search & Discuss)

**Issue:** #148 — L10 Units (0777L)  
**Date:** 2026-08-18  
**Framework stage:** Stage 0 Discovery (G-D)  
**Code:** None  

---

## Client ask (verbatim)

Policy **9011284087** (company president — get this one right). QLAdmin shows 100 units / $100,000. LifePRO comparison shows 100 units as “not applicable.” Group **0777L** Central States Omaha Life. Product discussed as L10 / 1L1095 family. Only one of that product pulled in like this; other L10s matched or had rounding.

---

## Verdict

This is a **one-policy / one-product** unit question, not the vanish or RPU unit workstreams.

Repo traces already know the policy (Issue 47 status extract: 9011284087 / 011284087C, status 22, issue 2023-02-01). Conversion currently emits 100 units. The comparison “not applicable” needs a LifePRO field lock before any remap.

Do not fold this into #143 or #146.

---

## Related issues

| Issue | Relationship |
|---|---|
| **#107 1L1095 RV source** | L10 rate-source research. Not units. |
| **#143 / #146 / #147** | Other unit workstreams. Different cause. |

---

## Proposed work list (Planning will refine)

1. Trace 9011284087 on PPBEN / PPBENTYP: NUMBER_OF_UNITS, VALUE_PER_UNIT, current DB, plan/group 0777L.
2. Compare Output quikmstr / quikridr MUNIT and Amount Ins.
3. Confirm whether any other 0777L / L10 row is actually off (Eric said the rest matched or rounding).

---

## Open questions

1. What LifePRO field is “not applicable” — units, gender, or a rate key?
2. Is 0777L a group number, a plan, or a billing group?
3. Are there two L10 outliers (Eric: “two of them that don’t”) or only this one plus a zero that “makes sense”?

---

## Stop

Discovery complete. Awaiting **Proceed to Intake**.
