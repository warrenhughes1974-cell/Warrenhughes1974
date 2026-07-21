# Issue #60 — Implementation Notes

**Issue:** #60 — PUA phase fields (Chris plan) — Track A  
**Version:** **v57.85**  
**Date:** 2026-07-14  
**Status:** Implemented — validator PASS; ready for Validation Agent  
**Track B:** Not implemented (base interest still blocked)

---

## Summary

Surgical expansion of PUA inheritance in `app.py` / `QLA_Migration/app.py`. Changes apply **only** inside `_apply_pua_rider_inheritance` (gated by `_is_paid_up_addition_product`). Other riders’ dates and ages are untouched.

---

## Code changes

| File | Change |
|------|--------|
| `app.py` | v57.85 — PUA phase inheritance |
| `QLA_Migration/app.py` | Mirror |

### `_cache_quikridr_base_phase`

Now caches phase-1: `MEFFDATE`, `MAGE`, `MPHSTAT` (plus existing `MPLAN`, `MEXPRY`, `MPAYUP`).

### `_apply_pua_rider_inheritance`

| Field | Rule |
|-------|------|
| `MPLAN` | `base[:4]+"PA"` (unchanged) |
| `MEXPRY` | copy base (unchanged) |
| `MEFFDATE` | copy base |
| `MAGE` | copy base |
| `MPAYUP` | set to inherited `MEFFDATE` (not base payup) |
| `MPHSTAT` | `41` when base `MPHSTAT` &lt; 50; else unchanged |
| `MLASTANN` | recomputed via existing `_apply_quikridr_mlastann` after MEFFDATE inherit |

### Not changed

- Non-PUA riders (ADB, WP, term, etc.)
- Phase-1 base rows
- Rate emit / QuikPlCv / `1960PA` plan file (#56 withdrawn)
- #25 MPOLICY / #26 MPREM

---

## Before / after trace

### `010310404C` (Chris golden)

| Ph | Field | Before | After |
|----|-------|--------|-------|
| 2 | MPHSTAT | 22 | **41** |
| 2 | MEFFDATE | 20110128 | **19690128** |
| 2 | MAGE | 68 | **26** |
| 2 | MLASTANN | 15 | **57** |
| 2 | MPAYUP | 20460128 | **19690128** |

### `010150910C` (PUA + ADB)

| Ph | MPLAN | MEFFDATE / MAGE | After |
|----|-------|-----------------|-------|
| 2 | 920ADB | unchanged | **unchanged** |
| 3 | 221EPA (PUA) | dates → base | PUA rules only |

---

## Validation

| Script | Result |
|--------|--------|
| `tools/validators/validate_issue60_pua_phase.py` | **PASS** |
| `QLA_Migration/_validate_issue60_pua_phase.py` | wrapper |

Fleet: **494** PUA rows checked; **1,357** other later-phase rows unchanged vs `evidence/quikridr_pre_v5785_baseline.csv`.

Published: `QLA_Migration/Output/Test_Validation/quikridr.csv`

---

## UAT (client)

1. Reload `Test_Validation/quikridr.csv` (DBF append).  
2. Run Data Admin + rebuild CV on **`010310404C`**.  
3. Track B still needed for non-zero `1960PO` NFOINT/reserve interest before PUA dollar values fully match Chris expectations.

---

## Next

Validation Agent (read-only regression) → Regression Agent → Closure.
