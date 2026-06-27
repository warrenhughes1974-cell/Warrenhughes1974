# Issue #28 — Implementation Summary

**Issue:** #28 — Incorrect Plan Number Mapping  
**Development date:** 2026-06-24  
**Baseline:** v57.34  
**Delivered:** **v57.35**

---

## Problem

Runtime product catalog authority read `ql_plan_code` (compat/passthrough) instead of client-approved `crosswalk_ql_plan_code`, causing **33 PLAN mismatches** and missing **DISCHO25** catalog coverage.

---

## Solution delivered

| Phase | Deliverable | Status |
|-------|-------------|--------|
| **Phase 0** | DISCHO25 catalog row (`9DIS25`) + migration catalog sync | ✅ Complete |
| **Phase 1** | `crosswalk_ql_plan_code` runtime authority in `load_product_catalog_crosswalk()` | ✅ Complete |
| **Phase 2** | P3E MPLAN default ON + post-quikplan resolver refresh | ✅ Complete |

---

## Expected functional result (post batch re-run)

- quikplan PLAN uses authoritative QL plan codes for all 33 previously divergent mappings
- DISCHO25 emits PLAN `9DIS25` in quikplan
- quikridr MPLAN aligns to authoritative PLAN via P3E resolver
- 108 previously correct mappings unchanged
- Protected issues (#21M, #21M-FU, #21K, #25, #26) code paths unmodified

---

## Key code change (one line concept)

```
PLAN authority = crosswalk_ql_plan_code if non-blank else ql_plan_code
```

Implemented in `qla_core/product_catalog_authority.py:load_product_catalog_crosswalk()`.

---

## Population impact (from Risk Agent — unchanged)

| Metric | Value |
|--------|------:|
| PLAN corrections | 33 + DISCHO25 |
| Policies affected | 219 |
| PPBEN rows | 239 |
| quikridr rows | 241 |

---

## Rollback

| Component | Action |
|-----------|--------|
| Phase 1 | Revert `product_catalog_authority.py` + version bump |
| Phase 0 | Remove DISCHO25 row / restore migration catalog |
| Phase 2 | Set `QLA_CLOSED_MPLAN_AUTHORITY=0` |

See `Issue_28_Rollback_Checklist.md`.

---

## Next stage

**Validation Agent** — full batch re-run + validator suite. Do not proceed to Client UAT until Validation PASS.

Development artifacts:

- `Issue_28_Development_Report.md` (includes Validation Agent prompt)
- `Issue_28_Code_Changes.md`
- `Issue_28_File_Modification_Log.md`
- `Issue_28_PreValidation_Checklist.md`
- `tools/validators/validate_issue28_plan_mapping.py`
