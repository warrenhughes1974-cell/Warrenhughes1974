# Issue #28 — PLAN Comparison Report

**Risk analysis date:** 2026-06-24  
**Authority:** Policy Form Crosswalk 5/22/2026 (client confirmed binding — B-01)

---

## Summary

| Metric | Value |
|--------|------:|
| Total crosswalk mappings | 141 |
| Correct at v57.34 runtime | 108 |
| **Requiring correction** | **33** |
| Correction type | Compat passthrough → authoritative QL Plan Code |
| One-to-many / many-to-one conflicts | None |

---

## Client examples

| LifePRO Coverage_ID | v57.34 quikplan.PLAN | Approved PLAN | Change |
|---------------------|----------------------|---------------|--------|
| 10827 MN5K | 10827 MN5K | **1CSIMN** | Passthrough → product code |
| 0823 960CH | 0823 960CH | **960CWP** | Passthrough → product code |
| 0824 P DIS | 0824 P DIS | **94PDIS** | Passthrough → product code |

---

## Full transition table (33 mappings)

| # | LifePRO Coverage_ID | v57.34 PLAN (compat) | Approved PLAN | Product description (crosswalk) |
|---|---------------------|----------------------|---------------|-----------------------------------|
| 1 | 0823 960CH | 0823 960CH | 960CWP | Waiver of Premium - Child |
| 2 | 0824 P DIS | 0824 P DIS | 94PDIS | Payor Disability Rider |
| 3 | 10827 MN5K | 10827 MN5K | 1CSIMN | CSI Life MN $5000 |
| 4 | 1578 SPSPU | 1578 SPSPU | 578STR | Paid Up Spouse Term Rider |
| 5 | 1579 GPO | 1579 GPO | 9GPO79 | Guaranteed Purchase Option Rider |
| 6 | 1596 667 | 1596 667 | 967ADB | Accidental Death Benefit Rider |
| 7 | 619 CH PU | 619 CH PU | 719CTR | Decr Term Paid Up for Child |
| 8 | 621 PUA | 621 PUA | 121PUA | Paid Up Adds - Endowment at Age 85 |
| 9 | 630 JEB | 630 JEB | 130JEB | Juvenile Estate Builder |
| 10 | 646 ART | 646 ART | 5646AT | Annual Renewable Term |
| 11 | 667 ART CR | 667 ART CR | 57ATCR | ART Preferred Credit Life |
| 12 | 669 SR GD | 669 SR GD | 1669SR | Interest-Sensitive Whole Life |
| 13 | 686S 30MRG | 686S 30MRG | 7686S3 | Decreasing Term Life |
| 14 | 687J 30MRG | 687J 30MRG | 7687J3 | Joint Decreasing Term Life |
| 15 | 690 DT 65 | 690 DT 65 | 7690DT | Dec Term to 65 Convertible |
| 16 | 8034 30MRG | 8034 30MRG | 934SWP | Disability Waiver 30MRG |
| 17 | 8034 J30MT | 8034 J30MT | 934JWP | Disability Waiver Joint 30MT |
| 18 | 8043CTR WP | 8043CTR WP | 943CWP | 8043 CTR Waiver of Premium |
| 19 | 8046 JPO | 8046 JPO | 9JPO46 | Juvenile Future Purchase Option |
| 20 | 961 ME65 | 961 ME65 | 2961ME | Modified Endowment at 65 |
| 21 | 961 PUA | 961 PUA | 261PUA | Paid Up Adds - Modified Endowment |
| 22 | 970 JEB | 970 JEB | 1970JB | Juvenile Est Build PU at 85 |
| 23 | 970 PUA | 970 PUA | 1970PA | Paid Up Adds - Juv Est Build |
| 24 | DISCHO2475 | 9DIS25 | 9DIS24 | Home Office Discount 24.75% |
| 25 | DISCHO247B | DISCHO247B | 9DS24B | Home Office Discount 24.75% |
| 26 | DISCHO247C | 9DIS25 | 9DS24C | Home Office Discount 24.75% |
| 27 | DISCHO29 | DISCHO29 | 9DIS29 | Home Office Discount 29% |
| 28 | L01 10Y MA | L01 10Y MA | 5L01MA | Ten Year Level Term to Age 95 |
| 29 | L10 PRE97 | L10 PRE97 | 1L10OD | L10 PRE97 / OLD variant |
| 30 | L10 PREUNI | L10 PREUNI | 1L10PR | L10 PREUNI |
| 31 | L10 SPSWP | L10 SPSWP | 910SWP | L10 Spouse WP |
| 32 | L10 WP SRN | L10 WP SRN | 910RWP | L10 Waiver of Premium Post 1997 |
| 33 | WP 646 | WP 646 | 9WP646 | Waiver of Premium |

---

## DISCHO25 (Phase 0 — not in 33 count)

| LifePRO ID | v57.34 | Approved | Status |
|------------|--------|----------|--------|
| DISCHO25 | Missing from quikplan | **9DIS25** | Catalog row add required |

---

## PLAN code quality delta

| Attribute | v57.34 (compat) | Post-fix (auth) |
|-----------|-----------------|-----------------|
| Values with embedded spaces | Up to 30 | **0** (authoritative codes space-free) |
| Passthrough LifePRO IDs as PLAN | 33 | **0** |
| Referential match to crosswalk | 76.6% | **100%** (target) |

---

## Machine-readable artifacts

| File | Content |
|------|---------|
| `Issue_28_Mapping_Differences.csv` | Full 141-row comparison |
| `_risk_affected_plans.csv` | 33-row affected subset |
| `plan_governance/manifests/plan_change_manifest.csv` | Pre-documented transitions |

---

## Rate table cross-reference (risk flag)

Phase R3 sample shows **PLAN_NOT_IN_TARGET** for several authoritative PLAN codes when used as rate lookup keys (e.g. `1CSIMN`, discount family). This is a **downstream validation risk**, not a blocker to catalog correction — client has approved the PLAN codes.
