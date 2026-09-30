# Issue 181 — Risk Review Report

**Issue:** 181 — 658/659 QuikTvs Duration Shift
**Framework stage:** Risk
**Status:** Conditional Go
**Generated:** 2026-09-30
**Agent:** Risk (read-only simulation on the current QuikTvs and the 6/30 comparison). No production change.

**Status note:** Risk only. Rates and code stay as they are until you approve Development.

## Go / No-Go Recommendation

**CONDITIONAL GO.** Move the six plans' QuikTvs factors one year earlier. On the 6/30 file that makes 1,120 of 1,121 policies with a reserve match LifePRO. Ship it only if Store Means stays on for those plans, and exempt those plans from the Issue 106 duration check.

## 1. Current vs Proposed

| Field | Current | Proposed | Change? |
|---|---|---|---|
| QuikTvs year k, six plans | LifePRO year k | LifePRO year k+1 | Yes |
| QuikTvs final populated year, six plans | Last factor | Same factor, held | No |
| QuikTvs, every other plan | Current | Current | No |
| QuikPlTv STOREMEANS | N in our file; Y in Jill's 6/30 region | Leave both alone | No |
| QuikNps | Issue-year rate on every duration | Same | No |

## 2. Fields Untouched

| Target | Touched? |
|---|---|
| MPOLICY padding (#25) | No |
| MPREM / MMODPREM (#26) | No |
| QuikCvs and QuikPlCv (#172, #176) | No |
| QuikNps | No |
| quikplan, quikridr, quikmstr, quikval, policy tables | No |
| QuikPlTv | No |

## 3. Repo References

| Location | Role |
|---|---|
| `QLA_Migration/Output/rates/QuikTvs.csv` | The table to shift |
| `POST_EMIT_RATE_PATCHES` in both `app.py` files | Must re-apply the shift after a rate rebuild |
| `Issue_Log_Items/Issue_106/validate_issue106_quiktvs_duration.py` | Will fail on 1659C2 until that proof is exempt |
| `tools/validators/validate_release_closed_issues.py` | New smoke registered at Closure |
| `QLA_Migration/Reports/rates/newest_plan_rate_package.json` | Hash refresh after the edit |

## 4. Population Analysis

| Metric | Count |
|---|---:|
| QuikTvs rows | 104,327 |
| Rows in scope | 7,644 |
| Rows that stay byte-identical | 96,683 |
| Grids shifted | 1,196 |
| Factor cells that change | 70,002 |
| Final cells held | 1,196 |
| Year 0 today | `.00` on all 1,196 grids |

| Plan | Grids |
|---|---:|
| 1659C2 | 344 |
| 1658C1 | 304 |
| 1659CR | 172 |
| 1658CS | 152 |
| 1659CS | 152 |
| 1659SR | 72 |

6/30 valuation rows joined to a grid: 1,230. Of the 1,121 with a nonzero LifePRO reserve, 1,120 match the proposed factor. 109 rows have a LifePRO reserve of 0.00 even though the grid has a factor. One row is past the grid.

## 5. Fallback

| Option | What it does | Assessment |
|---|---|---|
| A. Shift QuikTvs one year earlier on the six plans | QLAdmin, with Store Means on, reads LifePRO's current-year factor | Recommended |
| B. Leave the table and turn Store Means off | Back to averaging two years. Jill already rejected that. She measured t−1 only after turning Store Means on. | Reject |
| C. Shift every plan | Undoes Issue 106 for the whole fleet. Jill named six plans. | Reject |

**Recommended:** Option A, six plans only.

## 6. Trace Policies

| Policy | QLAdmin reads today | After the shift | LifePRO | Pass? |
|---|---:|---:|---:|---|
| 9010713704C | 751 | 764 | 764 | Yes. 25 × 764 = 19,100.00 |
| 9010718309C | 198 | 205 | 205 | Yes |
| 9010755152C | 874 | 895 | 895 | Yes |
| 9010809294C | 321 | 332 | 332.00 | Yes |
| 9010809296C | 324 | 338 | 338.00 | Yes |
| 9010898471C | 747.83 | 763.99 | 763.99 | Yes |
| 9010756091C | no year-40 factor | still none | 206 at year 41 | Known gap. Age 67 grid ends at year 33. Do not invent years. |

## 7. Largest Factor Moves in the Trace

These are per unit, which is what the table stores. Dollars are units times the factor.

| Policy | Units | Before | After | Per-unit change |
|---|---:|---:|---:|---:|
| 9010755152C | 7 | 874 | 895 | +21 |
| 9010898471C | 5 | 747.83 | 763.99 | +16.16 |
| 9010713704C | 25 | 751 | 764 | +13 |
| 9010809296C | 18.173 | 324 | 338 | +14 |
| 9010809294C | 25.173 | 321 | 332 | +11 |
| 9010718309C | 25 | 198 | 205 | +7 |

9010713704C is the dollar example Jill's test should show: 18,775.00 today (25 × 751) versus 19,100.00 after (25 × 764).

## 8. Material Calculation Impact

Intentional. While Store Means is on, QLAdmin is one year behind LifePRO on these plans. The shift closes that gap for 1,120 policies. It does not change how any other plan is reserved, because those rows are not edited.

If the shifted table is loaded into a region where Store Means is off, QLAdmin would average two already-shifted years and move further from LifePRO. That is why the condition below is mandatory.

## 9. Prior Fix Preservation

| Check | Result |
|---|---|
| Issue 25 MPOLICY padding | Preserved. No policy file. |
| Issue 26 MPREM / MMODPREM | Preserved. No premium file. |
| Issue 106 | Overridden for these six plans only. Warren, 2026-09-30. Other 106 anchors (170858, 17085M, 170588, 221END, 1960OL) are not in the file being edited. |
| Issue 172 / 176 | Preserved. QuikCvs is not edited. |
| Issue 168 / 169 | Preserved. Different plans. |

## 10. Regression Checklist for Validation

- [ ] 9010713704C year 43 is 764.00. 1659C2 M PR age 44 year 0 is 2.00, not .00.
- [ ] 1,120 of 1,121 nonzero 6/30 reserves match units × the new factor at year t−1.
- [ ] 9010756091C is still past the grid. No invented years.
- [ ] In-scope row count is still 7,644. Out-of-scope QuikTvs is byte-identical.
- [ ] QuikNps, QuikCvs, QuikDvs, QuikPlTv unchanged.
- [ ] Issue 106 smoke passes with the six-plan exemption and still checks the other anchors.
- [ ] CEN net-premium smoke, 172, 176, 168, and 169 smokes pass.
- [ ] Newest-plan/rate manifest refreshed. PLAN-KEEP passes.
- [ ] Running the patch twice prints SKIP the second time.

## 11. Recommended Development Task

1. Write `Issue_Log_Items/Issue_181/tools/apply_issue181_cen_tv_shift.py` using the shift rule in the Planning report. Idempotent. Archive first. Stop if any row outside the six plans would change.
2. Add it to `POST_EMIT_RATE_PATCHES` in `app.py` and `QLA_Migration/app.py`. Bump `APP_VERSION` to v59.28 in both. Do not disturb the uncommitted #172 and #161 edits.
3. Exempt the six plans in the Issue 106 validator, including its Dur0-must-be-zero check for 1659C2. Update the Issue 106 guide row with the 2026-09-30 approval. Add the Issue 181 guide row and the fail-closed smoke when this issue is closed, not before Validation passes.
4. Do not edit QuikPlTv. Do not set STOREMEANS from conversion.
5. Refresh `newest_plan_rate_package.json` (package date 20260831).
6. After Validation, append QuikTvs through the Desktop DBF Append Tool.

### Conditions on the Go

1. CSO's region must still have Store Means on for these six plans when the new QuikTvs is loaded. Do not replace their QuikPlTv with our copy, which still says N.
2. Issue 106 is exempt for these six plans only, per Warren's 2026-09-30 approval.
3. Robert's separate QLAdmin flag is not part of this change. Tell CSO the table is ready. If they rerun before his flag is in, other plans can still move for the reason Jill already saw, and that movement is not from this table.

## Appendix

- Simulation was read-only against `QLA_Migration/Output/rates/QuikTvs.csv` and `evidence/issue181_valx_vs_quiktvs_20260630.csv`.
- Planning: `Issue_181_Planning_Report.md`
- Gate: `Issue_181_Dependency_Gate.md` (PASS)
