# DG-R-007 — Validation

**Date:** 2026-07-18  
**Data region:** `Q:\CSO\CSO_Test_6_30_2026`  
**Run:** `validation_out/DG-20260718_193945_001021`

| Check | Result |
|-------|--------|
| DG-QUIKPLAN-008 on CSO | 141/142 pass; **1** residual (blank PLAN LOAGE=0 HIAGE=0 → LOAGE not below HIAGE) |
| Non-zero LOAGE plans (55) | No longer fail for LOAGE_NOT_ZERO |
| `pytest` test_ages_renew_payment_insurance | **Pass** |

Residual blank-plan row is expected and belongs with **DG-R-008** cleanup, not this item.
