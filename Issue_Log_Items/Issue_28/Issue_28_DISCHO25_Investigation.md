# Issue #28 — DISCHO25 Investigation (Planning)

**Date:** 2026-06-24  
**Status:** Conclusive — not an alias of DISCHO247C

---

## Question

Intake flagged `DISCHO25` as absent from `product_catalog_crosswalk.csv` and hypothesized it might map to catalog row `DISCHO247C`. Planning must resolve this without assumption.

---

## Evidence Summary

| Source | DISCHO25 present? | QL Plan Code | Notes |
|--------|-------------------|--------------|-------|
| Policy Form Crosswalk 5.22.26.xlsx | **Yes** (row 138) | `9DIS25` | Description: *Home Office Discount - 25%-10Yr* |
| product_catalog_crosswalk.csv | **No** | — | Catalog gap |
| Master_Crosswalk.csv | **Yes** (2 rows) | `9DIS25` | `DISCHO25 → 9DIS25` |
| quikplan_source.csv | **Yes** (row 105) | — | Active coverage `DISCHO25` |
| quikplan.csv (batch output) | **No** | — | Neither `DISCHO25` nor `9DIS25` in output |
| PPBEN (batch riders) | **Yes** | `DISCHO25` PLAN_CODE | 4+ policies in P3E validation traces |

---

## Crosswalk — DISCHO Family (distinct products)

| LifePRO Coverage_ID | Authoritative QL Plan | Product description (crosswalk) |
|---------------------|----------------------|--------------------------------|
| **DISCHO25** | **9DIS25** | Home Office Discount - **25%-10Yr** |
| DISCHO2475 | 9DIS24 | Home Office Discount - **24.75%** |
| DISCHO247B | 9DS24B | Home Office Discount - 24.75% |
| DISCHO247C | **9DS24C** | Home Office Discount - 24.75% |
| DISCHO29 | 9DIS29 | Home Office Discount 29% |

**Conclusion:** `DISCHO25` and `DISCHO247C` are **separate LifePRO products** with **different authoritative plan codes** (`9DIS25` vs `9DS24C`). They do **not** alias.

---

## Catalog anomaly (related, not same ID)

Catalog row `DISCHO247C` has `ql_plan_code=9DIS25` (compat) but `crosswalk_ql_plan_code=9DS24C` (authoritative). This reflects historical Master_Crosswalk many-to-one targeting:

`crosswalk_governance_manifest.csv`:
> *Multiple Old_Value map to PLAN 9DIS25: DISCHO2475, DISCHO247C, DISCHO25*

That legacy collision is a **discount-family data quality issue** — separate from whether DISCHO25 equals DISCHO247C (it does not).

---

## Runtime behavior today (v57.34)

| Path | DISCHO25 behavior |
|------|-------------------|
| quikplan PLAN | **Missing from output** — not in catalog; P3C treats as unauthorized despite Master_Crosswalk legacy row |
| quikridr MPLAN (default) | Master_Crosswalk passthrough → `9DIS25` when PLAN_CODE=`DISCHO25` |
| P3E resolver (when enabled) | Resolves to `9DS24C` in some traces — **incorrect target** due to catalog gap + shared 9DIS25 compat on DISCHO247C |

Intake comparison showed runtime PLAN `9DIS25` matching authoritative crosswalk for the ID — that reflects **Master_Crosswalk fallback in the comparison script**, not successful quikplan emission (quikplan output lacks the plan row).

---

## Determination

| Hypothesis | Verdict | Evidence |
|------------|---------|----------|
| DISCHO25 maps to DISCHO247C | **REJECTED** | Distinct crosswalk rows, descriptions, and authoritative codes |
| Data defect | **PARTIAL** | Catalog missing row; quikplan output missing plan; legacy many-to-one on 9DIS25 |
| Obsolete product | **REJECTED** | Active in quikplan_source, PPBEN, PCOVRSGT lineage |
| Separate remediation required | **CONFIRMED** | Add catalog row: `DISCHO25 → 9DIS25`; ensure quikplan emits plan row |

---

## Planning recommendation

Include **DISCHO25 catalog completeness** as a **Phase 0 data task** in Issue #28 implementation — independent of the 33 `CROSSWALK_DIVERGENT` rows but in scope for full crosswalk alignment (141/141 catalog coverage).
