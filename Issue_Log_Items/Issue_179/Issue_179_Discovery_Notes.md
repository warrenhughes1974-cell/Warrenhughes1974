# Issue 179 — Discovery Notes

**Issue:** 179 — Missing Next Div in Temp Values
**Status:** Closed. Female dividend rates copied from the male scale on 2026-09-30.
**Date:** 2026-09-28

## Client ask

9010143726C has a next dividend of $18.40 in LifePRO. QLAdmin does not have a dividend. $18.40 is the 7.36 factor at duration 66 times the units. Other policies also missing a dividend in QLAdmin: 9010348734C, 9010264207C, and 9010157076C.

## What the screen is

Policy Display field 37, Next Div: dividends to be credited at the next anniversary. QLAdmin stores that amount in QuikTmpv (Dividends Next 12 Months: policy, dividend option, date, amount). The amount is written when dividend values are rebuilt from the QuikDvs rate. This conversion does not load QuikTmpv.

## 9010143726C

| Item | Value |
|---|---|
| Plan | 221END (LifePRO 621 END85) |
| Sex | Female |
| Issue age | 19 |
| Units | 2.5 |
| Issued | 1961-05-01 |
| Paid to | 2027-05-01 |
| Last anniversary duration | 65 |
| Next duration | 66 |
| Participating | Yes |
| Dividend option | 1 (cash) |

LifePRO PDAGE for 621 END85 dividends is male only. There is no female scale. Male issue age 19, duration 66, is 7.36. 7.36 × 2.5 = 18.40.

Current QuikDvs has that 7.36 on male only. QuikPlDv also has a female key for 221END, and that key has no rates. quikplan.GDVARYDV is Y, so QLAdmin looks up the policy sex. The female lookup finds nothing, so Next Div stays blank.

## The other three

Each of these has a QuikDvs rate for its own sex, issue age, and next duration. The same factor is in the 8/31 LifePRO dividend extract.

| Policy | Plan | Sex | Age | Units | Next duration | Factor | Factor × units |
|---|---|---|---|---|---|---|---|
| 9010157076C | 221END | M | 20 | 1 | 65 | 7.38 | 7.38 |
| 9010264207C | 280END | F | 4 | 8.533 | 60 | 19.32 | 164.86 |
| 9010348734C | 196085 | M | 17 | 2.5 | 57 | 25.33 | 63.33 |

A blank Next Div on these three is not the missing female scale. Either dividend values have not been rebuilt into QuikTmpv, or the region is not on this rate file.

## How wide the female miss is

Active participating policies whose sex has no dividend scale, while the other sex does: 28.

| Plan | Sex on the policy | Scale on file | Policies |
|---|---|---|---|
| 1960OL | F | M only | 24 |
| 221END | F | M only | 2 |
| 196065 | F | M only | 2 |

209 other active participating policies match a scale for their sex.

## What a fix would be

For 9010143726C, LifePRO is already using the male 7.36 scale. The female policy needs to use that same scale. Do not invent a different female dividend. Do not change cash values. Plan 221END cash values are already male factors with a female key, and that pattern is a separate closed check.

## Screen check and email

Warren confirmed 9010157076C on Policy Display. Next Div is $7.38, the male 221END duration-65 factor times 1 unit.

Email sent to Eric on 2026-09-28 asking for screenshots of the female dividend rates on 221END, 196065, and 1960OL. The note says we look the dividend up by the sex on the policy, the male 221END policy shows $7.38, and the rate file and the July and August LifePRO extracts have no female rates for those three plans.

## Open question

Waiting on Eric's screenshots of a female dividend scale for 221END, 196065, and 1960OL. 9010264207C and 9010348734C have a rate for their own sex in the current file. Those two screens have not been confirmed.

## Rate table update (2026-09-30)

Warren approved copying the male dividend scale onto the female key for 221END, 196065, and 1960OL.

| Table | What changed |
|---|---|
| `QLA_Migration/Output/rates/QuikDvs.csv` | Female rows added as an exact copy of the male rows. 221END 236, 196065 249, 1960OL 345. |
| `QLA_Migration/Output/rates/QuikPlDv.csv` | No change. The female keys were already there. |

Male rows were not changed. Other plans were not changed. 221END female, age 19, duration 66 (CNTL 06, DV6) is 7.36.

## Close (2026-09-30)

Warren approved the copy. `QuikDvs` female rows for 221END, 196065, and 1960OL match the male rows. `QuikPlDv` was not changed. A later rate rebuild re-applies the copy. Smoke: `python tools/validators/validate_issue179_female_dividend.py`.
