# Issue #152 — Implementation Notes

**Date:** 2026-09-22  
**Version:** v59.19  
**Status:** Closed 2026-09-22. Validation PASS on current Output. Warren set the sheet to Closed.

Warren approved the Closed Issue 88 exception and Development on 2026-09-22.

## Change

On phase-1 base (BF) rows whose `ANN_PREM_PER_UNIT` is blank, active SU/SL/OR rider mode premium is subtracted from base `MODE_PREMIUM` before the existing Issue 88/137 per-unit calculation. Rider rows, billed `quikmstr.MMODEPREM`, fees, units, and VANISH are unchanged.

## Code

- `qla_core/issue152_rider_modal.py` — structural rider-mode sum
- `app.py` and `QLA_Migration/app.py` — cache plus interceptor, version v59.19
- `tools/validators/validate_issue152_mprem_rider.py` — fail-closed check
- `tools/validators/validate_issue88_mprem_unit_fallback.py` — expected MODE uses the same exception
- `Issue_Log_Items/Issue_152/scripts/apply_issue152_base_mprem.py` — wrote the 33 current-file values without a full rebatch
- Completed Issues guide, Issue 88 How-clause, cites the 2026-09-22 exception

## Output

`QLA_Migration/Output/quikridr.csv`: 33 phase-1 `MPREM` values updated. Published to `Output/Test_Validation/quikridr.csv`.

Examples: 9010723388C 8.82 → 7.82; 9010723386C 8.52 → 7.52; 9011069655C 8.69 → 8.47; 9010987095C 7.841481 → 7.48.

## Not in this step

Smoke registration, accountability row, and Closure wait for the post-validation chain. Fresh QLAdmin valuation is the later UAT check. Current QuikValf is still the 6/30 before-state.
