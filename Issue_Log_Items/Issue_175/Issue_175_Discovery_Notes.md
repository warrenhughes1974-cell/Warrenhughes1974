# Issue 175 — Discovery Notes

**Issue:** 175 — Res Cat Unique Field
**Date:** 2026-09-28
**Framework stage:** Discovery
**Code:** None

---

## Client ask

Policies on products `1L15GD`, `1L16GD`, and `1L17SP` did not pull the correct reserve category. The categories should be 13, 13, and 12. Raised 2026-09-25 by Eric. No Go. Owner Eric. Assigned Warren.

Warren: this is the spec field.

## Verdict

Yes. This is `quikspec.RESRVCAT`, the reserve category on the policy User Defined screen from Issue 141. It is not the plan LOB.

The plan product code is already right. The policy field is the letter `L`.

| Plan | Policies | Plan `PRODUCT` today | Policy `RESRVCAT` today | Eric wants |
|---|---:|---|---|---|
| 1L15GD | 11 | 13 | L | 13 |
| 1L16GD | 2 | 13 | L | 13 |
| 1L17SP | 20 | 12 | L | 12 |

Those 33 policies are the only rows in the current package with reserve category `L`.

## Source

LifePRO `PCOVR.PRODUCT_TYPE` on the 8/31 and 6/30 extracts:

| Coverage | Description | PRODUCT_TYPE |
|---|---|---|
| L15 | Graded Death Benefit | L |
| L16 | Graded Death Benefit | L |
| L17 BASE | Single Premium | L |
| L17 1 / L17 2+ (and JPO) | Single Premium Whole Life | 12 |
| L15 ADB | Inherent accidental death | 13 |

Issue 141 copies that base-coverage `PRODUCT_TYPE` onto `quikspec.RESRVCAT`. These policies sit on L15, L16, and L17 BASE, so the policy gets `L`.

`L` also appears on discount coverages `DISCHO20 B`, `DISCHO25`, and `DISCHO80`. None of those is a base plan on a policy in this package.

The plan row was already set to 13 or 12 (`quikplan.PRODUCT`). Issue 141 deliberately does not copy the plan product onto the policy, because ISWL plans carry `ISWLFE` there.

## What should change, and what should not

Change only `quikspec.RESRVCAT` on these 33 policies: `L` to 13, 13, and 12.

Do not change `quikplan` (product is already 13/12, and ISWL plans stay `ISWLFE`). Do not change vanish, resident state, or source policy number on the same spec row. Do not change the other reserve categories (05, 13, 03, 16, and the rest).

This is a narrow exception to Closed Issue 141, which said to keep LifePRO `L` as-is. The Issue 141 check will fail on these three plans unless that check is updated with the exception. The rest of Issue 141 stays.

## Examples

`9011210337C` plan 1L15GD, reserve category L, should be 13.
`9011216680C` plan 1L16GD, reserve category L, should be 13.
`9011217014C` plan 1L17SP, reserve category L, should be 12.

## Open point

Eric’s 13 / 13 / 12 matches the plan product code, not the LifePRO letter `L`. Discovery treats that as the requested policy reserve category.

## Stop

Awaiting “Proceed to Intake”.
