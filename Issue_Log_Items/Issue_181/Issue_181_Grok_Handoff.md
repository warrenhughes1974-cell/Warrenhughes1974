# Issue 181 — Handoff to Grok 4.7

**2026-09-30:** Intake, Planning, Dependency Gate (PASS), and Risk (Conditional Go) are written in this folder. Development has not started. Wait for Warren to say Approved for Development, then follow section "Development" below. Do not redo Intake.

**Read first:** `Issue_181_Discovery_Notes.md` (this folder, including the 2026-09-30 update), `docs/qladmin_rates/README.md`, Closed row 106 in `Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md`.

**Target:** the next CSO run later this week (Jill Burns, 2026-09-30).

## Decision (made — do not re-litigate)

- The 658/659 QuikTvs factors are **mean** reserves. LifePRO reserve = units × factor at policy year t. Proven on the 6/30 VALX: `RV_T` ÷ units = QuikTvs year t on 1,120 of 1,121 policies with a reserve.
- CSO turned on **Store Means** on these keys. In that mode QLAdmin reads the factor one year earlier (t−1).
- **Fix:** move every factor on these six plans one year earlier in QuikTvs.
- Warren approved the override of Closed Issue 106 for these six plans on 2026-09-30 ("We need to move them"). Every other plan keeps the 106 alignment.

## Scope

| In | Out |
|---|---|
| `rates/QuikTvs.csv` for `1659C2`, `1658C1`, `1659CR`, `1658CS`, `1659CS`, `1659SR`: all genders, classes, ages and bands (1,196 grids, 7,644 rows, EFFDATE 19000101) | `976658`, `976659` (WP riders), every other plan, `QuikNps`, `QuikCvs`, `QuikDvs`, `quikplan`, all policy tables |
| `STOREMEANS=Y` on these six plans' `QuikPlTv` keys (see below) | `CALCMIDS`, `RSVMETH`, `RSVINT`, `MORT` (CSO's E1/F1 stay) |

## Shift rule (exact)

A grid = one (PLAN, GENDER, UWCLASS, AGE, BAND, ISSCNTRY, ISSUEST, EFFDATE). Year (slot) = CNTL × 10 + i across TV0–TV9, CNTL ascending.

1. Flatten the grid to its populated years 0..L (L = last non-blank year).
2. New year k = old year k+1 for k = 0..L−1. Old year 0 (0.00) drops off.
3. New year L = old year L (hold the final value, e.g. 978). No new blanks, same CNTL rows, same row count.
4. Blank cells after L stay blank. Keep the `.00` / `2.00` number format as emitted.

Gold, 1659C2 M PR age 44:

| Year | 0 | 1 | 2 | 42 | 43 | L |
|---|---:|---:|---:|---:|---:|---:|
| Before | .00 | 2.00 | 17.00 | 751.00 | 764.00 | 978.00 |
| After | 2.00 | 17.00 | 33.00 | 764.00 | 776.00 | 978.00 |

Policy 9010713704C (25 units, year 43, Store Means on): QLAdmin reads year 42 → 764 → 19,100.00 = LifePRO `RV_T`.

## Store Means flag

- QLAdmin loads CSO's `QuikPlTv.dbf` from `C:\Users\warren\Desktop\DBF_Append_Tool\input\Product_Files_From_CSO\`. That file still has `STOREMEANS=N` on these keys.
- Jill already set Y in the 6/30 test region. Ask Warren for that updated `QuikPlTv.dbf`, or for his OK to set Y in the CSO product copy. Do not rebuild or wipe the DBF (append-only rule).
- Also set `STOREMEANS=Y` on the six plans in our `rates/QuikPlTv.csv` so conversion and CSO agree.
- **Do not ship the shifted QuikTvs with `STOREMEANS=N`.** QLAdmin would then average two shifted years and move further away.
- Robert's QLAdmin-side "store means by plan" flag, which stopped other plans from changing, is owned by QLAdmin development. Confirm it is in the region before CSO reruns. It is not a conversion change.

## Stages

Discovery is done and Warren has approved the direction. Run Intake → Planning → Dependency Gate → Risk, then stop for Development approval. Given the deadline, keep each stage short.

The Dependency Gate passes when the Store Means source (Jill's DBF or Warren's OK to set it) is settled.

## Development (after approval)

- `Issue_Log_Items/Issue_181/tools/apply_issue181_cen_tv_shift.py`, same pattern as `Issue_168/tools/apply_issue168_l14_reserve_class_replication.py`:
  - six plans only, QuikTvs (plus the `QuikPlTv` STOREMEANS cells)
  - idempotent: detect already-shifted grids with the gold above and print SKIP
  - archive copy first
  - SHA-256 guard that every other plan's rows and every other rate table are byte-identical
- Register it in `POST_EMIT_RATE_PATCHES` in **both** `app.py` and `QLA_Migration/app.py`, and bump `APP_VERSION` in both. Leave the uncommitted #172/#161 hunks in those files alone.
- `validate_issue106_quiktvs_duration.py`: exempt only the six plans and keep every other 106 anchor. Update the guide's 106 row to note the exception (Warren 2026-09-30).
- New fail-closed smoke `tools/validators/validate_issue181_cen_tv_shift.py`. It fails if:
  - the gold grid is not shifted
  - any of the 1,196 grids is not old k+1
  - STOREMEANS is not Y on the six plans
  - row counts differ from 7,644 in scope
- Add it to `SMOKE_JOBS` and to the accountability list.
- Refresh `QLA_Migration/Reports/rates/newest_plan_rate_package.json` (package date 20260831) so PLAN-KEEP passes.
- Push QuikTvs (and QuikPlTv if changed) through the Desktop DBF Append Tool. Suggested share name: `QuikTvs_Issue181_YYYYMMDD.dbf`.

## Validation

- Issue 181 smoke PASS on full Output.
- For every 6/30 VALX 658/659 policy with a reserve: units × new QuikTvs(t−1) = LifePRO `RV_T`. Expect 1,120 of 1,121. Use `evidence/issue181_valx_vs_quiktvs_20260630.csv` as the baseline.
- 106 (with the exemption), CEN NP, 169-TV, 168, 172, 176, PSUBSSEG and PLAN-KEEP smokes PASS.
- Every QuikTvs row outside the six plans is byte-identical to before.
- CSO reruns the 6/30 valuation. 9010713704C should show 19,100.00 table reserve.

## Rollback

Restore the archived `QuikTvs.csv` / `QuikPlTv.csv`, remove the `POST_EMIT_RATE_PATCHES` entry, re-append the DBF and refresh the manifest.
