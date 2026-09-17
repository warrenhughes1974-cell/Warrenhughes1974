# Issue #169 — Validation Report (Stage 6)

**Date:** 2026-09-15
**Engine:** `APP_VERSION v59.14` (was v59.13)
**Valuation date:** `20260831` (active `PPOLC_PolicyMaster_Extract_20260831.csv`)
**Scope validated:** RC-1 only — `5667AT` (667 ART) net valuation premium emit
**Verdict:** **PASS** on the 9 criteria provable in our Output. Criterion 10 is **deferred to UAT** for the reason given in §4.

---

## 1. What was changed

| File | Change |
|---|---|
| `qla_core/paagerat_np_loader.py` | **New.** Reads the PAAGERAT `NP` leg and expands the attained-age vector onto the issue-age × duration grid. |
| `qla_core/rate_pipeline.py` | Wires the loader in behind a config gate; adds `paagerat_np` counters to the run summary. |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | New `paagerat_np` block, allowlist `["5667AT"]`, `issue_age_max: 75`. |
| `tools/validators/validate_issue169_667art_np.py` | **New.** Fail-closed release smoke. |
| `tools/validators/validate_release_closed_issues.py` | Registers `#169 667 ART net premium` in `SMOKE_JOBS` as required. |
| `app.py`, `QLA_Migration/app.py` | `APP_VERSION` → `v59.14`. |

The PSUBSSEG scope manifest was **not** touched — the fix rides its own `paagerat_np` gate, so
`psubsseg_substitution_scope.csv` stays byte-identical and the D-1 Closed-row notification is
satisfied without amending delivered PSUBSSEG work.

## 2. Output effect

| Table | Before | After | Delta |
|---|---:|---:|---|
| `rates/QuikNps.csv` | 87,581 | 89,317 | **+1,736 — all `5667AT`** |
| `rates/QuikPlTv.csv` | 389 | 393 | **+4 key rows — all `5667AT`** |
| All 22 other rate tables | — | — | **byte-identical** |

`5667AT` `QuikNps` went from **0 rows to 1,736** across four keys at `EFFDATE=19000101`
(M/F × PR/ST). `667 ART 95` keeps its own `19950101` generation, untouched.

## 3. Criteria results

| # | Criterion | Result |
|---|---|---|
| 1 | `5667AT` cells value-identical to PAAGERAT source | **PASS** — attained-age invariant holds on 459 cell pairs; three golden cells match to the cent |
| 2 | Every emitted grid has a matching `QuikPlTv` key row (#77) | **PASS** — 4 keys at `19000101`, all carrying `MORT=A1 RSVINT=G RSVMETH=3` |
| 3 | Every other plan's `QuikNps` byte-identical | **PASS** — `5667AT` is the only plan with any row delta |
| 4 | `5667AT` `QuikTvs` unchanged (PSUBSSEG OI-2) | **PASS** — 92,654 rows before and after, identical |
| 5 | `1668SP` (2,128) and `A96DAR` (8) unchanged | **PASS** — counts identical; CEN NP level-flatten unaffected |
| 6 | `validate_psubsseg_substitution.py` | **PASS** |
| 7 | #136 PVO flags, #158 PR segment ownership, #168 L14 reserve classes | **PASS** (see §5 on #168) |
| 8 | `validate_release_closed_issues.py --smoke-only` | **32 of 33 PASS**; only failure is pre-existing #160 (§6) |
| 9 | New validator PASS and fails closed when rows absent | **PASS** — exit 0 on current Output, exit 1 against the pre-emit snapshot |
| 10 | `MTABNET` resolves and `MRESERVE` reconciles on anchor policies | **DEFERRED — not provable in our Output** (§4) |

Validator name is `validate_issue169_667art_np.py`; Planning had written it as
`validate_issue169_667art_np_emit.py`.

## 4. Why criterion 10 cannot close on our side

`MTABNET` and `MRESERVE` are **not fields this converter emits.** A repo-wide search finds
`MTABNET` only in diagnostic scripts and analysis docs that *read* it back out of `QuikValf`.
QLAdmin computes both at valuation time from the rate tables we supply. So "re-run and watch
`MRESERVE` land on $132,229.48" requires a QLAdmin valuation run, which happens in UAT, not here.

The strongest proof available on our side was done during Development instead: the emitted grid
values reconcile **to the cent against LifePRO's `RV_MEAN_RV`** on **94 of the 96** valued rows,
including anchors `9010764158C`, `9010764248C`, `9010768802C`.

The two that do not reconcile are both known and out of scope for this pass:

| Row | LifePRO | Why it doesn't reconcile |
|---|---:|---|
| one policy in the `19950101` generation | — | `667 ART 95` keeps its own generation; not in this pass |
| `9010886099` seq 2 | $1,317.00 | Carries a reserve against **zero units** — no per-unit grid can reproduce it |

LifePRO's full `5667AT` total is **$133,546.48 across 96 valued rows**. Excluding the zero-units
row gives the **$132,229.48 / 95 rows** figure quoted in the earlier Planning and Intake documents;
both numbers are correct, they just count different things. The zero-units row is a separate
finding and is **not** fixed by this change.

**This is the one item to watch in UAT.** If `5667AT` still reserves 0 after a QLAdmin valuation,
the grid is right and the problem is downstream of us.

## 5. Regression finding worth recording

Re-running the rate emit **silently undid the Issue #168 fix**, because that fix lives in a
post-emit script (`apply_issue168_l14_reserve_class_replication.py`) rather than in the emit
pipeline. The `--smoke-only` run caught it, the script was re-applied, and #168 now passes.

`rates/QuikPlUw.csv` also dropped from 238 to 204 rows across 28 unrelated plans, because those
rows are added by `apply_issue118_output_remap.py` — another post-emit script, and one that reads a
**7/31** extract and also rewrites `quikridr`. Re-running it against an 8/31 package would have had
a far wider blast radius than this issue warrants, so `QuikPlUw.csv` was restored to its released
state instead. `5667AT` carries `PR` and `ST` in that table both before and after, so this fix is
unaffected either way.

**Standing risk:** any rate re-emit drops both post-emit fixes again. #168 is now protected by a
smoke job; the `QuikPlUw` rebuild is not, and its owning script is pinned to a stale extract.
Worth a follow-up issue.

## 6. Pre-existing failure, not introduced here

`#160 PUA terminal status inheritance` fails on a missing archive snapshot
(`QLA_Migration/Archive/issue160_pre_remap/quikridr_pre_issue160.csv`). That folder does not exist,
is gitignored, and was never committed; the job was already failing before this work. Nothing in
this change touches `quikridr` or that archive. It does, however, mean
`validate_release_closed_issues.py` currently reports **RELEASE_BLOCKED**, so this package is
**not** cleared for client handoff and the DBF Append publish has intentionally **not** been run.

## 7. Housekeeping completed

- `newest_plan_rate_package.json` refreshed at `package_valuation_date=20260831`; the only hashes
  that moved are `rates/QuikNps.csv` and `rates/QuikPlTv.csv`. Future 6/30 and 7/31 older-cut runs
  now pin to the corrected package.
- `Output/Test_Validation/rates/` refreshed with the full eight-table set. The #168 publish there
  predated this emit and was stale. Reload the set together — `QuikNps` without its matching
  `QuikPlTv` keys values 0.

## 8. Still open on this issue (client input required)

RC-2 through RC-4 are **not** addressed by this change:

| Plan(s) | LifePRO | QL | Root cause | Needs |
|---|---:|---:|---|---|
| `7619PU`, `901ADB`, `996ADB` | $405.92 | $123.00 | Absent from `CSO_Valuation_Setup.csv`, so `MORT`/`RSVINT`/`RSVMETH` emit blank and no CSO-basis reserve can compute | Client valuation assumptions |
| `196085` | $1,858.42 | $0.00 | Source rate grid stops at duration 12; the one policy is at duration 57. Valuation assumptions *are* present (`MORT=O1 RSVINT=2 RSVMETH=3`) — this one is the grid, not the setup | Actuarial decision on extension |
| `9595WP`, `967ADB`, `9SLADB` | $0.00 | $104.00 | LifePRO itself reserves 0 while QL reserves something — the reverse of the reported symptom | Confirmation from Jill that 0 is correct |
| `5667AT` seq 2 on `9010886099` | $1,317.00 | $0.00 | Reserve held against **zero units**; not reproducible from a per-unit grid | Separate question — surfaced by this pass |

Drafts for the first and third rows are in `Issue_169_Client_Asks_Drafts.md`.

## 9. Addendum 2026-09-17 — second root cause found live in Warren's Q test region

Warren deployed the 9/15 fix (§2) to his own `Q:\CSO\CSO_Test_6_30_2026` test region, ran a 6/30
valuation, and `9010800356C` still reserved $0.

**Root cause #2:** `QuikPlTv` carries **two** generations for `5667AT` `M`/`PR` (and the other
three gender/class keys) — `EFFDATE=19000101` (standard) and `EFFDATE=19950101` (`667 ART 95`,
the PSUBSSEG-scoped generation) — with **identical** `MORT=A1 RSVINT=G RSVMETH=3`. The 9/15 fix
only populated the `19000101` `QuikNps` grid. QLAdmin's engine resolves the newest `EFFDATE <=`
the valuation date, which for a policy issued after 1995 is `19950101` — and that generation's
`QuikNps` grid was empty, so `MTABNET` (and therefore `MRESERVE`) valued 0 for every `5667AT`
policy regardless of issue date, not just the ones nominally in the `667 ART 95` band.

**Fix:** added one row to the reviewed PSUBSSEG scope manifest
(`Issue_Log_Items/PSUBSSEG_Rate_Substitution/psubsseg_substitution_scope.csv`):

```
667 ART,5667AT,NP,19950101,667 ART 95,PLAN_COPY:5667AT,19950101,3,2,PDAGE;Rate_Table,Y
```

This uses the manifest's existing `PLAN_COPY:<plan>` self-copy mechanism (already proven on
`670 GL85-8` / `17085M`) to mirror `5667AT`'s standard-generation `QuikNps` grid onto its own
`19950101` band — no change to `paagerat_np_loader.py`, `rate_pipeline.py`, or any other plan.
`QuikPlTv` was **not** touched; the `19950101` key rows already existed from the original
PSUBSSEG RV entry.

**Rebuild (`APP_VERSION v59.15`):**

| Table | Before (9/15 baseline) | After | Delta |
|---|---:|---:|---|
| `rates/QuikNps.csv` | 89,317 (`5667AT`=1,736) | 91,053 (`5667AT`=3,472) | **+1,736 — all `5667AT` @ `19950101`** |
| All other rate tables | — | — | **byte-identical to the 9/15 baseline** |

`validate_issue169_667art_np.py` and `validate_psubsseg_substitution.py` (51 scope entries — 42
EXTRACT / 9 PLAN_COPY — 633,044 cells checked) both **PASS**.

**§5 standing risk materialized and was re-closed same session:** the full rate re-emit again
silently dropped the Issue #168 post-emit L14 (`1L14SC`) replication, exactly as flagged on 9/15.
`apply_issue168_l14_reserve_class_replication.py` was re-applied immediately after this fix
(+3,972 rows restoring `PQ`/`PR`/`ST` parity with `NT`); `#168 L14 reserve class keys` now
**PASS**es again in the same Output. `#160` and `#161` remain the only release-gate failures —
both pre-existing (§6), neither touches any of the 23 rate tables, so neither affects a Q-region
valuation run.

**Delivered:** DBFs rebuilt via the Desktop DBF Append Tool (44/44) and the 23 rate tables
redeployed to `Q:\CSO\CSO_Test_6_30_2026` (`QuikNps.dbf` 91,053 recs, `QuikPlTv.dbf` 394 recs) for
another valuation pass.

---

## 10. Root cause 3 (2026-09-17, Opus) � the reserve reads `QuikTvs`, not `QuikNps`

Warren revalued 6/30 in the Q region with the �9 package and `9010800356C` was **still $0**.
Both prior root causes are now retracted.

### 10.1 The �9 EFFDATE reading was wrong

QLAdmin resolves a rate generation against the **policy issue date**, not the valuation date.
All 92 pre-1995 `5667AT` policies correctly resolve to `19000101`, which already carried the
9/15 net premiums. The `19950101` mirror was harmless but could not have been the fix.

### 10.2 The reserve formula, proven from live data

`QuikPlTv` for these plans carries `STOREMEANS=N` (QuikTvs holds **terminal** factors) and
`CALCMIDS=N` (engine computes **mean** reserves), so QLAdmin builds

```text
mean reserve per unit = � � ( terminal(t-1) + net premium + terminal(t) )
```

terminal factors from `QuikTvs`, net premium from `QuikNps`. Verified against Issue #168's
independently confirmed L14 golds using our own emitted cells � `1L14SC` F / issue age 62:

| slot | term(t-1) | net prem | term(t) | mean | LifePRO |
|---:|---:|---:|---:|---:|---|
| 23 | 605.12 | 38.19 | 629.15 | **636.23** | 636.23 ? |
| 24 | 629.15 | 38.19 | 652.10 | **659.72** | 659.72 ? |

Two exact matches to the cent. The engine will not pick the net premium up unless a `QuikTvs`
row exists at the policy's generation / gender / class / issue age.

### 10.3 Why 667 ART was $0 � and the one policy that proved it

`5667AT`'s `QuikTvs` grid only ever arrived through the PSUBSSEG `667 ART 95` entry
(`5667AT,RV,19950101`). There is **no** base `19000101` RV generation, because PDAGE has no RV
rows for the base 667 ART segment. Worse, only the **ST** classes were real:

| `QuikTvs` key | rows | ages |
|---|---:|---|
| M/ST, F/ST @ `19950101` | 988 each | 00�75 (full grid) |
| M/PR, F/PR, M/00, F/00 @ `19950101` | 11 each | `AGE=00` stub only |
| anything @ `19000101` | **0** | � |

Live 6/30 `QuikValf`, 94 rows on `A1G35667AT`:

| cohort | rows | valued |
|---|---:|---:|
| issued before 19950101 (no reachable generation) | 92 | **0** |
| issued on/after 19950101, class **PR** (`AGE=00` stub only) | 1 | **0** |
| issued on/after 19950101, class **ST** (full grid reachable) | 1 | **1** |

The one that valued is `9011136641C` � M/ST, issued 19960224, age 22, duration 31, 25 units �
`MTABNET` 196.50, `MRESERVE` **98.25** = exactly half. Net premium 7.86 � 25 = 196.50. That row
also pins the slot convention: 7.86 sits at `CNTL=03` index 0, i.e. **0-based slot = duration - 1**,
confirming the #169 net-premium grid alignment is correct.

### 10.4 Fix

`Issue_Log_Items/Issue_169/tools/apply_issue169_667art_tvs_base_generation.py` clones the real ST
grid onto the missing keys: `EFFDATE=19000101` for both classes, plus the PR class at both
generations. **+5,906 rows, `5667AT` `QuikTvs` 2,020 ? 7,926.** Terminal factors stay `.00`, which
is the correct terminal reserve for an annually renewable term � the whole reserve is the
half-net-premium term.

Append-only with byte-prefix verification, idempotent skip, Archive backup, and a SHA-256 guard
proving `QuikNps`, `QuikPlTv`, `QuikGps`, `QuikCvs`, `quikplan` and `quikridr` are untouched.
It runs **after** the R7B refresh so the PVO / `*VARY*` flags stay on the values already proven to
work for M/ST.

| Policy | key | expected | computed |
|---|---|---:|---:|
| `9010800356C` | M/PR age 39 dur 40, 200u | 8,239.00 | **8,239.00** ? |
| `9010768802C` | F/PR age 28 dur 41, 30u | 490.35 | **490.35** ? |
| `9010764248C` | F/PR age 22 dur 41, 50u | 474.50 | **474.50** ? |
| `9011136641C` | M/ST age 22 dur 31, 25u | 98.25 | **98.25** ? |

All 3,472 `5667AT` net-premium addresses now have a terminal-reserve row behind them (was 3,472
uncovered). New validator `tools/validators/validate_issue169_667art_tvs_reachable.py` **PASS**.
`validate_issue169_667art_np.py`, `validate_psubsseg_substitution.py` and
`validate_issue168_l14_reserve_class_replication.py` all still **PASS**; `#160` / `#161` remain the
only release-gate failures and are pre-existing (`#160` is a missing local Archive snapshot).

### 10.5 Drop protection

The #168 loss on 9/16 happened because that post-emit patch was never wired into the rate finale.
`POST_EMIT_RATE_PATCHES` (`APP_VERSION v59.16`) now re-applies both #169 and #168 at the end of the
rate-only path **and** the batch finale. The newest plan/rate hash manifest was refreshed � it was
already stale from the 9/16 `QuikNps`/`QuikPlTv` work and would have failed a 6/30 keep-gate run.

### 10.6 Same defect on 12 other plans � not fixed here

Plans carrying a `QuikNps` key with no real `QuikTvs` grid behind it, against the live 6/30 run:

| coverage | plan | valf rows | at $0 |
|---|---|---:|---:|
| 667 ART | `5667AT` | 94 | 93 |
| **L10** | `5L0110` | 122 | **122** |
| **L05** | `5L0510` | 10 | **5** |
| ADB / WP riders | `901ADB`, `996ADB`, `976659`, `9L01WP` | 31 | 0 |

Plans whose net premiums all have a reserve row: **3.9% zero**. Misaligned plans: **85.6% zero**.
`5L0110` is Issue #170's "L10 et al are not matching"; `5L0510` is the L05 remainder left open on
#168. Warren scoped this pass to 667 ART only.

**Delivered:** DBFs rebuilt via the Desktop DBF Append Tool (44/44) and the 23 rate tables
redeployed to `Q:\CSO\CSO_Test_6_30_2026` � `QuikTvs.dbf` 92,654 ? 98,560 records, every other rate
table unchanged. Verified in place by
`Issue_Log_Items/Issue_169/tools/verify_667art_tvs_in_q.py`: 0 uncovered addresses, all
four anchors reproduce LifePRO to the cent. Ready for another valuation pass.
