# Issue 181 — Dependency Gate

**Issue:** 181 — 658/659 QuikTvs Duration Shift
**Framework stage:** Dependency Gate
**Date:** 2026-09-30
**Result:** PASS

## Checklist

### Source data

| Check | Status | Detail |
|---|---|---|
| LifePRO extract present | Met | 6/30 comparison already built: `evidence/issue181_valx_vs_quiktvs_20260630.csv` (1,230 rows). |
| Row count > 0 | Met | 1,121 rows with a LifePRO reserve; 1,120 tie to QuikTvs at the current policy year. |
| Columns documented | Met | Policy, plan, sex, class, age, issue date, policy year, units, LifePRO per-unit reserve, QuikTvs at t−2 through t+1. |
| Extract date matches the batch under test | Met | 6/30/2026 valuation, which is the file Jill compared. |
| Re-extract required | N/A | Not for this shift. |

### Field definitions

| Check | Status | Detail |
|---|---|---|
| QLAdmin target table | Met | `rates/QuikTvs.csv`. TV0–TV9, CHAR(7). Year = CNTL × 10 + slot. |
| Target meaning | Met | These factors are mean reserves. With Store Means on, reserve = units × the factor. |
| LifePRO meaning | Met | `RV_T` = units × the factor at the current policy year. |
| Transformation | Met | New year k = old year k+1. Final populated year stays. Year 0 (`.00` on every grid) drops off. |

### Client clarification

| Check | Status | Detail |
|---|---|---|
| Scope | Met | Jill named 1658C1, 1658CS, 1659C2, 1659CS, 1659CR, 1659SR. Waiver riders 976658 and 976659 stay out. |
| Edge rule | Met | Do not invent a factor past the last populated year. Repeat that last factor so the row does not grow. No 6/30 in-force policy sits on that last cell except 9010756091C, which is already past the grid. |
| Store Means | Met | Jill turned it on in the 6/30 region on 2026-09-28. This issue does not set it and must not reload QuikPlTv over it. |
| Acceptance | Met | For a policy with a LifePRO reserve, units × the shifted factor at year t−1 equals LifePRO `RV_T`. Gold: 9010713704C year 43 reads 764, and 25 × 764 = 19,100.00. |

### Evidence

| Check | Status | Detail |
|---|---|---|
| Example policies | Met | 9010713704C, 9010718309C, 9010755152C, plus one each on 1658CS, 1659CS, and 1659SR in the Planning trace. |
| Client support | Met | Jill's 2026-09-29 email, and her 2026-09-28 note that Store Means landed on t−1. |
| Before-state measurable | Met | Current QuikTvs on disk. |

### Regression guards

| Check | Status | Detail |
|---|---|---|
| Issue 25 MPOLICY padding | Met | No policy table in scope. |
| Issue 26 MPREM | Met | No premium field in scope. |
| Unrelated rulebooks | Met | Output patch only. No rulebook edit. |
| Issue 106 | Met, with written override | A one-year move undoes 106 on these six plans. Warren approved it on 2026-09-30 ("We need to move them"). The 106 guide row must note that exception. Every other 106 anchor stays. |
| Issues 172 and 176 | Met | Those own QuikCvs, not QuikTvs. |

## What this gate does not include

Robert's QLAdmin change, so that checking Store Means does not move every other plan, is his product work. It is not a missing file for this shift. Our table change does not alter those other plans' factors.

## Gate result

**PASS.** Proceed to Risk. No code in this stage.
