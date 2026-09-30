# Issue 181 — Planning Report

**Issue:** 181 — 658/659 QuikTvs Duration Shift
**Framework stage:** Planning
**Status:** Planning
**Generated:** 2026-09-30
**Agent:** Intake → Planning (read-only). No code or Output change.

## 1. Executive Finding

The 658/659 QuikTvs factors are mean reserves. LifePRO's reserve is units times the factor for the current policy year. With Store Means on, QLAdmin reads that factor one year earlier. Move each factor one year earlier on the six plans Jill named. On the 6/30 file, that lines up 1,120 of the 1,121 policies that have a reserve. The remaining policy is past the end of its grid already, so the shift does not create a factor for it.

## 2. Confirmed LifePRO Source

| Source | File | In Source/? | Rows |
|---|---|---|---:|
| 6/30 valuation extract (VALX) | Compared in `evidence/issue181_valx_vs_quiktvs_20260630.csv` | Evidence file, not a new extract | 1,230 joined 658/659 rows |
| Current QuikTvs | `QLA_Migration/Output/rates/QuikTvs.csv` | Output rates | 104,327 total; 7,644 in scope |

LifePRO `RV_T` ÷ units equals QuikTvs at policy year t on 1,120 rows. `RV_T_1` is 0.00 on every 658/659 row, so LifePRO is not storing a separate beginning-of-year reserve for these plans.

## 3. Confirmed QLAdmin Target

| Table | Field | Type | What it is |
|---|---|---|---|
| QuikTvs | TV0–TV9 | CHAR(7) | Reserve factor per unit. Year = CNTL × 10 + slot |
| QuikTvs | PLAN, GENDER, UWCLASS, AGE, BAND, ISSCNTRY, ISSUEST, EFFDATE, CNTL | key | Unchanged |
| QuikPlTv | STOREMEANS | logical | Already Y in Jill's 6/30 region. N in our CSV and in the CSO product file we ship. Do not overwrite her region file. |

Repo path that must keep re-applying the shift after a rate rebuild: `POST_EMIT_RATE_PATCHES` in `app.py` and `QLA_Migration/app.py`.

## 4. Source-to-Target Mapping

| From | To | Transformation | Change? |
|---|---|---|---|
| QuikTvs year k+1 on the six plans | QuikTvs year k | One year earlier | Yes |
| QuikTvs final populated year | Same cell | Hold. Do not invent a year past the grid. | No value change |
| QuikTvs year 0 (`.00` on all 1,196 grids) | Dropped | Replaced by old year 1 | Yes |
| Every other plan | Same bytes | | No |
| QuikNps, QuikCvs, QuikDvs, QuikPlTv, quikplan, policy tables | | | No |

### Fields that must remain unchanged

| Target | Touch? |
|---|---|
| quikmstr.MMODPREM (#26) | No |
| quikridr.MPREM (#26) | No |
| MPOLICY padding (#25) | No |
| QuikCvs / QuikPlCv (#172, #176) | No |
| QuikNps (CEN net premium stays the issue-year rate) | No |
| QuikPlTv STOREMEANS in the CSO product file | No. Jill set Y. Reloading our N would undo her. |

## 5. Open Client Questions

1. None that block the shift. Jill named the six plans and the direction. Warren approved the move, including the Issue 106 override.
2. Carried as a load rule, not a question: Store Means must still be on when CSO reruns. We do not turn it on in the product file from this issue.
3. Robert's QLAdmin flag (so other plans do not all move when Store Means is checked) is his work. It does not change this table.

## 6. Formatting Rules

| Rule | Recommendation |
|---|---|
| Number format | Keep the existing text (`764.00`, `.00`). |
| Row count | Same 7,644 rows, same CNTL pages. No added or deleted rows. |
| Blank tail | Cells after the last populated year stay blank. |
| Final year | Repeat the last populated factor in place. |
| Idempotent | If year 0 is already the old year 1 (gold below), the patch prints SKIP. |

Gold, 1659C2 male Preferred age 44:

| Year | 0 | 1 | 42 | 43 | last |
|---|---:|---:|---:|---:|---:|
| Now | .00 | 2.00 | 751.00 | 764.00 | 978-class final on the young-age grid |
| After | 2.00 | 17.00 | 764.00 | 776.00 | same final value |

## 7. Memo / Text

Not applicable.

## 8. Policy Number Key Handling

No policy-key change. #25 padding is untouched. The trace policies below are read from the valuation file only to prove the factor.

## 9. Estimated Record Counts

| Metric | Count | Basis |
|---|---:|---|
| Grids in scope | 1,196 | All sex / class / age / band keys on the six plans, EFFDATE 19000101 |
| QuikTvs rows in scope | 7,644 | |
| Factor cells that move | 70,002 | Every populated year except the final one |
| Final cells held | 1,196 | One per grid |
| QuikTvs rows outside scope | 96,683 | Must stay byte-identical |
| 6/30 policies whose factor then matches LifePRO | 1,120 of 1,121 with a reserve | units × new factor at year t−1 = old factor at year t = `RV_T` per unit |
| LifePRO reserve of 0.00 | 109 | Not a table miss. The factor is present; LifePRO stored no reserve. |
| Past the grid | 1 | 9010756091C |

Grid counts: 1659C2 344, 1658C1 304, 1659CR 172, 1658CS 152, 1659CS 152, 1659SR 72.

## 10. Sample Trace

QLAdmin with Store Means reads the factor at year t−1. After the shift, that cell holds today's year-t factor, which is LifePRO's per-unit reserve.

| Policy | Plan | Year | Now (t−1) | After | LifePRO per unit |
|---|---|---:|---:|---:|---:|
| 9010713704C | 1659C2 M PR 44 | 43 | 751 | 764 | 764 (25 units = 19,100.00) |
| 9010718309C | 1658C1 M PR 24 | 43 | 198 | 205 | 205 |
| 9010755152C | 1659CR F ST 55 | 42 | 874 | 895 | 895 |
| 9010809294C | 1658CS F ST 38 | 40 | 321 | 332 | 332.00 |
| 9010809296C | 1659CS M ST 14 | 40 | 324 | 338 | 338.00 |
| 9010898471C | 1659SR F ST 51 | 38 | 747.83 | 763.99 | 763.99 |

Edge: 9010756091C, 1658C1 female Standard, issue age 67, policy year 41, 25 units, LifePRO 206 per unit. The grid for age 67 ends at year 33 (maturity). There is no year-41 factor to shift into place. Leave it. Do not invent years past the grid.

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|---|---|---|
| Shifted table loaded while Store Means is off | High | Do not replace QuikPlTv. Jill's Y must remain. Say so in the handoff to CSO. |
| Issue 106 smoke fails | High | Exempt only these six plans. 1659C2 M/17 ST today is Dur1 = 1.00 and Dur83 = 978.00. After the shift Dur0 = 1.00 and Dur1 = 5.00; Dur83 stays 978.00 because year 83 is the last cell. The Dur0 "must be zero" check fails too, so the whole 1659C2 proof is exempt, not just Dur1. |
| Other plans' reserves move | Not caused by this table | Robert's flag. Our change does not alter their QuikTvs rows. |
| A later rate rebuild wipes the shift | Medium | Register the patch in `POST_EMIT_RATE_PATCHES` and add a fail-closed smoke. |
| Older-cut plan/rate hash | Medium | Refresh `newest_plan_rate_package.json` after the edit. Package date stays 20260831. |

## 12. Dependency Gate Preview

| Check | Met? |
|---|---|
| Source file present | Yes. Current QuikTvs plus the 6/30 comparison. |
| Field definitions confirmed | Yes. TV0–TV9, year = CNTL × 10 + slot. |
| Client scope clear | Yes. Six plans, one year earlier. Warren approved. |
| Example policies available | Yes. |

## 13. Recommended Risk Agent Prompt

Quantify the shift on the current QuikTvs: cells moved, cells held, rows outside the six plans unchanged, and the 1,120 / 1,121 LifePRO tie. Confirm #25, #26, #172, and #176 are untouched. Recommend Conditional Go if the only conditions are "do not overwrite Store Means" and "exempt Issue 106 for these six plans."

## 14. Recommended Development Task (Do Not Implement)

1. Add `Issue_Log_Items/Issue_181/tools/apply_issue181_cen_tv_shift.py`. Six plans only. Shift rule in section 6. Idempotent against the 1659C2 M PR age 44 gold. Archive copy first. Refuse to run if any out-of-scope QuikTvs row would change.
2. Register it in `POST_EMIT_RATE_PATCHES` in both `app.py` files. Bump `APP_VERSION` from v59.27 to v59.28 in both. Leave the uncommitted #172 and #161 edits in those files as they are.
3. Exempt the six plans in `Issue_Log_Items/Issue_106/validate_issue106_quiktvs_duration.py`. Keep every other proof.
4. Add `tools/validators/validate_issue181_cen_tv_shift.py`. Fail if the gold is not shifted, if any in-scope grid is not old year k+1, if the in-scope row count is not 7,644, or if any other plan's QuikTvs changed. Register it in `SMOKE_JOBS` and the accountability list at Closure, not before Validation passes.
5. Refresh the newest-plan/rate manifest.
6. Do not edit QuikPlTv, QuikNps, QuikCvs, or any policy CSV.
7. After Validation, push QuikTvs through the Desktop DBF Append Tool. Suggested share name: `QuikTvs_Issue181_YYYYMMDD.dbf`.

## Appendix

- Discovery: `Issue_181_Discovery_Notes.md`
- Comparison: `evidence/issue181_valx_vs_quiktvs_20260630.csv`
- Read-only research: `tools/_research_issue181_duration.py`
- Issue 106 proof that will break: `validate_issue106_quiktvs_duration.py` line for 1659C2 M/17 ST
