# Issue #40 — Implementation Notes

**Issue:** Inherited Cash Value Rate Load  
**Date:** 2026-07-06  
**Status:** Implemented — validation PASS; client UAT pending  
**Scope:** QuikCvs / QuikPlCv inherited CV emit only

---

## Change summary

Issue #40 adds a PCOVRSGT-aware inherited CV loader that emits Rate_Table CV rows from approved rate-owner coverages under issuing plan codes when the issuing coverage has no direct CV table.

Example:

| Issuing plan | Issuing coverage | Rate owner | Result |
|--------------|------------------|------------|--------|
| `17085M` | `670 GL85-M` | `670 GL85-8` → plan `170858` | **1,002** QuikCvs keys (was **0**) |

Direct rate-owner plans (e.g. `170858`) are unchanged. Issue #37 / #41 CV duration placement rules apply to inherited rows.

---

## Files changed

| File | Change |
|------|--------|
| `qla_core/cv_inheritance_loader.py` | **New** — manifest builder + inherited CV transform stream |
| `qla_core/rate_pipeline.py` | Wire inherited CV stream after direct `transform_source`; expose manifest/status in summary |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | `issue40_cv_inheritance.enabled` + fleet audit CSV path |
| `QLA_Migration/_validate_issue40_inherited_cv_source_parity.py` | **New** — 100% source-to-QLA parity validator |
| `QLA_Migration/Output/rates/QuikCvs.csv` | Regenerated — **38,047** rows (+ inherited fleet keys) |
| `QLA_Migration/Output/rates/QuikPlCv.csv` | Regenerated — **94** rate-key rows (includes issuing inherited plans) |
| `QLA_Migration/Output/rates/QuikPlGd.csv` | Regenerated — gender members per plan (Plan Information screen) |
| `QLA_Migration/Output/rates/QuikPlUw.csv` | Regenerated — UW class members per plan |
| `QLA_Migration/Output/rates/QuikPlBd.csv` | Regenerated — band members per plan |
| `QLA_Migration/Output/rates/QuikPlSt.csv` | Regenerated — country/state members per plan |
| `QLA_Migration/Output/rates/QuikPlNb.csv` | Regenerated — new-business window per plan |

---

## Inheritance manifest (10 plans)

| Issuing plan | Rate owner coverage | Selection rule |
|--------------|---------------------|----------------|
| `17085M` | `670 GL85-8` | Single owner |
| `1668SP` | `659 CEN II` | Single owner |
| `1666AI` | `666 WL` | Single owner |
| `1SALMI` / `1SALML` | `SAL OL` | Single owner |
| `280PUA` | `980 END65` | Single owner |
| `265PUA` | `665 STME95` | Single owner |
| `261PUA` | `961 ME65` | Single owner |
| `1L10SO` | `L10 PRE97` | Multi-owner — PCOVRSGT slot count (5 vs 1) |
| `1L10SR` | `L10 LP95` | Multi-owner — PCOVRSGT slot count (5 vs 4) |

Manifest source: `Issue_40_Fleet_CV_Inheritance_Audit.csv` + `PCOVRSGT.csv` + Rate_Table CV scan.

---

## Regression boundaries

Unchanged:

- `quikplan`, `quikridr`, `quikmstr`, and policy conversion logic
- Non-CV rate families (`QuikNps`, `QuikGps`, `QuikDbs`, `QuikDvs`, `QuikTvs`)
- Issue #37 / #41 CV duration-index rules
- Direct rate-owner QuikCvs rows (values and plan codes)

Known blocker outside Issue #40:

| Blocker | Impact |
|---------|--------|
| `V-UINT-PDINT` / missing `PDINTTBL` for `QuikUint` | Full guarded R5 emit still reports one blocker. Issue #40 regenerated `QuikCvs.csv` and `QuikPlCv.csv` from the validated grid only. |

---

## Validation commands

```powershell
python "QLA_Migration\_validate_issue40_inherited_cv_source_parity.py"
python "QLA_Migration\_validate_issue37_quikcvs_placement.py"
python "QLA_Migration\_validate_issue41_quikcvs_endpoint.py"
```

Issue #40 parity: **101,793** inherited IN_SCOPE rows; **0** source mismatches across all 10 plans; **0** inherited-plan grid collisions.

---

## Next steps

1. Client reloads **all** rate tables for inherited plans into QLAdmin:
   - **Factors + keys:** `QuikCvs.csv`, `QuikPlCv.csv`
   - **Plan members (Plan Information screen):** `QuikPlGd.csv`, `QuikPlUw.csv`, `QuikPlBd.csv`, `QuikPlSt.csv`, `QuikPlNb.csv`
2. Client UAT on policies from `Issue_40_Population.csv` (minimum: `010367438C`, `010615191C`, `010464869C` on plan `17085M`).
3. Confirm CV calculation proceeds without missing-rate failure on `17085M`.
4. Resolve unrelated `QuikUint` blocker before full guarded rate emit.
