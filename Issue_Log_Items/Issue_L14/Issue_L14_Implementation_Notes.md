# Issue L14 — Implementation Notes

**Issue:** L14 — Cash Value Duration Off-by-One (QuikCvs)  
**Engine:** v58.82  
**Date:** 2026-08-06

## Change

Coverage-scoped CV duration **identity** for `COVERAGE_ID=L14`:

`ql_duration = source_duration` (no `first − fnz` offset).

GL85 / other CV coverages keep existing `cv_remap_ql_duration` (#98).

## Files

| File | Change |
|------|--------|
| `qla_core/rate_factor_loader.py` | `CV_IDENTITY_DURATION_COVERAGES`; `coverage_id` arg on remap |
| `qla_core/cv_inheritance_loader.py` | Pass `coverage_id` |
| `qla_core/pdage_missfill.py` | Pass `coverage_id` |
| `app.py` / `QLA_Migration/app.py` | v58.82 |
| `Issue_Log_Items/Issue_L14/validate_issue_l14_quikcvs_duration.py` | Gold F/69 + F/45 |
| `tests/test_cv_l14_duration_identity.py` | Unit remap checks |
| `tools/validators/validate_release_closed_issues.py` | L14 smoke job |
| `Completed_Issues_Release_Validation_Guide.md` | L14 smoke + guide row |

## Emit

Rates re-emitted via `rate_loader_gui_runner.py --emit-csv` → `QLA_Migration/Output/rates/` (SUCCESS, 0 blockers).
