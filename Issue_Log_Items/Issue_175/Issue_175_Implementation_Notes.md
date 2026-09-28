# Issue 175 — Implementation Notes

**Issue:** 175 — Res Cat Unique Field
**Framework stage:** Development
**Engine version:** v59.26 unchanged. `app.py` was not edited. The filler lives in `qla_core`.
**Date:** 2026-09-28
**Approval:** Warren, approved for development, including the Closed Issue 141 exception.

---

## What changed

LifePRO product type `L` still copies onto the policy reserve category, except three base coverages:

| Coverage | Plan | Reserve category |
|---|---|---|
| L15 | 1L15GD | 13 |
| L16 | 1L16GD | 13 |
| L17 BASE | 1L17SP | 12 |

Discount coverages that are also product type `L` are not in the map.

The current `quikspec.csv` was corrected in place. 33 lines changed. Each change is `RESRVCAT` only. The file stayed 5,083 data rows, six columns, CRLF.

## Files

| File | Change |
|---|---|
| `qla_core/quikspec_resrvcat.py` | `reserve_category()` and the three-coverage map |
| `QLA_Migration/_validate_issue141_resrvcat.py` | Expects 13 / 13 / 12 on those coverages |
| `tools/validators/validate_issue175_resrvcat.py` | Fail-closed check. Not registered in the smoke list yet. |
| `Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md` | Issue 141 row notes the exception and the approval date |
| `QLA_Migration/Output/quikspec.csv` | 33 cells. Not in git. |
| `QLA_Migration/Output/Test_Validation/quikspec.csv` | Published after validation |

## Trace

| Policy | Before | After | Other fields |
|---|---|---|---|
| 9011210337C | L | 13 | Vanish F, KY, source policy 9011210337 |
| 9011216680C | L | 13 | Vanish F, IN, source policy 9011216680 |
| 9011217014C | L | 12 | Vanish F, LA, source policy 9011217014 |

## Not changed

`quikplan` product codes were already 13, 13, and 12. Premium, policy keys, vanish, resident state, and source policy number were not rewritten. Category `L` is now 0. Category 13 is 845 (was 832). Category 12 is 541 (was 521).
