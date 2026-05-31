# R5 Business-Input Readiness Summary

This folder collects the **business/actuarial inputs** that must be completed before R5 (Rate Loader Implementation) can produce DBFs. No code, DBFs, or decisions are produced here — these are blank templates for sign-off.

## Why these inputs are required
The R3/R4 analysis proved the *transformation* (PLAN resolution, TYPE_CODE routing, SEX/BAND/UWCLASS crosswalks, duration→CNTL paging) and the *field capacity* (`CHAR(7)`, 2-decimal, pos ≤ 9999.99 / neg ≥ −999.99). Two input gaps remain that **only the business/actuarial team can fill**:

1. **Overflow decisions** — two plans hold factors larger than the QLAdmin field can store. The fix (rescale vs alternate basis vs quarantine) is an actuarial call, not a code change.
2. **Rate-key assumptions** — `QuikPlCv` and `QuikPlTv` (the latter shared by NP) require per-plan actuarial basis values (`MORT`, `RSVINT`, `RSVMETH`, `INTMETH*`, `ETIMORT`, `NFOINT`, `STOREMEANS`, `CALCMIDS`) that **do not exist in the LifePRO rate extract**.

## Decisions blocking R5
| Blocker | Affects | Owner | Artifact |
|---|---|---|---|
| Overflow handling for `2665ST` (DB) and `A96DAR` (CV) | those 2 plans only | Actuarial | `rate_overflow_business_decision_sheet.csv` |
| Per-plan reserve / cash-value assumptions | CV, RV (TV), NP families | Actuarial | `plan_rate_key_assumption_mapping_template.csv` |
| EFFDATE generation value + ISSCNTRY/ISSUEST defaults | all families (need a date/default) | Business | assumption template (left blank) |

## Loader development can begin family-first in this order
1. **PR / Gross Premium** — lowest risk; **no overflow**, no assumption-table dependency.
2. **DV / Dividends** — lowest risk; **no overflow**, no assumption-table dependency.
3. **DB / Death Benefits — excluding overflow plan `2665ST`** — no assumption dependency; one plan gated by an overflow decision.
4. **CV / Cash Values — excluding overflow plan `A96DAR`** — needs `QuikPlCv` assumptions (MORT/ETIMORT/NFOINT/INTMETHCV); one plan gated by overflow.
5. **RV / Terminal Reserves** — needs `QuikPlTv` assumptions (MORT/RSVINT/RSVMETH/INTMETHTV/STOREMEANS/CALCMIDS).
6. **NP / Net Premiums** — through the **shared `QuikPlTv`** reserve assumptions (depends on the same reserve basis as RV).

## Family gating at a glance
- **PR and DV** are the lowest risk because they have **zero overflow** and need no assumption mapping → start here.
- **CV / TV / NP** are gated by the **assumption mapping** (cannot generate correct rate keys without it).
- **DB** has **one overflow plan** (`2665ST`) requiring a decision; the other 9 DB plans are unblocked.
- **CV** has **one overflow plan** (`A96DAR`) requiring a decision, on top of its assumption dependency.

## Plans gated by overflow
| Family | Plan | Overflow rows | Max value |
|---|---|---|---|
| DEATH_BENEFIT (DB) | `2665ST` | 1,333 | 28,134.00 |
| CASH_VALUE (CV) | `A96DAR` | 300 | 26,418.10 |

## Scope of the assumption template
- **64** distinct authoritative plans, **168** plan × family rows.
- Rows by family: GROSS_PREMIUM 11, DIVIDEND 15, DEATH_BENEFIT 10, CASH_VALUE 36, TERMINAL_RESERVE 49, NET_PREMIUM 47.
- `GENDER_REQUIRED / UWCLASS_REQUIRED / BAND_REQUIRED` are pre-filled (Y/N) from **observed** source segmentation; assumption columns are `N/A` for families that don't carry them and **blank** where actuarial input is needed.
