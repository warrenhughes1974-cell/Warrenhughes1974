# Issue 181 — 658/659 QuikTvs Duration Shift

**Status:** Active. Discovery complete. No conversion change.
**Date:** 2026-09-29 (logged), 2026-09-30 (Discovery)
**Number:** Filed as 181 because 180 is already NACHA Bank Layout Gaps.

## Client ask (verbatim)

I checked all the 658/659 plan codes, and where the calculation is based on the UNITS x Mean Reserve the results match for the t-1 duration. Could you shift the table one duration so they would then match? This is in quiktvs.

## Plans in scope

| QLAdmin plan | LifePRO coverage | QuikTvs rows | 6/30 valuation rows |
|---|---|---:|---:|
| 1659C2 | 659 CEN II | 2,164 (M/F x PR/ST) | 796 |
| 1658C1 | 658 CEN I | 2,064 (M/F x PR/ST) | 305 |
| 1659CR | 659 CEN SR | 1,082 (M/F ST) | 112 |
| 1658CS | 658 CEN SD | 1,031 | 8 |
| 1659CS | 659 CEN SD | 1,031 | 8 |
| 1659SR | 659 SR GD | 272 | 1 |

`976658` and `976659` are waiver-of-premium riders. Their codes contain 658/659, but they are not CEN plans. `976659` has 250 QuikTvs rows. Confirm with Eric whether they are in scope. Default: out.

## How QLAdmin reads this table

- `QuikPlTv` for all six plans has `STOREMEANS=N` and `CALCMIDS=N`, both in our Output and in CSO's own region file (`Product_Files_From_CSO\QuikPlTv.dbf`). QuikTvs holds **end-of-year** reserves, and QLAdmin works out the mean itself: ½ × (end of year t−1 + net premium + end of year t).
- The L14 policies prove which year of the table QLAdmin reads. For policy year 23 on `1L14SC` F/62, LifePRO shows the start of year at 605.12 (QuikTvs year 22), the end of year at 629.15 (QuikTvs year 23), and a mean of 636.23. QLAdmin matched that after the Issue 168 load. **QuikTvs year N = end of policy year N.**
- CSO's region uses mortality `E1`/`F1` on these keys. Our conversion file uses `A1`. The reserve key table is CSO's own file and is not rebuilt from conversion, so this does not drive the complaint. Note it for Eric.

## What the LifePRO valuation file shows (6/30/2026 VALX)

Script: `Issue_Log_Items/Issue_181/tools/_research_issue181_duration.py` (read-only)
Detail: `Issue_Log_Items/Issue_181/evidence/issue181_valx_vs_quiktvs_20260630.csv`

| Check | Result |
|---|---|
| 658/659 valuation rows joined to a QuikTvs grid | 1,230 |
| LifePRO end-of-year reserve per unit (`RV_T` ÷ units) = QuikTvs at **policy year t** | **1,120** |
| Rows that do not tie | 110. 109 have a LifePRO reserve of 0.00; 1 is non-zero |
| LifePRO start-of-year reserve (`RV_T_1`) | 0.00 on every 658/659 row. LifePRO does not store it for these plans |
| LifePRO statutory mean (`RV_MEAN_RV`) | The ISWL account value, not a grid value (e.g. 9010713704C 45,551.94) |
| LifePRO net level mean (`MEAN_NL_RESERVE` ÷ units) | 2–3 above QuikTvs year t (e.g. 767 against 764). It is not the standard ½ × (t−1 + t + premium) from this grid |

Example 9010713704C: 1659C2, male Preferred, issue age 44, issued 4/19/1984, 25 units, policy year 43 at 6/30/2026. QLAdmin valuation also shows duration 43.

| QuikTvs year | 42 | 43 | 44 |
|---|---:|---:|---:|
| End-of-year reserve per unit | 751 | **764** | 776 |

LifePRO `RV_T` = 19,100.00 = 25 × 764 (year 43). Net premium per unit is 17. QLAdmin's own formula gives ½ × (751 + 17 + 764) = 766 per unit.

## 2026-09-30 update — CSO email thread (supersedes the verdict below)

From the 9/28–9/30 thread (Jill Burns, Robert De Sarro):

- Jill: the 658/659 QuikTvs factors are **mean** reserves. LifePRO reserve = units × factor. This agrees with the VALX tie above: `RV_T` = units × QuikTvs year t.
- Jill turned on **Store Means** on every 658/659 key in the 6/30 test region and reran. With Store Means on, QLAdmin takes units × the factor **one year earlier** than LifePRO, so it lands on t−1.
- Jill asked us to shift the table one duration, in time for the next run later this week.
- Robert: a separate QLAdmin-side item. Changing Store Means on 658/659 changed reserves on every plan, which needs an internal "store means by plan" flag. That is not conversion work.
- Warren, 2026-09-30: "We need to move them." This is recorded as Warren's written approval to override Closed Issue 106 for these six plans only.

**Decision.** For `1659C2`, `1658C1`, `1659CR`, `1658CS`, `1659CS` and `1659SR` only, move every QuikTvs factor one year earlier (new year k = old year k+1). With Store Means on, QLAdmin at policy year t then reads LifePRO's year t factor. Example 9010713704C, year 43: QLAdmin reads 764 (was 751), so 25 × 764 = 19,100.00 = LifePRO `RV_T`.

The shift only works with **Store Means = Y** on these keys. The QuikPlTv shipped from `Product_Files_From_CSO` still says N. The shift and the flag must go out together.

## Verdict before the CSO thread (kept for history)

The table is **not** one year early against LifePRO's own valuation file. LifePRO's end-of-year reserve for policy year t is at QuikTvs year t on 1,120 of the 1,121 policies that carry a reserve, which is how Issue 106 aligned it. Moving the grid one year would break that tie on those 1,120 policies.

We cannot yet reproduce Eric's "matches t−1" from what is in the repo. Possible explanations, none proven:

1. Eric's "Mean Reserve" is the LifePRO value `units × grid(t)`. For 658/659 LifePRO appears to hold reserves by taking that grid value directly, while QLAdmin averages the start and end of the year (`STOREMEANS=N`). Then QLAdmin sits about half a year behind, not a full year. If so, the fix is a plan reserve setting (`STOREMEANS`, `CALCMIDS`, or the method on CSO's key), not a table shift.
2. Eric is comparing QLAdmin to a CSO mean-reserve table that is not in our extracts.
3. His QLAdmin region has a different QuikTvs than the current Output. The last reserve rebuild was 9/30 09:46.

## Conflicts with Closed issues (notify Warren before any change)

| Closed issue | Conflict |
|---|---|
| **106** RV Rates Off by One Duration | This fix set QuikTvs year N = LifePRO year N. A one-year shift on 658/659 undoes it for these plans. Anchor `1659C2` M/17 SM Dur1=1 Dur83=978 and `validate_issue106_quiktvs_duration.py` would fail. |
| **CEN NP** smoke | `1658C1` / `1659CR` QuikNps stay level on the year-1 rate. Shifting only QuikTvs changes which net premium sits next to which reserve in QLAdmin's mean. |
| **PLAN-KEEP** | Any QuikTvs change requires a refreshed newest-plan/rate manifest, or older-cut runs fail. |

## Open questions (must be answered before Development)

1. **Eric: one worked example.** Policy number, the QLAdmin screen or QuikValf value he compared (reserve, mean, or tabular net), his UNITS × Mean Reserve value, the duration he used, and where his Mean Reserve number comes from (LifePRO screen, VALX field, or a CSO table).
2. **Warren: read access to the 6/30 QLAdmin valuation.** `Q:\CSO\CSO_Test_6_30_2026\QuikValf.dbf` (MDUR, MMEAN, MTABNET, MRESERVE) to confirm which two years QLAdmin uses for 658/659. This path is outside the repo and needs your OK.
3. **Scope:** confirm `976658` / `976659` are out.
4. **Warren:** if the evidence supports a shift, written approval to override Issue 106 for these six plans only.

## Stop

Discovery only. No rate change. Awaiting answers to the open questions, then Proceed to Intake.
