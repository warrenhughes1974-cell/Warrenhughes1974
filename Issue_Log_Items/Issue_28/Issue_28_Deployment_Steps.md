# Issue #28 — Deployment Steps

**Version:** v57.35  
**Issue:** Incorrect Plan Number Mapping  
**Date:** 2026-06-27

---

## Pre-deployment checklist

- [ ] Confirm target environment has v57.35 code (`app.py` header)
- [ ] Confirm catalog files identical (byte-level): `plan_governance/product_catalog_crosswalk.csv` ↔ `QLA_Migration/Mapping/product_catalog_crosswalk.csv` (142 lines / 141 data rows)
- [ ] Confirm no local overrides to `CROSSWALK_OVERLAY` unless intentional
- [ ] Archive v57.34 output as rollback baseline (if not already in `Issue_Log_Items/Issue_28/evidence/`)
- [ ] Notify client of planned PLAN code changes (33 mappings + DISCHO25)

---

## Deployment steps (staging / UAT environment)

### Step 1 — Deploy code

Deploy the following changed files from the v57.35 release candidate:

| File | Change |
|------|--------|
| `qla_core/product_catalog_authority.py` | Phase 1 authority + Phase 2 P3E default |
| `app.py` | v57.35 + post-quikplan P3E refresh |
| `QLA_Migration/app.py` | Mirror of app.py |
| `plan_governance/product_catalog_crosswalk.csv` | DISCHO25 row |
| `QLA_Migration/Mapping/product_catalog_crosswalk.csv` | Synced catalog |
| `tools/validators/validate_issue28_plan_mapping.py` | Issue #28 validator |

**Do not deploy:** rulebooks, Master_Crosswalk, Policy Form Crosswalk xlsx (unchanged).

### Step 2 — Environment variables

| Variable | v57.35 default | Staging recommendation |
|----------|----------------|------------------------|
| `QLA_CLOSED_MPLAN_AUTHORITY` | **1** (ON) | Leave ON for full Phase 2 behavior |
| `QLA_ALLOW_LEGACY_MPLAN_FALLBACK` | 0 | Leave OFF |
| `CROSSWALK_OVERLAY` | 0 | Leave OFF |
| `QLA_RUN_MODE` | — | `UAT` for staging batch |

To disable P3E MPLAN alignment only: set `QLA_CLOSED_MPLAN_AUTHORITY=0`.

### Step 3 — Run full batch

```powershell
cd C:\Users\warren\Documents\GitHub\Warrenhughes1974
python tools/batch_tests/run_full_batch_test.py
```

Expected: exit code 0; quikplan 141 rows; quikridr 7002 rows.

### Step 4 — Post-deployment validation

```powershell
python tools/validators/validate_issue28_plan_mapping.py
python tools/validators/validate_mpolicy_width.py
python tools/validators/validate_issue26_mprem.py
python tools/validators/validate_issue21m_quikmemo.py
python tools/validators/validate_issue21m_dbf_packaging.py
python Issue_Log_Items/Issue_28/_issue28_intake_analysis.py
```

Optional (DBF UAT):

```powershell
python issue21k_units_migration.py --reload-quikridr
python tools/validators/validate_issue21k_munit.py
```

### Step 5 — Verify client examples

In `QLA_Migration/Output/quikplan.csv`:

| Source product | Expected PLAN |
|----------------|---------------|
| 10827 MN5K | 1CSIMN |
| 0823 960CH | 960CWP |
| 0824 P DIS | 94PDIS |
| DISCHO25 | 9DIS25 |

In `quikridr.csv`, confirm MPLAN matches for policies carrying these riders.

### Step 6 — Archive output

Copy validated output to staging baseline:

```text
Issue_Log_Items/Issue_28/evidence/v57.35_staging_output/
```

---

## Rollback steps

See `Issue_28_Rollback_Checklist.md`. Summary:

1. **Code:** Revert `product_catalog_authority.py` + version bump to v57.34
2. **Catalog:** Remove DISCHO25 row; restore prior migration catalog copy
3. **P3E:** Set `QLA_CLOSED_MPLAN_AUTHORITY=0` (no code revert required)
4. **Output:** Re-run batch on v57.34 code or restore archived v57.34 output

Rollback time estimate: minutes (git revert + batch re-run).

---

## Post-deployment verification (Operations)

| Check | Pass criteria |
|-------|---------------|
| Batch log | No CRITICAL errors; P3E refresh logged after quikplan |
| quikplan PLAN diff vs v57.34 | Exactly 33 changes |
| Issue #28 validator | PASS, 0 mismatches |
| Protected validators | #25, #26, #21M, #21M-FU PASS |
| Row counts | quikplan 141, quikridr 7002, quikmemo 4380 |

---

## Production gate (not part of staging deploy)

Production release additionally requires:

- **B-02:** Client written acceptance of re-UAT scope (33 PLAN changes)
- **V-16:** Rate team sign-off on changed PLAN codes
- Client UAT PASS on acceptance criteria in `Issue_28_Client_UAT_Package.md`
