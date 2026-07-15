# Issue #71 — Implementation Notes

**Version:** v57.90  
**Stage:** Development (Composer 2.5)  
**Date:** 2026-07-14

## Summary

Standardized all rate factor/key `BAND` values to **`00`** (NOT APPLICABLE) to align with `quikridr.MBAND=00` (Chris policy band). Fixes Policy Display cash-value lookup mismatch (e.g. policy `010718309C` / plan `1658C1`).

## Code changes

| File | Change |
|------|--------|
| `qla_core/rate_dbf_schema.py` | `map_band()` collapses LifePRO 1/2/3 → `00`; added `band_collapse_priority()` |
| `qla_core/rate_factor_loader.py` | GP dedupe on band collapse (prefer former `01`); `source_band_raw` on transforms |
| `qla_core/*_loader.py` (7 files) | Pass `source_band_raw` for dedupe |
| `qla_core/quikissc_loader.py` | Fallback band `00` |
| `app.py`, `QLA_Migration/app.py` | `APP_VERSION` → **v57.90** |

## Scope decisions honored

- **SD-71-1–4:** Single-band tables remap `01`→`00`; `quikridr.MBAND` unchanged at `00`
- **SD-71-5:** QuikGps/QuikPlGp multi-band collapse dedupes by keeping former band `01` content
- **SD-71-6:** QuikPlBd `BDCODE=00`
- **No** NFOINT / LOANINTX / MCV0 amount edits

## Validation

```text
python Issue_Log_Items/Issue_71/scripts/validate_issue71_band.py
```

## UAT

1. Reload `Test_Validation/rates/` package into QLAdmin Data Admin  
2. Rebuild cash values on **`010718309C`** — expect non-zero CV grid (not all 0.00)  
3. Spot-check GP plan **`5L01MA`** peers per Risk report

## Publish

- `QLA_Migration/Output/rates/` — full rate CSV package  
- `QLA_Migration/Output/Test_Validation/rates/` — partial UAT reload
