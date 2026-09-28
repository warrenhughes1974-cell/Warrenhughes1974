# Issue 175 — Intake Summary

**Issue:** 175 — Res Cat Unique Field
**Framework stage:** Intake
**Date:** 2026-09-28
**Status recommendation:** Planning
**Owner:** Eric (business) / Warren (conversion)
**Priority:** No Go
**Code:** None

---

## Client symptom

Verbatim: The policies associated with products 1L15GD, 1L16GD and 1L17SP did not pull in the correct Res Cat. The categories should be 13, 13 and 12, respectively.

Normalized: On those three products, the policy reserve category should be 13, 13, and 12. Warren identified the spec field. Discovery confirmed that field is `quikspec.RESRVCAT`.

## Example policies

Client did not name policies. The current package identifies them by plan.

| Policy | Plan | Reserve category now | Requested |
|---|---|---|---|
| 9011210337C | 1L15GD | L | 13 |
| 9011216680C | 1L16GD | L | 13 |
| 9011217014C | 1L17SP | L | 12 |

Fleet: 11 + 2 + 20 = 33 policies. Population file: `evidence/issue175_resrvcat_population.csv`.

## Domain

Policy User Defined. Table `quikspec`. Field `RESRVCAT` (char 2), added by Issue 141.

## In scope

- `quikspec.RESRVCAT` on policies whose base coverage is L15, L16, or L17 BASE (plans 1L15GD, 1L16GD, 1L17SP).
- The Issue 141 check, so it accepts 13 / 13 / 12 on those coverages and still requires LifePRO product type everywhere else.

## Out of scope

- `quikplan.PRODUCT` (already 13, 13, and 12 on these plans).
- ISWL plan tags (`ISWLFE`).
- Other `quikspec` columns: vanish, vanish date, resident state, source policy number.
- Other reserve categories.
- Premium, units, status, and policy number width.

## Related issues

| Issue | Relationship |
|---|---|
| 141 Closed | Copies LifePRO `PCOVR.PRODUCT_TYPE` onto `RESRVCAT`, including the letter `L`. This issue is a three-coverage exception. |
| 99 Closed | ISWL product tags stay on the plan. Do not copy plan product onto the policy as a general rule. |
| 156 Closed | `SOR_POL` on the same row. Do not touch. |
| 145 / 132 | Vanish and resident state on the same row. Do not touch. |
| 25 / 26 | Policy number width and premium. Not this field. |

## What the client provided / what is missing

Provided: the three products and the three category codes. Warren confirmed the spec field.

Missing: none that block the work. No screenshot. The current file already shows `L` on all 33 policies.

## Blockers visible at intake

None for research. Development needs Warren’s written OK to carve these three coverages out of Closed Issue 141 before any code change.

## Owner and severity

Conversion defect on a closed mapping. Client priority No Go. The plan screen is already correct. The policy User Defined reserve category is the letter `L`.
