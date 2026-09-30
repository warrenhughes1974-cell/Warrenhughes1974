# Issue 181 — Resolution Summary

**Issue:** 181 — 658/659 QuikTvs Duration Shift
**Framework stage:** Closure
**Final status:** Closed
**Engine version:** v59.28
**Closed date:** 2026-09-30
**Owner:** Warren

## Resolution (issue log — paste-ready)

09/30/2026 Resolution: Reserve rates on 1658C1, 1658CS, 1659C2, 1659CR, 1659CS, and 1659SR were moved one year earlier so that, with Store Means on, units times the factor match the current duration. Examples: 9010713704C 1659C2 year 43 reads 764 per unit (25 units = 19,100.00); 9010718309C 1658C1 reads 205; 9010755152C 1659CR reads 895.

## Problem

Jill checked the 658/659 plans after turning Store Means on. QLAdmin was using the prior duration. LifePRO uses units times the factor for the current policy year.

## Root cause

The factors are mean reserves. With Store Means on, QLAdmin reads one year earlier than LifePRO. The table had been aligned to the LifePRO year by Issue 106, which is correct when Store Means is off and wrong when it is on. Warren approved the Issue 106 exception for these six plans on 2026-09-30.

## Fix

Each populated QuikTvs factor on the six plans moved one year earlier. The last populated year is repeated. No other plan or table was changed. QuikPlTv was not changed, so a reload of that file would turn Store Means back off. The shift is re-applied after a rate rebuild. Robert's QLAdmin Store Means change was confirmed in by Warren on 2026-09-30. That flag is what stops other plans from moving when Store Means is on for these six.

## Evidence

| Check | Result |
|---|---|
| `python tools/validators/validate_issue181_cen_tv_shift.py` | PASS on full Output. 7,644 rows, 1,196 grids. |
| Accountability | IN_DATA. Exit 0 on the Issue 181 validator, registered in `validate_issue_log_accountability.py`. |
| `--smoke-only` | Issue 181 PASS. |
| Regression | PASS. Out-of-scope QuikTvs lines match the pre-shift archive. |
| Test_Validation | `Output/Test_Validation/rates/QuikTvs.csv` |

## Not changed

QuikNps, QuikCvs, QuikDvs, QuikPlTv, quikplan, and every policy table. Waiver riders 976658 and 976659. Issue 106 anchors other than the six plans.

## Residual

The full release smoke is still blocked by Issue 160 (missing archive snapshot) and Issue 173 (gold balances no longer match). Both were already failing before this shift. Do not treat the package as a clean handoff until those two are resolved.

QuikTvs has not been written to a DBF. Do not replace CSO's QuikPlTv with the conversion copy.

9010756091C is issue age 67 in policy year 41. That grid ends at year 33. No year was invented for it.

## Rollback

Restore `QLA_Migration/Archive/issue181_pre_shift/QuikTvs.csv`, remove the Issue 181 entry from `POST_EMIT_RATE_PATCHES`, and refresh the newest-plan/rate manifest.

## Git

Commit `3a3db22258dad4674715a4a38df658104f5f1307` on `issue-34-pr7-quikisrr`. Not pushed.
