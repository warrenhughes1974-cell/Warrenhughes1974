# Issue 181 — Implementation Notes

**Date:** 2026-09-30
**Version:** v59.28
**Status:** On hold. Developed and validated. Not closed. Waiting for Robert's QLAdmin Store Means flag before Regression or Closure.

## What changed

QuikTvs for six plans only. Each populated factor moved one year earlier. The last populated year stays in place, so the grid does not grow. Store Means was not changed. QuikPlTv in our file is still N. Jill's 6/30 region already has it on, and this load must not replace that file.

| Plan | In |
|---|---|
| 1659C2, 1658C1, 1659CR, 1658CS, 1659CS, 1659SR | Yes |
| 976658, 976659, every other plan | No |
| QuikNps, QuikCvs, QuikDvs, QuikPlTv, policy tables | No |

## Before / after

QLAdmin with Store Means reads year t−1. After the move, that cell is LifePRO's current-year factor.

| Policy | Plan | Year | Before | After | LifePRO per unit |
|---|---|---:|---:|---:|---:|
| 9010713704C | 1659C2 M PR 44 | 43 | 751 | 764 | 764 (25 units = 19,100.00) |
| 9010718309C | 1658C1 M PR 24 | 43 | 198 | 205 | 205 |
| 9010755152C | 1659CR F ST 55 | 42 | 874 | 895 | 895 |
| 9010809294C | 1658CS F ST 38 | 40 | 321 | 332 | 332.00 |
| 9010809296C | 1659CS M ST 14 | 40 | 324 | 338 | 338.00 |
| 9010898471C | 1659SR F ST 51 | 38 | 747.83 | 763.99 | 763.99 |

9010756091C is still past the age-67 grid, which ends at year 33. No year was added for it.

## Counts

7,644 rows, 1,196 grids. 69,758 cells changed text. The other populated cells already equaled the next year, so the move left them as they were. A second run prints SKIP.

## Files

| File | Change |
|---|---|
| `Issue_Log_Items/Issue_181/tools/apply_issue181_cen_tv_shift.py` | The shift. Registered so a later rate rebuild reapplies it. |
| `tools/validators/validate_issue181_cen_tv_shift.py` | Fail-closed check against the pre-shift extract. |
| `app.py`, `QLA_Migration/app.py` | Patch registered. Version v59.28. |
| `Issue_Log_Items/Issue_106/validate_issue106_quiktvs_duration.py` | 1659C2 removed from the identity proofs. |
| `Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md` | Issue 106 row notes Warren's 2026-09-30 exception. |
| `QLA_Migration/Output/rates/QuikTvs.csv` | Shifted table. |
| `QLA_Migration/Output/Test_Validation/rates/QuikTvs.csv` | Same file, for a partial reload. |
| `Issue_Log_Items/Issue_181/evidence/quiktvs_six_plans_before_shift.csv` | Pre-shift rows the validator compares to. |
| `QLA_Migration/Archive/issue181_pre_shift/QuikTvs.csv` | Full-file rollback copy. |

## Not done yet

The always-on smoke registration and the Issue 181 guide row wait for Closure. QuikTvs has not been appended to a DBF. Do not run a full product reload that replaces QuikPlTv.
