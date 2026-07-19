# DG-R-009 — Change Log

**Status:** Applied (SP cluster)  
**Date:** 2026-07-18  
**APP_VERSION:** v58.10

## Backup

`Q:\CSO\CSO_Test_6_30_2026_backup_DG-R-009_20260718` (QuikPlan.*)

## CSO QuikPlan data (6 SPWL plans)

Plans: `1668SP`, `10L171`, `10L172`, `17MJPO`, `1L17SP`, `117JPO`

| Field | Before (typical) | After |
|-------|------------------|-------|
| PAYYRS | 0 | **1** |
| PAYAGE | 0 | **0** |
| SEMI / QTRL / MTHD / MTHB | modal factors (~50/25/8…) | **0** |

## Conversion

| File | Change |
|------|--------|
| `QLA_Migration/Configs/single_premium_plans.csv` | **New** — confirmed SP plan list |
| `qla_core/quikplan_converter.py` | `apply_single_premium_payment_settings` after R7B |
| `app.py` / `QLA_Migration/app.py` | Call enrichment; **APP_VERSION v58.10** |
| `data_governance/config/plan_classification.csv` | Marked six plans `IS_SINGLE_PREMIUM=Y` |

## Deferred / hold (no change)

| Item | Status |
|------|--------|
| 986JPO, 982JPO (010) | Deferred |
| A60MIR, A96DAR BASIS (005) | Deferred |
| 1970PA (003) | Hold/exception |
| WPA RRULE=A (018) | Out of scope |
