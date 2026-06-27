# Issue #28 — PLAN Validation Report

**Validation date:** 2026-06-27  
**Engine:** v57.35  
**Authority:** `crosswalk_ql_plan_code` via `load_product_catalog_crosswalk()`

---

## Scope

Validate all **141** authoritative crosswalk mappings against fresh v57.35 batch output.

---

## Results

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| Catalog data rows | 141 | 141 | PASS |
| quikplan output rows | 141 | 141 | PASS |
| Unique quikplan PLAN codes | 141 | 141 | PASS |
| Authoritative matches | 141 | 141 | PASS |
| Mismatches | 0 | 0 | PASS |
| Previously divergent corrections | 33 | 33 | PASS |
| Stable mappings unchanged | 108 | 108 | PASS |
| Unexpected PLAN changes | 0 | 0 | PASS |
| Duplicate PLAN assignments (new) | 0 | 0 | PASS |
| Many-to-one mapping regressions | 0 | 0 | PASS |

---

## 33 corrected mappings (v57.34 compat → v57.35 authoritative)

All 33 transitions match `Issue_28_PLAN_Comparison_Report.md`. Evidence: `Issue_Log_Items/Issue_28/evidence/v57.35_quikplan_plan_diff.csv`

| # | Coverage_ID | v57.34 PLAN | v57.35 PLAN |
|---|-------------|-------------|-------------|
| 1 | 0823 960CH | 0823 960CH | 960CWP |
| 2 | 0824 P DIS | 0824 P DIS | 94PDIS |
| 3 | 10827 MN5K | 10827 MN5K | 1CSIMN |
| 4 | 1578 SPSPU | 1578 SPSPU | 578STR |
| 5 | 1579 GPO | 1579 GPO | 9GPO79 |
| 6 | 1596 667 | 1596 667 | 967ADB |
| 7 | 619 CH PU | 619 CH PU | 719CTR |
| 8 | 621 PUA | 621 PUA | 121PUA |
| 9 | 630 JEB | 630 JEB | 130JEB |
| 10 | 646 ART | 646 ART | 5646AT |
| 11 | 667 ART CR | 667 ART CR | 57ATCR |
| 12 | 669 SR GD | 669 SR GD | 1669SR |
| 13 | 686S 30MRG | 686S 30MRG | 7686S3 |
| 14 | 687J 30MRG | 687J 30MRG | 7687J3 |
| 15 | 690 DT 65 | 690 DT 65 | 7690DT |
| 16 | 8034 30MRG | 8034 30MRG | 934SWP |
| 17 | 8034 J30MT | 8034 J30MT | 934JWP |
| 18 | 8043CTR WP | 8043CTR WP | 943CWP |
| 19 | 8046 JPO | 8046 JPO | 9JPO46 |
| 20 | 961 ME65 | 961 ME65 | 2961ME |
| 21 | 961 PUA | 961 PUA | 261PUA |
| 22 | 970 JEB | 970 JEB | 1970JB |
| 23 | 970 PUA | 970 PUA | 1970PA |
| 24 | DISCHO2475 | 9DIS25 | 9DIS24 |
| 25 | DISCHO247B | DISCHO247B | 9DS24B |
| 26 | DISCHO247C | 9DIS25 | 9DS24C |
| 27 | DISCHO29 | DISCHO29 | 9DIS29 |
| 28 | L01 10Y MA | L01 10Y MA | 5L01MA |
| 29 | L10 PRE97 | L10 PRE97 | 1L10OD |
| 30 | L10 PREUNI | L10 PREUNI | 1L10PR |
| 31 | L10 SPSWP | L10 SPSWP | 910SWP |
| 32 | L10 WP SRN | L10 WP SRN | 910RWP |
| 33 | WP 646 | WP 646 | 9WP646 |

---

## DISCHO25 (Phase 0 — separate from 33-row set)

| Check | Result |
|-------|--------|
| Catalog row present | PASS — `DISCHO25 → 9DIS25` |
| quikplan emits PLAN 9DIS25 | PASS — 1 row |
| FORM/DESCR preserved | PASS |
| DISCHO247C independent | PASS — resolves to `9DS24C` (not aliased) |
| v57.34 had 3 rows at compat `9DIS25` | v57.35: 1 row `9DIS25` (DISCHO25) + DISCHO247C→9DS24C + DISCHO2475→9DIS24 |

---

## FORM / DESCR integrity

For all 33 changed PLAN rows:

- **FORM unchanged:** True  
- **DESCR unchanged:** True  

Only the `PLAN` field changed — no unintended metadata drift.

---

## Validators used

1. `tools/validators/validate_issue28_plan_mapping.py` — PASS  
2. `Issue_Log_Items/Issue_28/_issue28_intake_analysis.py` — PASS (141/141)  
3. Supplemental pandas diff — `evidence/v57.35_quikplan_plan_diff.csv`

---

## Decision

**PLAN validation: PASS**
