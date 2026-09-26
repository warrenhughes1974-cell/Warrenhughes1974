# Issue #155 — Handoff (2026-09-24, end of Opus session)

**Stage:** Development DONE (v59.23). Next = Validation on a **6/30** full batch.  
**Read first:** `Issue_155_Risk_Review_Report.md` (spec + validation checklist), `Issue_155_Dependency_Gate.md` (Warren approvals), `Issue_155_Tracking_Sheet_Row.tsv`.

## What was built (Composer, reviewed)

- `qla_core/quikiswl_loader.py`: keeps #124 month-0 rows; adds one seed row per ISWL policy from `PFNDR_FundHistory_Extract_<QLA_VALUATION_DATE>.csv` (MLASTANNV = QL monthiversary on/before PFNDR date, MMONTH from issue, MACCTBAL = MCASHVAL = max(FUND_BALANCE,0), MLOANBAL, MSUMPREM = GROSS_DEPOSITS). Exceptions → `QLA_Migration/Reports/issue155_iswl_seed_exceptions_<date>.csv`. `stamp_iswl_miswl()` adds `MISWL` to quikprmh.csv and QuikIsrr.csv.
- `app.py` + `QLA_Migration/app.py`: v59.23; quikprmh schema + MISWL; batch step `_execute_batch_iswl_miswl_stamp` after QuikIsrr finale.
- Validators: new `tools/validators/validate_issue155_iswl_seed.py` (in SMOKE_JOBS); updated #124, #21F, `iswl_quikisrr_reconcile.py` V-ISRR-16.
- Dev proof on current Output (8/31 cut): #155/#124/#21F/#145B/#146/#151 PASS; 139,417 non-ISWL quikprmh rows unchanged. Rollback copy: `QLA_Migration/Archive/issue155_pre_dev_20260924_111001/`.

## UPDATE 11:50 — Warren said "Yes to both" (2026-09-24)

- Done: `QuikIswl.csv` removed from `PLAN_FILES`; manifest rewritten (24 pinned files, package 20260831; old manifest copied to the issue155 archive folder); rule text updated. `validate_newest_plan_rates_kept.py` PASS.
- **6/30 batch FAILED (~11:57). Not a 6/30 package. Do not load Q from it.**
  1. Source resolver used `*_20260831.csv` for PPOLC, PPBEN, PACTG, RNA, PPBENTYP (newest file wins). Same problem as the 9/18 run, which parked the later extracts and reran.
  2. quikprmh then crashed `KeyError: 'MISWL'` (`app.py` ~7522: schema lists MISWL, `row_data` does not). QuikIswl was not re-emitted (file still 11:10, 8/31 balances: 9010713704C 20260819 / 45,906.83). quikprmh.csv also still 11:10.
  3. Post-check resident-state FAIL (5 policies) ran against that mixed Output. Release smokes, #155 gold, and DBF Append were **not** completed. Desktop `output\` DBFs are still 9/22.
  Next: add `"MISWL": ""` to the quikprmh `row_data` in both `app.py` files, park the 8/31 policy extracts the way 9/18 did, rerun `QLA_VALUATION_DATE=20260630`.
- #160 approval: if the release smoke fails **only** on #160's missing archive snapshot, run `python Issue_Log_Items/Issue_A/tools/build_full_dbf_append_package.py` manually.

## (Original) Warren decisions — now approved

1. **Remove `QuikIswl.csv` from the older-cut keep-newest list.** `qla_core/newest_plan_rate_package.py` `PLAN_FILES = ("quikplan.csv", "QuikIswl.csv")`. On a 6/30 run the batch would otherwise restore the 8/31 QuikIswl (8/31 balances) and `validate_newest_plan_rates_kept.py` fails because the pinned hash is the old month-0-only file. If Warren says yes: drop QuikIswl from `PLAN_FILES`, rewrite `QLA_Migration/Reports/rates/newest_plan_rate_package.json` without the QuikIswl entry (quikplan + rates/ hashes unchanged, package date 20260831), and update `.cursor/rules/older-cut-keep-newest-plan-rates.mdc` text. This overrides a Warren-locked rule — do not do it without his yes.
2. **#160 smoke** fails only because `QLA_Migration/Archive/issue160_pre_remap/quikridr_pre_issue160.csv` is missing (since 9/13; live checks pass). Headless batch stops before DBF Append on any smoke FAIL. Ask Warren whether to run `python Issue_Log_Items/Issue_A/tools/build_full_dbf_append_package.py` manually if #160 is the only failure.

## Run (after approvals)

```text
$env:QLA_VALUATION_DATE="20260630"
python tools/batch_tests/run_full_batch_test.py
```

Older-cut mode is automatic (6/30 < 8/31 package). 6/30 Source lacks PAAGE/PAAGERAT/PDAGE/PCOVRISS/PCONT/PSUBS/PSUBSSEG — all plan/rate inputs, kept from 8/31, so OK.

## After the batch

- Output root has only quik*.csv + rates/ (move logs/reports out).
- `validate_release_closed_issues.py --smoke-only` — must include #133, #151, #152, #155, #172. #143 gold is locked to 6/30 and should PASS on a 6/30 batch (it failed on 8/31 Output only).
- #148 spot check: 9011284087C MUNIT 100, MVPU 1000. #149: all 20 plan 1L17SP policies MVPU 1000.
- #155 gold (6/30): 9010713704C seed 20260619 / MMONTH 506 / 45551.94 / MSUMPREM 22292.52; 9010713705C 26251.74; 9010713707C 8146.88; 9010779727C 0.00.
- `validate_newest_plan_rates_kept.py` PASS.
- Issue A checklist run log (`Issue_Log_Items/Issue_A/Issue_A_Conversion_Checklist.md`) — mandatory on every conversion.
- DBF Append package; confirm today's timestamps on `quikmstr.dbf` / `QuikIsrr.dbf` / `QuikIswl.dbf` in `C:\Users\warren\Desktop\DBF_Append_Tool\output\`. Confirm the Append template carries `quikprmh.MISWL`.
- Warren loads Q, runs anniversary: 9010713704C next row 2026-07-19 must start from 45,551.94 with **no** re-application of old premiums; QuikValf MACCTBAL at 6/30 = seed balance.

## Open defect from the history rebuild — fix after Warren's Q test (his call 2026-09-24 1:30 PM)

**9010801730C loses its whole account value.** Status 22, premium paying, paid to 20270709, 25 units,
plan 1659C2. The 6/30 PFNDR extract carries it with `FUND_BALANCE` 11,799.87 and PFNDRDET has 1,394
detail rows, but `qla_core/quikiswl_loader.py` line ~473 treats `VALUATION_DATE` (20260709) later than
the cut as `NO_PFNDR` and `continue`s, so the policy emits **zero** QuikIswl rows.

Fix: keep the policy. Compute the implied opening balance off the PFNDR snapshot date as usual, emit
rows only through `QLA_VALUATION_DATE`, and skip just the final-balance tie assertion when the snapshot
postdates the cut (record it as its own exception reason, e.g. `PFNDR_AFTER_CUT`, not `NO_PFNDR`).
Then add a validator check that no in-force ISWL policy (`MSTATUS < 50`) emits zero rows.

Scope on the 6/30 cut is this one policy — the other 23 `NO_PFNDR` rows are genuinely absent from the
PFNDR extract and all 23 are `MSTATUS` 53 (deceased), where no account value is correct.
Warren chose to load the current DBF into Q first and fix after his anniversary test.

## Verified fine, not defects

- 24 `OPEN_BALANCE_UNTIED` forced to 0.00: all terminated or non-forfeiture (54/53/55/56 plus 44 ETI ×2,
  45 RPU ×1). LifePRO's own `FUND_BALANCE` is `.00` on every one; its summary does not satisfy the PFNDR
  identity for these (e.g. 9010813163C deposits 16,049.90 vs deductions 5,326.94), so the itemized detail
  cannot reach zero on its own. Emitting LifePRO's stated 0.00 is right.
- `PFNDR_FundHistory_Extract_20260630.csv` and `_20260831.csv` are the same byte size but different MD5 —
  the 6/30 run read genuine 6/30 fund data (9010713704C at 20260619 / 45,551.94, not the 8/31 45,906.83).
- 434 policies with `NEGATIVE_FLOORED_ZERO` months still tie to LifePRO's reported balance.

## Known, not #155

- `iswl_quikisrr_reconcile.py` full run fails pre-existing V-ISRR-01/08/10/18/20.
- Working tree has many uncommitted changes from earlier sessions (rules, AGENTS.md, other validators, deleted CFIC dev files). Nothing committed for #155 yet.
- Post-conversion drift: QLAdmin ISWL engine credits 7%, no COI, $5 + 5% expense regardless of loaded tables (Warren raising with QLAdmin).

## Closure still owed (after Validation PASS)

Regression → Closure: Completed Issues guide row for #155 (+ note #124/#21F/#34 changes approved by Warren 2026-09-24), smoke already registered, G7 accountability IN_DATA, Test_Validation publish, resolution line.
