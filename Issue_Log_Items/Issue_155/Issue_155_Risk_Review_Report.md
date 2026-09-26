# Issue #155 — Risk Review Report

**Date:** 2026-09-24  
**Stage:** Risk (G3). Read-only simulation; no production code.  
**Script:** `tools/_risk_review_issue155_iswl_seed.py`  
**Evidence:** `evidence/issue155_risk_simulation_20260630.json`, `evidence/issue155_risk_seed_preview_20260630.csv`  
**Package under test:** full `QLA_Migration/Output/` (**8/31 cut** — batch 2026-09-22, `QLA_VALUATION_DATE=20260831`) paired with PFNDR **6/30** seeds; QLAdmin QuikIswl from Q test region (6/30 data, 9/23 anniversary). Correction 2026-09-24: Output is the 8/31 cut, not 6/30. The quikprmh "left blank" count therefore includes July–August premiums. Development reads the PFNDR extract matching `QLA_VALUATION_DATE`, so seed pairing follows the batch cut.

## Recommendation: **Conditional Go**

Scope = QLAdmin account equals the LifePRO fund on the conversion date. Conditions below are mandatory.

## Before / after (simulated)

| Measure | Before | After |
|---|---:|---:|
| QuikIswl rows | 2,268 (month 0) | 2,268 month 0 **unchanged** + 2,244 seed rows |
| ISWL policies whose QL account = LifePRO at seed date (of 1,097 comparable) | **0** | All except negative-fund policies (floored to 0.00, listed) |
| Account total, 1,097 comparable policies | QL $15,408,538 | LifePRO $13,397,143 (−$2.01M) |
| quikprmh rows | 214,339 | 214,339 (no rows added/removed) |
| quikprmh ISWL rows with `MISWL` | 0 | 73,346 stamped; 1,575 left blank (paid after seed monthiversary) |
| quikprmh non-ISWL rows | 139,417 | **unchanged** |
| QuikIsrr rows with `MISWL` | 0 of 102 | 101 stamped; 1 blank |

QLAdmin runs **high**, not low, across the book: with no COI it overstates the account on most policies (largest: 9011072813C QL 159,553.57 vs LifePRO 60,980.19). Valuation reserves where the account exceeds the table reserve will fall once seeded. Jill's 3 policies move the other way (+$14k on 9010713704).

## Seed-date quality (2,245 policies with PFNDR 6/30)

| Group | Count | Treatment |
|---|---:|---|
| Active (22), LifePRO date on QL monthiversary, June 2026 | 1,061 | Seed as is |
| MMONTH vs QLAdmin's own row on same date | 1,097 checked | **0 mismatches** |
| Active, LifePRO monthiversary day ≠ QL issue day | 23 | MLASTANNV = QL monthiversary on/before LifePRO date; list (e.g. 9010722516C issue 07/01, LifePRO 06/11) |
| Active, stale fund date (fund stopped 2002–2025) | 28 | Seed at that date; list |
| Terminated / other statuses (53, 55, 54, 57, 44, 45, 50, 56, 90) | 1,132 | Seed (same all-status scope as #124); most dates are termination dates |
| LifePRO date after 6/30 (9010801730C, 2026-07-09) | 1 | **Exclude from seed**, keep month-0, list |
| Negative LifePRO fund | 247 | Seed 0.00 (Warren); list |
| No PFNDR row | 23 | Month-0 only; list |

## Premium check

Stamped premium total equals LifePRO lifetime deposits (`GROSS_DEPOSITS`) on 1,585 of 2,245. Differences do not create double counting because stamped rows are never re-applied:

- 144 policies have no quikprmh history at all (e.g. 9010751933C, deposits 33,495.00).
- 447 have less history than LifePRO deposits (pre-2018 lump below lifetime).
- 69 have more (quikprmh includes rider premium not deposited to the fund, e.g. 9010799675C).

Double-count risk exists only on **blank** rows: 1,575 rows paid after the seed monthiversary. For active aligned policies these are premiums LifePRO had not yet applied at the seed date — correct to leave for QLAdmin.

## Regression surfaces

| Surface | Impact | Action |
|---|---|---|
| `tools/validators/validate_issue124_quikiswl.py` | Fails on MMONTH ≠ 0 | Update: month-0 checks apply to month-0 rows; seed rows validated by new #155 validator |
| `tools/validators/iswl_quikisrr_reconcile.py` V-ISRR-16 | Requires `MISWL` blank (#34 design) | Update per Warren OK 2026-09-24 |
| #145B / #146 / #151 QuikIsrr exclusions | Rows stay excluded; only `MISWL` added to remaining rows | Smokes must still PASS |
| #21F CONV_ADJ | Amounts unchanged; `MISWL` added | `validate_issue21f_premium_adjustment.py` must PASS |
| quikprmh / QuikIsrr CSV header | New trailing column `MISWL` (field exists in QLAdmin DBF template) | Confirm Append Tool maps it; `TABLE_SCHEMAS["quikprmh"]` in app.py if schema check is strict |
| QuikIswl DBF | Two rows per seeded policy; QL index is MPOLICY + descending MLASTANNV, latest wins | Proven by QL's own multi-row history |
| Surrender charges (QuikIssc 14 yrs) | 0 policies issued after 2012-06-30 | None |

Untouched: quikridr (MUNIT, MVPU, MPREM), quikmstr, quikplan, `rates/` (older-cut rule), QuikUint, QuikCoi.

## Residual risks (accepted by scope)

1. **Post-conversion drift:** ≈ +$113/month on 9010713704 until QLAdmin interest/COI/expense match LifePRO. Warren raising with QLAdmin.
2. **QLAdmin valuation projection:** if QuikValf projects the account with the same engine, reserves still differ from LifePRO (reserve formula follow-up issue).
3. **`MISWL` honored by anniversary:** inferred from QL stamping behavior; prove in Validation by running anniversary in Q and confirming no premium re-application.

## Recommended Development task (surgical)

1. `qla_core/quikiswl_loader.py` — add seed rows from `PFNDR_FundHistory_Extract_<QLA_VALUATION_DATE>.csv`: MLASTANNV = QL monthiversary on/before PFNDR `VALUATION_DATE` (skip if date > valuation date), MMONTH from issue, MACCTBAL = MCASHVAL = max(FUND_BALANCE, 0), MLOANBAL, MSUMPREM = GROSS_DEPOSITS; keep month-0 rows.
2. Same step: add `MISWL` to `quikprmh.csv` and `QuikIsrr.csv` for ISWL policies — next monthiversary on/after paid/surrender date when ≤ seed date; else blank. Non-ISWL rows byte-identical except the new empty column.
3. Exception list to `QLA_Migration/Reports/` (floored, misaligned, stale, post-valdate, no PFNDR).
4. Validator `tools/validators/validate_issue155_iswl_seed.py` (fail-closed): seed balance = PFNDR (or 0.00 floor) for every seeded policy; gold 9010713704C 2026-06-19 / 506 / 45,551.94 / MSUMPREM 22,292.52; no stamped MISWL after seed date; month-0 rows unchanged; non-ISWL quikprmh unchanged.
5. Update #124 and #34 validators as above; bump `APP_VERSION` in both app.py files only if app.py changes.
6. Full 6/30 batch (`QLA_VALUATION_DATE=20260630`, older-cut plan/rate keep), DBF Append, then Warren runs anniversary + valuation in Q.

## Validation checklist

- [ ] New #155 validator PASS on full Output
- [ ] #124, #21F, #34, #145B, #146, #151 validators PASS
- [ ] `validate_release_closed_issues.py --smoke-only` PASS
- [ ] `validate_newest_plan_rates_kept.py` PASS
- [ ] Non-ISWL quikprmh rows identical (hash compare, excluding new column)
- [ ] Q: anniversary run — 9010713704C next row 2026-07-19 starts from 45,551.94, no premium re-application
- [ ] Q: QuikValf MACCTBAL at 6/30 = seed balance for seeded in-force policies

## Gate G3

- [x] Risk report published with recommendation
- [x] Impact quantified
- [x] Unrelated fields marked untouched
- [x] #25 / #26 preserved
- [ ] Warren acknowledges → "Approved for Development"
