# Issue 181 — Intake Summary

**Issue:** 181 — 658/659 QuikTvs Duration Shift
**Framework stage:** Intake
**Date:** 2026-09-30
**Track:** Client-facing (Jill Burns / CSO). Needed for the next run later this week.

## Client symptom

Jill checked every 658/659 plan. Where the reserve is units times the mean-reserve factor, QLAdmin matches the prior duration (t−1). She asked us to shift the QuikTvs table one duration so it matches the current duration.

She had already turned on Store Means for these plans in the 6/30 test region. With that box on, QLAdmin multiplies units by the factor one year earlier than LifePRO does. LifePRO's own 6/30 valuation file uses the factor for the current policy year.

Warren, 2026-09-30: "We need to move them." That is the approval to override Closed Issue 106 for these six plans only.

## Example policies

| Policy | Plan | What LifePRO has | What QLAdmin reads today (t−1) | After the shift |
|---|---|---:|---:|---:|
| 9010713704C | 1659C2 M PR age 44, year 43, 25 units | 764 | 751 | 764 (25 × 764 = 19,100.00) |
| 9010718309C | 1658C1 M PR age 24, year 43, 25 units | 205 | 198 | 205 |
| 9010755152C | 1659CR F ST age 55, year 42, 7 units | 895 | 874 | 895 |

Full comparison: `evidence/issue181_valx_vs_quiktvs_20260630.csv` (1,230 rows).

## Domain

Rates. `QuikTvs` only. Not policy, premium, client, claims, or memo.

## In scope

Move every populated QuikTvs factor one year earlier on these plans only:

`1659C2`, `1658C1`, `1659CR`, `1658CS`, `1659CS`, `1659SR`

All genders, classes, ages, and bands. 1,196 grids, 7,644 rows.

## Out of scope

- `976658` and `976659` (waiver riders). Jill named the six plans above.
- Every other plan's QuikTvs, and QuikNps, QuikCvs, QuikDvs, quikplan, and all policy tables.
- Turning Store Means on. Jill already did that in the 6/30 region. This issue must not reload `QuikPlTv` over that setting.
- Robert's QLAdmin change that stops other plans' reserves from moving when Store Means is checked. That is QLAdmin product work, not this conversion.

## Related issues

| Issue | Relation |
|---|---|
| 106 (Closed) | Set QuikTvs year N = LifePRO year N. This shift undoes that for the six plans. Warren approved the override on 2026-09-30. |
| 172, 176 (Closed) | Cash-value keys on 1659C2. Different table. Do not touch. |
| 168, 169 (Closed) | Other plans' reserve loads. Do not touch. |

## Owner and priority

- Owner: Warren (conversion). Client contact: Jill Burns.
- Priority: this week's CSO run.
- Severity: valuation reserves on the 658/659 block are one year light while Store Means is on.

## Blockers visible at intake

None that stop Planning. Two load conditions to carry forward:

1. The shifted table only matches LifePRO if Store Means stays on for these six plans.
2. The Issue 106 release check must exempt these six plans, or the next smoke run fails.

## Status recommendation

Planning. No code or rate change in this stage.
