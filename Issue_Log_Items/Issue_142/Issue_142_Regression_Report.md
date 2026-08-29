# Issue 142 — Regression Report

**Date:** 2026-08-29
**Engine:** v59.04
**Scope:** Active SL rows emit as 9SUBLF (MVPU=0); Issue #27 suppression narrowed to non-active SL (Warren override 2026-08-29).

## Verdict: PASS

Evidence: `evidence/issue142_regression_summary.json` (script `evidence/_regression_issue142.py`).

## Checks

| # | Check | Result | Detail |
|---|-------|--------|--------|
| 1 | Engine partition simulation (v59.04 app.py block vs 20260630 PPBEN) | PASS | 68 SL rows → 22 Active emit / 46 suppressed; all 22 routed to 9SUBLF with VALUE_PER_UNIT=0 |
| 2 | Transform isolation | PASS | prepare_active_sl_for_emit touched zero non-active-SL rows |
| 3 | quikridr non-9SUBLF rows unchanged | PASS | 6,934 rows hash-identical (MD5) to last packaged baseline (DBF_Append_Tool input) |
| 4 | quikridr 9SUBLF rows | PASS | 22 rows; every MVPU=0; amount-insured contribution 0.00 |
| 5 | No duplicate (MPOLICY, MPHASE) keys | PASS | 0 collisions across 6,956 rows |
| 6 | quikplan delta | PASS | Exactly one new 9SUBLF row; all 141 other rows byte-identical to baseline |
| 7 | Other Output tables untouched | PASS | quikmstr et al. retain 8/28 batch timestamps; Issue 142 wrote only quikridr + quikplan |

## Defect found during regression (fixed before Closure)

- **9SUBLF VARGP** was seeded as `3` (varies by attained age) but 9SUBLF emits no QuikGps grid; Issue A7 validator correctly flagged it (a dangling code-3 pointer causes "Values Not on File" in QLAdmin). Fixed to `4` (no rate table on file) in `qla_core/issue142_sl_rider.py` and patched in Output + Test_Validation. A7 now PASS.

## Stale-count validator updates (class A, guide-sanctioned)

Issue 142 legitimately adds 22 quikridr rows and 1 quikplan row; two prior validators carried hardcoded pre-142 counts and were made Output-aware (substantive checks untouched, original book guards preserved):

- `validate_issue55_munit_floor.py` — row guard now: non-9SUBLF count == 6,934 (9SUBLF counted separately). All floor/trace/leading-dot checks unchanged, PASS.
- `validate_issue70_loanintx.py` — LOANINTX count guard now excludes the seeded 9SUBLF plan (A=137 pre-142 book). PCOVR fidelity and traces unchanged, PASS.
- Cascade: `validate_issue143_smoke.py` condition 7 (embeds #55) now PASS.

## Release smoke suite (`--smoke-only`)

All smokes PASS including the new **#142 SL rider 9SUBLF** job, except one **pre-existing** failure unrelated to Issue 142:

- **#59 MSTATUS allowlist FAIL** — quikmstr status drift from the 8/28 batch (23 unexpected changes, e.g. 9010521213C 22→53 expected 50). quikmstr last written 2026-08-28 10:25, before any Issue 142 work; Issue 142 writes only quikridr/quikplan. Needs its own review before release handoff.

## Accountability

`validate_issue_log_accountability.py`: IN_DATA 70 / WARN 14 / GAP 4. **#142 = IN_DATA.**
Remaining GAPs all pre-existing on tables Issue 142 never touched: #76 (ETI/RPU MLASTANN drift, none of the 22 SL policies in the fail list), #114 (quikbenh MBENTYP=10 above midyear floor), #59:010521213C (quikmstr spot), #135 (claims marker payee). Pre-142 baseline report had 13 GAPs; this run has 4.

## DBF Append package

`build_full_dbf_append_package.py` headless: 43/43 APPEND OK; quikridr.dbf (6,956) / quikplan.dbf (142) / claims alignment PASS; Desktop output timestamps 2026-08-29 12:38.
