# Issue #167 — Implementation Notes

**Issue:** #167 — Dividend Premium Payment
**Framework stage:** Development Agent (G5)
**Engine:** v59.12
**Date:** 2026-09-10
**Approved for Development:** Warren 2026-09-10

---

## What changed

`_compute_quikridr_mlastann` in both `app.py` and `QLA_Migration/app.py` now uses completed years to the issue anniversary:

`val.year − issue.year − ((val.month, val.day) < (issue.month, issue.day))`

Same month/day test as Issue #108B. `_apply_issue76_eti_rpu_phase1_payup_mlastann` was not edited.

Current 8/31 Output was remapped with `Issue_Log_Items/Issue_167/tools/remap_issue167_mlastann.py` (2,142 rows; 314 ETI/RPU phase-1 skipped). A later full quikridr convert will use the engine function.

## Files

| File | Change |
|---|---|
| `app.py` | Formula + `APP_VERSION` v59.12 |
| `QLA_Migration/app.py` | Same |
| `tools/validators/validate_issue167_mlastann.py` | Fail-closed validator |
| `Issue_Log_Items/Issue_167/tools/remap_issue167_mlastann.py` | One-time Output remapper |
| `QLA_Migration/Output/quikridr.csv` | Remapped |
| `QLA_Migration/Output/Test_Validation/quikridr.csv` | Published after validator PASS |

## Before / after (gold)

| Policy | Phase | Before | After |
|---|---|---|---|
| 9010397528C | 1 | 55 | **54** |
| 9010397528C | 2 PUA | 55 | **54** |
| 9010367704C | 1 | 56 | 56 |
| 9010412641C | 1 | 54 | 54 |
| 9010149295C | 1 ETI | 33 | 33 |

## DBF

Desktop Append Tool (headless, quikridr only): appended 6,956 rows onto the master template.

`C:\Users\warren\Desktop\DBF_Append_Tool\output\quikridr.dbf` — 2026-09-10 09:16
