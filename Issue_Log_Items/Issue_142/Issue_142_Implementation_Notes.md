# Issue 142 — Implementation Notes

**Date:** 2026-08-29 · **Engine:** v59.04 · **Approved for Development:** Warren in chat

## What changed

Active `BENEFIT_TYPE=SL` rows now emit to quikridr as plan **9SUBLF** with **MVPU=0**.
Units and `ANN_PREM_PER_UNIT` stay, so the rating premium is visible and the insured
amount is not duplicated. Non-active SL rows stay suppressed (Issue #27, narrowed).

## Files

| File | Change |
|---|---|
| `app.py` / `QLA_Migration/app.py` | v59.04; SL filter partitions Active vs non-active; seed 9SUBLF after Issue A plan setup |
| `qla_core/issue142_sl_rider.py` | Active mask, PLAN/VPU transform, emit audit, quikplan seed |
| `qla_core/sl_benefit_governance.py` | `is_active_sl_status`; docstring narrowed |
| `qla_core/quikplan_converter.py` | seed 9SUBLF on standalone quikplan convert |
| `QLA_Migration/Mapping/product_catalog_crosswalk.csv` | identity 9SUBLF row |
| `plan_governance/product_catalog_crosswalk.csv` | same |
| `tools/validators/validate_issue142_sl_rider.py` | fail-closed Output validator (smoke candidate) |
| `Issue_Log_Items/Issue_142/tools/apply_issue142_9sublf.py` | surgical apply to current Output |

## Before / after (examples)

| Policy | Before | After |
|---|---|---|
| 9010886099C | base 5667AT only; SL $26.34/unit hidden | + phase 2 9SUBLF, 100 units, MVPU 0, MPREM 26.34 |
| 9010469666C | base 1960OL only; SL $2.50/unit hidden | + phase 2 9SUBLF, 10 units, MVPU 0, MPREM 2.50 |
| 9011201237C | base 5L0110 only; SL $11.935/unit hidden | + phase 2 9SUBLF, 25 units, MVPU 0, MPREM 11.935 |
| 9010782078C | no SL row | + 9SUBLF MPREM 0 (outlier left as decided) |

## Rollback

Revert the v59.04 commit. No schema or field-order changes.
