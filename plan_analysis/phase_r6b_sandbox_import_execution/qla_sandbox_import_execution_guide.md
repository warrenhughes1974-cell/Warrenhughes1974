# QLAdmin Sandbox Import Execution Guide (R6B)

> **SANDBOX ONLY.** Execute this guide in a QLAdmin **test/sandbox** environment.
> Do **not** import into production. All testing must be reversible via backup/restore.

## Purpose

Step-by-step instructions to import the R5-generated rate library (16 DBFs) and verify
post-load integrity before functional testing.

**Source location:** `plan_analysis/phase_r5_rate_loader/emitted_dbf/`  
**Manifest:** `sandbox_import_manifest.csv`  
**Validation matrix:** `rate_import_validation_matrix.csv`

---

## Prerequisites

Before importing any rate table:

1. **QuikPlan** must already exist — every PLAN referenced by member/key/factor tables (64 distinct plans) must be set up in governed quikplan.
2. **Product authority complete** — P3/P3E/P3G governance satisfied (no synthetic or passthrough PLANs).
3. **Sandbox environment** identified and isolated from production.
4. **QLAdmin administrator access** with permission to import DBF tables.
5. **Business tester** assigned to complete `rate_import_validation_matrix.csv` and `qladmin_lookup_trace_template.csv`.

---

## Backup (mandatory before import)

1. Take a full backup/snapshot of the sandbox QLAdmin database (or at minimum all tables listed below if they already exist).
2. Record current row counts for each target table.
3. Document backup location, timestamp, and operator name.
4. Confirm restore procedure is tested and available.

**Tables to back up if present:**

- Member: `QuikPlGd`, `QuikPlUw`, `QuikPlBd`, `QuikPlSt`, `QuikPlNb`
- Rate keys: `QuikPlGp`, `QuikPlDv`, `QuikPlDb`, `QuikPlCv`, `QuikPlTv`
- Factors: `QuikGps`, `QuikDvs`, `QuikDbs`, `QuikCvs`, `QuikTvs`, `QuikNps`

---

## Recommended load order

Load in sequence. Do **not** load factor tables before their parent rate-key tables.
Load member tables **before** rate keys.

| Seq | Table | Rows | Category |
|---:|---|---:|---|
| 1 | QuikPlGd | 110 | Member — gender |
| 2 | QuikPlUw | 80 | Member — UW class |
| 3 | QuikPlBd | 66 | Member — band |
| 4 | QuikPlSt | 64 | Member — state/country |
| 5 | QuikPlNb | 64 | Member — new business |
| 6 | QuikPlGp | 13 | Rate key — gross premium |
| 7 | QuikPlDv | 20 | Rate key — dividend |
| 8 | QuikPlDb | 12 | Rate key — death benefit |
| 9 | QuikPlCv | 70 | Rate key — cash value |
| 10 | QuikPlTv | 112 | Rate key — terminal reserve + net premium |
| 11 | QuikGps | 1,123 | Factor — gross premium |
| 12 | QuikDvs | 3,978 | Factor — dividend |
| 13 | QuikDbs | 1,380 | Factor — death benefit |
| 14 | QuikCvs | 25,717 | Factor — cash value |
| 15 | QuikTvs | 26,097 | Factor — terminal reserve |
| 16 | QuikNps | 26,650 | Factor — net premium |

**Subtotals:** Member = 384 rows | Keys + factors = 85,172 rows | **Full library = 85,556 rows**

---

## Import procedure (per table)

For each table in load order:

1. Locate source DBF: `plan_analysis/phase_r5_rate_loader/emitted_dbf/<TableName>.dbf`
2. Confirm file opens without error (optional: compare row count to manifest).
3. Import using sandbox QLAdmin DBF import procedure (append or replace per local policy).
4. Record `IMPORT_STATUS` in `sandbox_import_manifest.csv` (e.g. `IMPORTED`, `FAILED`, `SKIPPED`).
5. Verify imported row count matches manifest `ROW_COUNT`.
6. If import fails, **stop** — do not proceed to next table until resolved or rolled back.

---

## Post-load verification (structural)

Complete test **R6B-017** in `rate_import_validation_matrix.csv`:

- [ ] All 16 tables imported successfully (or documented skip with reason).
- [ ] Row counts match manifest for every table.
- [ ] No import errors in QLAdmin log.
- [ ] All EFFDATE-bearing tables contain **only** `19000101` (keys, factors, `QuikPlNb`).
- [ ] No blank PLAN values in any imported table.
- [ ] No orphan PLAN references (member PLANs exist in keys; key PLANs have member rows).
- [ ] No factor rows without matching rate-key segmentation tuple.
- [ ] No rate-key rows without corresponding factor coverage (where family applies).

---

## Post-load verification (functional — see functional test script)

After structural checks pass:

1. Execute `qla_functional_test_script.md` step by step.
2. Record results in `rate_import_validation_matrix.csv`.
3. Record factor lookups in `qladmin_lookup_trace_template.csv`.
4. Escalate any `PASS_FAIL = FAIL` with TEST_ID and NOTES.

---

## Known expected placeholders (not defects)

| Field | Table | Expected | Classification |
|---|---|---|---|
| `BDLOWVAL` | QuikPlBd | `0` | `MEMBER_PLACEHOLDER_DEFERRED` |
| `MLOANINT` | QuikPlSt | blank | `MEMBER_PLACEHOLDER_DEFERRED` |
| `TERMDATE` | QuikPlNb | blank/open | `MEMBER_PLACEHOLDER_DEFERRED` |
| MORT/RSVINT/etc. | QuikPlCv/QuikPlTv | blank | Actuarial assumption deferred |

Do **not** fail import or structural verification because of these placeholders.

---

## Rollback procedure

If import or validation fails:

1. **Stop** further imports immediately.
2. Restore sandbox from pre-import backup/snapshot.
3. Document failure: table, error message, operator, timestamp.
4. Do **not** hand-edit emitted DBFs.
5. If conversion-side issue suspected, escalate to conversion team with TEST_ID and log excerpt.
6. Re-attempt import only after root cause is understood and backup is confirmed available.

**Production environments must remain untouched throughout R6B.**

---

## Regenerate R6B artifacts

```bash
python plan_analysis/phase_r6b_sandbox_import_execution/_build_r6b_package.py
```

---

## Related packages

- R6 rate import validation: `plan_analysis/phase_r6_qla_rate_import_validation/`
- R6A member table validation: `plan_analysis/phase_r6a_member_table_validation/`
