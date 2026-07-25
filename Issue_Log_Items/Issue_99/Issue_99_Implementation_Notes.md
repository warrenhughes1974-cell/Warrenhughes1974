# Issue #99 — Implementation Notes

**Issue:** #99 — ISWL QuikPlan MKTG / PRODUCT / HLOB = ISWLFE  
**Date:** 2026-07-23  
**Release:** v58.28  
**Status:** Implemented v58.28 — Validation PASS

---

## Change summary

After all existing quikplan enrichments, ISWL MPLAN rows receive:

| Field | Value |
|-------|-------|
| MKTG | `ISWLFE` |
| PRODUCT | `ISWLFE` |
| HLOB | `ISWLFE` |

Scope: 8 plans in `ISWL_MPLAN_ALLOWLIST` only. All other plans unchanged.

---

## Code touched

| File | Change |
|------|--------|
| `qla_core/cso_mortality_crosswalk.py` | `ISWL_PRODUCT_TAG`, `ISWL_PRODUCT_TAG_FIELDS` constants |
| `qla_core/quikplan_converter.py` | `apply_iswl_product_tags()`; wired in `run_quikplan_conversion()` |
| `app.py` | Import + call after `apply_issue_a_plan_setup` on batch quikplan path |
| `QLA_Migration/app.py` | Same (synced) |
| `tools/validators/validate_issue99_iswl_product_tags.py` | Issue validator |

---

## Regression guardrails

- Uses existing `is_iswl_mplan()` — no second allowlist
- Runs last on quikplan emit (after Issue A / modal / CSO overlays)
- Validator asserts non-ISWL PRODUCT distribution unchanged vs pre-fix baseline
- Validator asserts no non-ISWL row gets `ISWLFE` on MKTG/PRODUCT/HLOB

---

## UAT reload

Partial reload: `QLA_Migration/Output/Test_Validation/quikplan.csv` (after validator PASS).
