# Issue 181 — Validation Report

**Issue:** 181 — 658/659 QuikTvs Duration Shift
**Framework stage:** Validation
**Date:** 2026-09-30
**Verdict:** PASS
**Version:** v59.28

No production code was changed during validation. The shift was already applied in Development.

## Commands

| Command | Result |
|---|---|
| `python tools/validators/validate_issue181_cen_tv_shift.py` | PASS. 7,644 rows, 1,196 grids, one year earlier. |
| `python Issue_Log_Items/Issue_181/tools/apply_issue181_cen_tv_shift.py` | SKIP. A second run does not move the factors again. |
| `python Issue_Log_Items/Issue_106/validate_issue106_quiktvs_duration.py` | PASS. 170858, 17085M, 170588, 221END, and 1960OL still match. 1659C2 is no longer in that proof. |
| `python tools/validators/validate_cen_np_issue_year_level.py` | PASS. 1658C1 and 1659CR net premiums are still the issue-year rate. |

## Trace policies

The validator's anchors are the shifted cells QLAdmin reads (year t−1).

| Policy | Anchor checked | Value | LifePRO |
|---|---|---:|---:|
| 9010713704C | 1659C2 M PR 44, year 42 | 764.00 | 764 |
| 9010718309C | 1658C1 M PR 24, year 42 | 205.00 | 205 |
| 9010755152C | 1659CR F ST 55, year 41 | 895.00 | 895 |
| 9010809294C | 1658CS F ST 38, year 39 | 332.00 | 332.00 |
| 9010809296C | 1659CS M ST 14, year 39 | 338.00 | 338.00 |
| 9010898471C | 1659SR F ST 51, year 37 | 763.99 | 763.99 |

Every one of the 1,196 grids matches the pre-shift file moved one year earlier, including the repeated final year. 9010756091C was not given a new year past age 67.

## Untouched

| Check | Result |
|---|---|
| QuikPlTv STOREMEANS on the six plans | Still N in our file. The validator fails if this issue turns it on. |
| QuikNps | CEN net-premium check passed. |
| QuikCvs, QuikDvs, policy tables | Not opened by the shift. |
| Issue 25 / Issue 26 | No policy or premium file in the change. |
| Out-of-scope QuikTvs lines | Compared to the original file inside the apply script before it saved. |

## Row counts

QuikTvs in-scope rows stayed 7,644. Grid count stayed 1,196. The pre-shift extract has those same rows.

## Load note

The shifted file is in `QLA_Migration/Output/rates/QuikTvs.csv` and `QLA_Migration/Output/Test_Validation/rates/QuikTvs.csv`. The newest-plan/rate manifest was refreshed at package date 20260831.

This matches LifePRO only while Store Means stays on for these six plans. Do not reload QuikPlTv from our copy.

## Verdict

**PASS.** Ready for Regression. Not closed. The Issue 181 smoke is not in the always-on release list yet. That happens at Closure.
