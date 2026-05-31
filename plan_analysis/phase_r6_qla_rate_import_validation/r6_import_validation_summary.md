# R6 — QLAdmin Rate Import & Functional Validation Summary

Practical import-readiness package for the R5 baseline rate library. **Read-only:** no loaders
redesigned, no governance/claims changes, no emitted values altered. Status: **ready for QLAdmin
sandbox import testing.**

## What was produced
Package folder: `plan_analysis/phase_r6_qla_rate_import_validation/`
- `qla_import_package_manifest.csv` — 16 tables, paths, row counts, EFFDATE, status (all **PASS**).
- `qla_rate_import_checklist.md` — load order, prerequisites, backup/rollback, sandbox warning.
- `qla_post_import_validation_checklist.md` — structural, referential, functional, regression checks.
- `rate_test_policy_selection.csv` — 29 representative test cases across all families + special plans.
- `rate_lookup_test_matrix.csv` — 29 concrete lookup cases with **real EXPECTED_VALUE** from the DBFs;
  `TEST_RESULT` left blank for the QLAdmin tester.
- `_build_r6_package.py` — regenerates the manifest + test CSVs from the emitted DBFs.

The 16 emitted DBFs are referenced (not duplicated) via the manifest; they remain the single source
in `plan_analysis/phase_r5_rate_loader/emitted_dbf/`.

## What should be loaded (recommended order)
1. **QuikPlan** (prerequisite — must already exist).
2. Member/dimension tables: `QuikPlGd → QuikPlUw → QuikPlBd → QuikPlSt → QuikPlNb` (declare each plan's
   valid segmentation members before keys/factors).
3. Rate-key tables: `QuikPlGp → QuikPlDv → QuikPlDb → QuikPlCv → QuikPlTv` (QuikPlTv shared by TV+NP).
4. Factor tables: `QuikGps → QuikDvs → QuikDbs → QuikCvs → QuikTvs → QuikNps`.

| Table | Rows | EFFDATE |
|---|---|---|
| QuikGps / QuikDvs / QuikDbs | 1,123 / 3,978 / 1,380 | 19000101 |
| QuikCvs / QuikTvs / QuikNps | 25,717 / 26,097 / 26,650 | 19000101 |
| QuikPlGp / QuikPlDv / QuikPlDb / QuikPlCv / QuikPlTv | 13 / 20 / 12 / 70 / 112 | 19000101 |
| QuikPlGd / QuikPlUw / QuikPlBd | 110 / 80 / 66 | n/a (no EFFDATE field) |
| QuikPlSt / QuikPlNb | 64 / 64 | n/a / 19000101 |
| **Total** | **85,556** | all EFFDATE rows = 19000101 |

## What should be tested
- Structural: DBFs open, row counts match, EFFDATE = 19000101 everywhere.
- Referential: no missing PLAN refs, no orphan factors, no empty keys; QuikPlTv serves TV **and** NP.
- Functional: premium / CV / DB lookups return expected values; reserves where applicable.
- Special scenarios (in the lookup matrix, with real expected values):
  - `1L10OD` AGE 99 `CV0 = 1000.00` (AGE-100 capped→99, genuine value retained).
  - `2665ST` `DB0 = 28134.0` (large DB factor stored as 7-char text).
  - `A96DAR` `CV5 = 12164.9` (large CV factor, precision-reduced to fit, magnitude intact).

## Known warnings (documented, not suppressed)
- **Actuarial assumptions deferred** — MORT/ETIMORT/RSVINT/RSVMETH/INTMETHCV/INTMETHTV/NFOINT/
  STOREMEANS/CALCMIDS are blank configurable placeholders; reserve/NP/CV runtime *calculations* may
  be incomplete until supplied. Not a blocker for import package creation.
- **260 precision-reduced cash values** — stored at 1 decimal to fit CHAR(7); **magnitude preserved**.
- **AGE 100 capped to 99** (plan `1L10OD`) with collision protection (genuine AGE-99 retained, audited).
- **Excluded TYPE_CODEs not loaded:** `NN, PN, TP, TX, UF, NF, SL` (inventoried only).
- **Member-table deferred placeholders** — code lists derived from validated segmentation tuples and
  standard label descriptions; but `QuikPlBd.BDLOWVAL` (band breakpoints) = 0, `QuikPlSt.MLOANINT`
  (loan interest) blank, `QuikPlNb.TERMDATE` blank. These are business inputs pending; supply before a
  production load that relies on banding/loan-interest/termination behavior.

## What is not yet finalized
- Actuarial assumption population (then re-emit and re-validate CV/TV/NP keys).
- ISSCNTRY/ISSUEST defaults (`0000`/`00`) pending confirmation of any state/country variation.
- Live QLAdmin read-back confirmation that >9999.99 text factors parse as expected at runtime.

## Open risks
- Reserve/NP functional results depend on assumptions still deferred — expect partial reserve calc
  behavior in sandbox until assumptions are loaded.
- The supplied reference DBF population was disjoint from these client plans (R3), so value-level
  ground-truth comparison happens **in QLAdmin** during this sandbox test, not against the reference set.

## Exact commands to regenerate the package
```bash
python plan_analysis/phase_r5_rate_loader/rate_loader_emit.py          # (re)emit the 16 DBFs (gated)
python plan_analysis/phase_r5_rate_loader/effdate_verification.py      # confirm EFFDATE = 19000101
python plan_analysis/phase_r6_qla_rate_import_validation/_build_r6_package.py  # build manifest + tests
```
