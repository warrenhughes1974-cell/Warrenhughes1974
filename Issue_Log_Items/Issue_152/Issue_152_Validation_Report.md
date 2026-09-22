# Issue #152 — Validation Report

**Date:** 2026-09-22  
**Result:** PASS  
**Output:** full `QLA_Migration/Output/` (quikridr phase-1 MPREM only)  
**Not Closed.** Regression and Closure were not started.

## Checks

| Check | Result |
|-------|--------|
| `python tools/validators/validate_issue152_mprem_rider.py` | PASS — 33/33 on PPBEN 20260831. Golds 9010723388C 7.82, 9010723386C 7.52, 9011069655C 8.47, 9010987095C 7.48 |
| Holds | 9010779552C 7.73, 9010767171C 2.168, 9010722550C 8.71966, 9010779727C 5.8615 unchanged |
| Billed mode premium | 857.00 / 827.00 / 844.00 / 46.18 unchanged |
| Rider phases | 977ADB 1.00, 976659 0.22 / 0.18, 9SUBLF 0.19520 unchanged |
| `validate_issue139_policy_fee_suppression.py` | PASS |
| `validate_issue142_sl_rider.py` | PASS — 22 `9SUBLF` rows, MVPU 0 |
| Issue 88 fleet check | Same 59 pre-existing mismatches as before this change (blank MPREM already 0). Anchor 9010779727C still 5.8615. The 33 Issue 152 rows are not new mismatches. |

## Publish

`python tools/publish_test_validation.py quikridr --issue Issue_152`  
Published `QLA_Migration/Output/Test_Validation/quikridr.csv`.

## Still later

Fresh QLAdmin valuation should show base modal 782, 752, and 847 on the three examples, with the rider rows still present. Current `docs/Valuation/QuikValf.dbf` is the 6/30 before-state.
