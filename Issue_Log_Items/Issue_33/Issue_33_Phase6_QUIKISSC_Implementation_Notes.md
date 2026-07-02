# Issue #33 — Phase 6 QUIKISSC Implementation Notes

**Issue:** #33 — ISWL Phase 6 QUIKISSC (Surrender Charges)  
**PR:** PR-6  
**Date:** 2026-07-01  
**Status:** **COMPLETE — APPROVED — FINAL AUTHORITY** (reconcile + semantic review closed 2026-07-01)

---

## 1. Files Modified

| File | Change |
|------|--------|
| `qla_core/rate_dbf_schema.py` | Added `QuikIssc` field spec + `quikissc_fields()` |
| `qla_core/rate_dbf_writer.py` | Added `write_quikissc_table()` / `write_quikissc_csv()` |
| `qla_core/rate_pipeline.py` | Wired `quikissc_loader`; `quikissc_rows`, status, summary |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | Added `iswl_phase6` block |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.example.json` | Synced phase 6 config |
| `plan_analysis/phase_r5_rate_loader/rate_loader_emit.py` | QuikIssc DBF + CSV emit |
| `tools/validators/iswl_common.py` | Phase 6 paths, `ISWL_ISSC_MPLANS`, `EXPECTED_ISSC_ROWS=8` |
| `tools/validators/iswl_quikissc_reconcile.py` | ASCII-safe console print (`PSEGT->SL`; see §10) |

**Not modified:** Phase 1–5 loaders, `app.py`, expense setup.

---

## 2. New Files Created

| File | Purpose |
|------|---------|
| `qla_core/quikissc_loader.py` | Rate_Table SL hub schedule → QuikIssc rows |
| `tools/validators/iswl_quikissc_reconcile.py` | V-ISSC-01 through V-ISSC-12 |
| `Issue_Log_Items/Issue_33/output/Phase6_QUIKISSC/iswl_quikissc_reconcile_summary.json` | Validator summary |
| `Issue_Log_Items/Issue_33/output/Phase6_QUIKISSC/iswl_quikissc_keys_by_mplan.csv` | Row detail export |
| `Issue_Log_Items/Issue_33/output/baselines/iswl_quikissc_regression_baseline.json` | Regression baseline |
| `QLA_Migration/Output/rates/QuikIssc.csv` | 8-row load package output |

---

## 3. Implementation Summary

**Runtime hierarchy (approved):**

```text
PCOMP → PCOVR → PCOVRSGT → PSEGT(SL) → OSLNS00XT/SLD000 → Rate_Table TYPE_CODE=SL → QuikIssc
```

**Loader behavior:**

1. Read `Rate_Table_Extract_20260427.csv` filtered to `COVERAGE_ID=659 CEN II`, `TYPE_CODE=SL`, `SEX=M`, `BAND=1`, `UNDERWRITING_CLASS=S`, `AGE=0`.
2. Pivot DURATION 1–14 → `SCHG01`–`SCHG14` as percent literals (4 decimals).
3. Map `UWCLASS S → SM`, `BAND 1 → 01` via `rate_dbf_schema` transforms.
4. Replicate hub schedule to all 8 ISWL MPLANs (one row each).
5. Leave `SCHG15`–`SCHG20` blank (no source durations).

**Config gate:** `iswl_phase6.quikissc_enabled=true` in `rate_loader_config.json`.

---

## 4. Validation Results

| Check | Result |
|-------|--------|
| V-ISSC-01 Schema | PASS |
| V-ISSC-02 PSEGT→Rate_Table SL | PASS (8/8 coverages, 14 durations) |
| V-ISSC-03 All 8 MPLANs | PASS |
| V-ISSC-04 Exactly 8 rows | PASS |
| V-ISSC-05 UWCLASS=SM | PASS |
| V-ISSC-06 AGE=0 | PASS |
| V-ISSC-07 SCHG01–14 values | PASS |
| V-ISSC-08 SCHG15–20 blank | PASS |
| V-ISSC-09 Percent literals | PASS |
| V-ISSC-10 Unique index key | PASS (0 dupes) |
| V-ISSC-11 Phase 1–5 regression | PASS |
| V-ISSC-12 QuikIssc.csv emit | PASS |

**Command:**

```text
python tools/validators/iswl_quikissc_reconcile.py --write-baseline --emit-csv
```

**Pipeline:** `blocker_count=0`, `emit_ready=True`

**Reconcile closure (2026-07-01):**

- Initial validator run failed with `UnicodeEncodeError` on Windows cp1252 console when printing `PSEGT→SL`.
- **Only post-development code fix:** changed validator log text to ASCII-safe `PSEGT->SL` in `iswl_quikissc_reconcile.py`.
- Re-run with `--write-baseline --emit-csv` completed successfully (exit 0).
- No loader, schema, mapping, or emit logic changes after successful validation.

---

## 4a. Validation Evidence (preserved)

| Evidence | Location |
|----------|----------|
| Reconcile summary (all V-ISSC flags) | `Issue_Log_Items/Issue_33/output/Phase6_QUIKISSC/iswl_quikissc_reconcile_summary.json` |
| Row detail by MPLAN | `Issue_Log_Items/Issue_33/output/Phase6_QUIKISSC/iswl_quikissc_keys_by_mplan.csv` |
| Regression baseline | `Issue_Log_Items/Issue_33/output/baselines/iswl_quikissc_regression_baseline.json` |
| Emitted load package | `QLA_Migration/Output/rates/QuikIssc.csv` |

**Recorded outcomes:**

| Metric | Result |
|--------|--------|
| QuikIssc.csv row count | **8** |
| V-ISSC-01 through V-ISSC-12 | **ALL PASS** |
| Phase 1–5 regression | **ALL PASS** (Phase1–Phase5 per `phase1_5_notes` in summary JSON) |
| PSEGT SL gate | 8/8 coverages |
| Hub SL durations | 14 |
| Duplicate index keys | 0 |

---

## 5. Row Counts

| Table | Rows |
|-------|------|
| QuikIssc | **8** (1 per MPLAN) |
| QuikUint (unchanged) | 32 |
| QuikCvs | unchanged vs baseline |
| QuikGps | unchanged vs baseline |
| QuikCoi | unchanged vs baseline |
| QuikGcoi | unchanged vs baseline |

**Hub SL schedule (659 CEN II, replicated to all MPLANs):**

| Duration | SCHG | Value |
|----------|------|-------|
| 1–2 | SCHG01–02 | 100.0000 |
| 3 | SCHG03 | 70.0000 |
| 4 | SCHG04 | 60.0000 |
| 5 | SCHG05 | 50.0000 |
| 6 | SCHG06 | 40.0000 |
| 7 | SCHG07 | 30.0000 |
| 8 | SCHG08 | 20.0000 |
| 9 | SCHG09 | 15.0000 |
| 10 | SCHG10 | 10.0000 |
| 11 | SCHG11 | 8.0000 |
| 12 | SCHG12 | 6.0000 |
| 13 | SCHG13 | 4.0000 |
| 14 | SCHG14 | 2.0000 |
| 15–20 | SCHG15–20 | blank |

---

## 6. Regression Results

Independent re-run of Phase 1–5 validators after PR-6:

| Phase | Script | Result |
|-------|--------|--------|
| 1 | `iswl_quikcvs_reconcile.py` | PASS |
| 2 | `iswl_quikgps_reconcile.py` | PASS |
| 3 | `iswl_quikcoi_reconcile.py` | PASS |
| 4 | `iswl_quikgcoi_reconcile.py` | PASS |
| 5 | `iswl_quikuint_reconcile.py` | PASS |

Factor-table row counts unchanged per `iswl_quikissc_regression_baseline.json`.

---

## 7. Known Issues

None blocking PR-6.

---

## 8. Deferred Items

| Item | Notes |
|------|-------|
| QuikIsrr (partial surrender) | Out of scope — separate issue |
| Expense setup | Explicitly deferred — do not begin |
| DBF production emit via `app.py` | Not requested for PR-6; CSV + isolated DBF via `rate_loader_emit.py` available |
| Female / non-smoker / multi-band expansion | Source has hub row only (M/S/Band 1); SME approved single row per MPLAN |
| Per-coverage schedule variation | SME approved hub replication to all 8 MPLANs |

---

## 9. PR-6 Review Recommendation

**COMPLETE — APPROVED — FINAL AUTHORITY**

`QLA_Migration/Output/rates/QuikIssc.csv` is the approved final authority for ISWL full surrender charges. See [`Issue_33_Phase6_QUIKISSC_Semantic_Review.md`](Issue_33_Phase6_QUIKISSC_Semantic_Review.md) and [`Issue_33_PR6_Closure_Report.md`](Issue_33_PR6_Closure_Report.md).

**Issue #33:** CLOSED. No further QuikIssc work unless a future review raises a defect.

---

## 10. Post-Development Fix Log

| Date | File | Change | Reason |
|------|------|--------|--------|
| 2026-07-01 | `tools/validators/iswl_quikissc_reconcile.py` | `PSEGT→SL` → `PSEGT->SL` in print output | Windows cp1252 `UnicodeEncodeError`; validator-only; no business-logic impact |
