# QLAdmin V5 Rate Import Checklist (R6)

> **SANDBOX ONLY.** Import these DBFs into a QLAdmin **sandbox/test** environment first.
> Do **not** load into production until sandbox functional validation passes. These tables
> carry deferred actuarial assumptions (blank placeholders) by design.

Source package: 16 emitted DBFs in `plan_analysis/phase_r5_rate_loader/emitted_dbf/`
(see `qla_import_package_manifest.csv` for paths, row counts, EFFDATE). All EFFDATE-bearing tables
carry `EFFDATE = 19000101`; member/dimension tables `QuikPlGd/QuikPlUw/QuikPlBd/QuikPlSt` have no
EFFDATE field by design.

## Prerequisite product tables (must already exist in the target QLAdmin environment)
- **QuikPlan** — every PLAN referenced by the rate keys must already be set up and authoritative.
- Underlying product/valuation setup as required by QLAdmin V5 for the families being loaded.
- Confirm the target environment's PLAN universe contains the authoritative plans in the manifest
  (the emitted keys reference governed quikplan PLAN codes).

## Backup / rollback (before any load)
1. Take a full backup/snapshot of the sandbox QLAdmin rate + key tables you are about to touch.
2. Record current row counts for each target table.
3. The emitted package is rollback-safe and isolated; to roll back, restore the snapshot. Do **not**
   hand-edit emitted DBFs.

## Recommended load order
1. **QuikPlan must already exist** (prerequisite — do not load here).
2. **Member / dimension tables** (declare each plan's valid segmentation members before keys/factors):
   1. `QuikPlGd`  *(gender members)*
   2. `QuikPlUw`  *(underwriting-class members)*
   3. `QuikPlBd`  *(band members — `BDLOWVAL` is a deferred 0 placeholder, see warnings)*
   4. `QuikPlSt`  *(state/country members — `MLOANINT` blank placeholder)*
   5. `QuikPlNb`  *(new-business window, `EFFDATE = 19000101`, open `TERMDATE`)*
3. **Rate key tables** (load before factor tables so factors resolve to a parent key):
   1. `QuikPlGp`
   2. `QuikPlDv`
   3. `QuikPlDb`
   4. `QuikPlCv`
   5. `QuikPlTv`  *(shared by Terminal Reserve **and** Net Premium)*
4. **Factor tables:**
   1. `QuikGps`
   2. `QuikDvs`
   3. `QuikDbs`
   4. `QuikCvs`
   5. `QuikTvs`
   6. `QuikNps`

## Load steps (per table)
- [ ] Confirm the target table is backed up.
- [ ] Import the DBF (append/replace per sandbox procedure).
- [ ] Confirm imported row count equals the manifest `ROW_COUNT`.
- [ ] Confirm `EFFDATE = 19000101` on all imported rows.

## Validation steps after load
- [ ] Run `qla_post_import_validation_checklist.md` end to end.
- [ ] Execute the lookup cases in `rate_lookup_test_matrix.csv` (record `TEST_RESULT`).
- [ ] Confirm no orphan factor rows / no empty key rows.
- [ ] Confirm representative premium / CV / DB / reserve lookups return expected values.

## Known warnings (do not treat as blockers for import)
- Actuarial assumptions (MORT/RSVINT/RSVMETH/INTMETHCV/INTMETHTV/ETIMORT/NFOINT/STOREMEANS/CALCMIDS)
  are blank deferred placeholders — reserve/NP/CV runtime *calculations* may be incomplete until supplied.
- 260 cash-value factors are precision-reduced (1 decimal) to fit CHAR(7); magnitude preserved.
- Plan `1L10OD` AGE 100 capped to 99 (collision-protected; genuine AGE-99 value retained).
- Excluded TYPE_CODEs not loaded: `NN, PN, TP, TX, UF, NF, SL`.
- Member tables: code lists are derived from validated segmentation tuples; descriptions use standard
  labels. `QuikPlBd.BDLOWVAL` (band breakpoints) = 0 placeholder, `QuikPlSt.MLOANINT` (loan interest)
  blank, and `QuikPlNb.TERMDATE` blank — all deferred business inputs, to be supplied before any
  production load that relies on banding/loan-interest behavior.
