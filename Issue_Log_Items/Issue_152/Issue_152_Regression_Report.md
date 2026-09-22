# Issue #152 — Regression Report

**Date:** 2026-09-22  
**Result:** PASS for this change  
**Scope:** quikridr phase-1 MPREM on the current 8/31 Output. No full rebatch.

## Intended change

33 phase-1 base rows. Golds 9010723388C 7.82, 9010723386C 7.52, 9011069655C 8.47, 9010987095C 7.48.

## Unchanged

- Rider-phase MPREM on the golds
- quikmstr MMODEPREM 857.00 / 827.00 / 844.00 / 46.18
- Populated-ANN holds 9010779552C 7.73 and 9010767171C 2.168
- Issue 88 anchor 9010779727C 5.8615
- Issue 137 gold 9010722550C 8.71966
- Issue 139 smoke PASS
- Issue 142 smoke PASS (22 9SUBLF rows, MVPU 0)

Issue 88 fleet check still has the same 59 pre-existing blank-MPREM mismatches it had before this change. The 33 Issue 152 rows are not new mismatches.
