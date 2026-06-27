# Issue #28 — Issue Log Entry

**Issue ID:** #28  
**Title:** Incorrect Plan Number Mapping  
**Status:** **CLOSED**  
**Closed date:** 2026-06-27  
**Resolved in:** v57.35  
**Severity:** High (data accuracy — product catalog)  
**Component:** LifePRO → QLAdmin conversion — quikplan PLAN / quikridr MPLAN

---

## Problem statement

QLAdmin `quikplan.PLAN` values were emitted using compatibility passthrough (`ql_plan_code`) instead of client-approved authoritative plan numbers from the **Policy Form Crosswalk (5/22/2026)**. **33 of 141** product mappings were incorrect. **DISCHO25** was missing from the product catalog.

---

## Root cause

`load_product_catalog_crosswalk()` in `qla_core/product_catalog_authority.py` read `ql_plan_code` (compat/passthrough) rather than `crosswalk_ql_plan_code` (authoritative). Catalog gap for DISCHO25 blocked quikplan emission for that product.

---

## Resolution

| Phase | Fix |
|-------|-----|
| Phase 0 | Added DISCHO25 → 9DIS25 catalog row; synced migration catalog |
| Phase 1 | Promoted `crosswalk_ql_plan_code` to runtime PLAN authority |
| Phase 2 | P3E MPLAN default ON; post-quikplan resolver refresh in batch |

---

## Client examples (verified)

| LifePRO source | Was | Now |
|----------------|-----|-----|
| 10827 MN5K | 10827 MN5K | 1CSIMN |
| 0823 960CH | 0823 960CH | 960CWP |
| 0824 P DIS | 0824 P DIS | 94PDIS |

---

## Framework stage outcomes

| Stage | Date | Outcome |
|-------|------|---------|
| Intake | 2026-06-24 | Root cause proven — CROSSWALK_DIVERGENT |
| Planning | 2026-06-24 | Option A + Phase 0 + Phase 2 recommended |
| Dependency Gate | 2026-06-24 | CONDITIONAL PASS |
| Risk | 2026-06-24 | CONDITIONAL GO |
| Development | 2026-06-24 | v57.35 delivered |
| Validation | 2026-06-27 | PASS WITH OBSERVATIONS |
| Regression & Deployment | 2026-06-27 | READY FOR CLIENT UAT |
| Client UAT | 2026-06-27 | **PASS — APPROVED** |
| **Closure** | **2026-06-27** | **CLOSED** |

---

## Validation summary

- 141/141 PLAN mappings match authoritative crosswalk
- 33 corrections exact; 108 stable mappings unchanged
- Protected issues #25, #26, #21M, #21M-FU: PASS
- Batch exit 0; no row count regressions

---

## Client acceptance

- **Sign-off date:** 2026-06-27
- **Result:** APPROVED — no defects reported
- **Blockers resolved:** B-01 (crosswalk binding), B-02 (re-UAT scope)

---

## Files modified (v57.35)

- `qla_core/product_catalog_authority.py`
- `plan_governance/product_catalog_crosswalk.csv`
- `QLA_Migration/Mapping/product_catalog_crosswalk.csv`
- `app.py`, `QLA_Migration/app.py`
- `tools/validators/validate_issue28_plan_mapping.py`

---

## Rollback

Available per `Issue_28_Rollback_Checklist.md` — revert code + version; optional catalog DISCHO25 removal; `QLA_CLOSED_MPLAN_AUTHORITY=0` for Phase 2.

---

## Related issues

No changes to protected issues #21M, #21M-FU, #21K, #25, #26 implementation paths.

---

## Closure authority

Issue #28 closed per AI Issue Resolution Framework — Client UAT PASS + Closure Agent documentation complete.

**Artifact folder:** `Issue_Log_Items/Issue_28/`
