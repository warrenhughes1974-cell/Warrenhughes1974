# Issue #37 — Implementation Notes

**Issue:** Age/Duration Rate Placement — CV / QuikCvs (fleet-wide)  
**Framework stage:** Development (G4)  
**Status:** Complete — ready for Validation (G5)  
**Date:** 2026-07-03  
**Risk basis:** Conditional Go approved 2026-07-03

---

## Summary

Surgical CV-only duration grid remapping in Phase R5 rate loader. Rate **values** unchanged; LifePRO duration **column numbers** now align with client-validated 960 PO screenshots.

---

## Files Changed

| File | Change |
|------|--------|
| `qla_core/rate_factor_loader.py` | CV grid helpers + `load_cv_slice_fnz()` + remap in `transform_source()` |
| `qla_core/rate_pipeline.py` | Pre-scan CV fnz; pass `cv_fnz` into transform |
| `QLA_Migration/_validate_issue37_quikcvs_placement.py` | Proof-case validation script |
| `QLA_Migration/Output/rates/QuikCvs.csv` | Re-emitted (when emit run succeeds) |

**Not touched:** `app.py`, QuikPlan converter, NP/GP/DB/DV/TV loaders, Issues #25 / #26.

---

## Algorithm

For each CV slice `(COVERAGE_ID, SEX, AGE)`:

1. Pre-scan: `fnz` = first source duration with non-zero value.
2. LifePRO first rate column: `cv_lifepro_first_duration(sex, age)` (proof matrix).
3. Remap: `lp_d = source_d + lp_first - fnz`; drop if `lp_d > 100 - age`.
4. QL slot: `ql_d = lp_d - 1`.

---

## Before / After Trace — 1960PO / M / Age 22

| Metric | Before | After |
|--------|-------:|------:|
| 8.32 QL duration | 1 | **3** (LifePRO dur 4) |
| 1000 QL duration | 75 | **77** (LifePRO dur 78) |
| Leading zeros | missing | slots 0–2 blank; LP 0–3 = zero |

---

## Rollback

Restore prior `QuikCvs.csv` from baseline/archive. Revert `rate_factor_loader.py` + `rate_pipeline.py` CV grid block.

---

## Validation

```text
python QLA_Migration/_validate_issue37_quikcvs_placement.py
python plan_analysis/phase_r5_rate_loader/rate_loader_emit.py --csv-only
```
