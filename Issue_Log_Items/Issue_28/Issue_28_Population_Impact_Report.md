# Issue #28 — Population Impact Report

**Risk analysis date:** 2026-06-24  
**Baseline:** v57.34 batch (Source dated 20260530)  
**Scope:** 33 `CROSSWALK_DIVERGENT` PLAN mappings + Phase 0 DISCHO25

---

## 1. Plan catalog population

| Metric | Count | Source |
|--------|------:|--------|
| Policy Form Crosswalk rows | 141 | xlsx |
| quikplan product rows (batch) | 141 | `quikplan.csv` |
| Catalog rows (governance) | 140 | `product_catalog_crosswalk.csv` |
| **Plans with incorrect PLAN emit (Issue #28 core)** | **33** | `Issue_28_Mapping_Differences.csv` |
| Plans unchanged (STABLE_EMIT) | 108 | Same |
| Additional catalog gap (DISCHO25) | 1 | xlsx only — Phase 0 |
| Unique compat PLAN values being replaced | 32 | 33 IDs; DISCHO2475/247C share compat `9DIS25` |
| Unique authoritative PLAN targets | 33 | One-to-one mapping — **no many-to-one** |

---

## 2. quikplan output impact

| Metric | Count |
|--------|------:|
| quikplan rows with PLAN value change | **34** |
| Distinct LifePRO Coverage_IDs affected | 33 |
| Authoritative PLAN codes **new to current quikplan** | 33 (all targets absent from v57.34 `quikplan.PLAN`) |
| quikplan rows with spaces in PLAN (removed post-fix) | Up to 30 passthrough-style compat values |

**Interpretation:** Fix replaces LifePRO-style passthrough PLAN strings with approved QL Plan Codes across the full divergent product catalog slice — not a subset of in-flight policies only.

---

## 3. Policy population (batch extract)

Analysis: `PPBEN_PolicyBenefit_Extract_20260530.csv` matched on affected `PLAN_CODE` / Coverage_ID.

| Metric | Count |
|--------|------:|
| Total PPBEN rows (batch) | 11,699 |
| PPBEN rows on affected PLAN_CODEs | **239** |
| **Distinct policies affected** | **219** |
| % of PPBEN policy universe | ~1.9% (219 / ~11.5K benefits implied) |
| Phase 1 (base) benefit rows | 166 |
| Rider phase benefit rows (phase ≠ 1) | 73 |
| Distinct policies — base phase hits | 166 |
| Distinct policies — rider phase hits | 73 |

Detail by product: `Issue_28_Policy_Impact_Summary.csv`

### Top policy-touch products (by PPBEN row count)

| LifePRO ID | Policies | PPBEN rows | Auth PLAN |
|------------|----------|------------|-----------|
| 8046 JPO | 10 | 10 | 9JPO46 |
| 1596 667 | 8 | 8 | 967ADB |
| 8043CTR WP | 6 | 6 | 943CWP |
| 1578 SPSPU | 4 | 4 | 578STR |
| 10827 MN5K | 3 | 3 | 1CSIMN |
| 686S 30MRG | 3 | 3 | 7686S3 |

Client examples (0823 960CH, 0824 P DIS, 10827 MN5K): **1 policy each** in current batch PPBEN.

---

## 4. Rider / quikridr population

| Metric | Count |
|--------|------:|
| quikridr total rows (v57.34) | 7,002 |
| quikridr rows with MPLAN in affected compat set | **241** |
| Distinct MPOLICY on those rows | **222** |
| Distinct affected MPLAN values (compat) | 30 |

**Phase 1 only:** quikridr MPLAN **unchanged** (Master_Crosswalk passthrough).  
**Phase 2 (P3E):** up to **241 quikridr rows** on **222 policies** may receive new authoritative MPLAN when P3E enabled.

P3D referential integrity (pre-fix): all 33 compat MPLAN values classified **ORPHAN_MPLAN** — emitted by quikridr but absent from P3C closed-authority quikplan.PLAN. Fix **resolves** this class of orphan for quikplan; Phase 2 aligns quikridr.

---

## 5. Base vs rider / product type

| Category | Count in affected set | Notes |
|----------|----------------------:|-------|
| Rider / supplemental products | Majority of 33 | WP, GPO, ADB, PUA, discount riders, term riders |
| Base / whole-life style | Few (e.g. 10827 MN5K, L10 variants) | Client example 10827 MN5K is base MN product |
| PUA products in affected set | 3 | `621 PUA`, `961 PUA`, `970 PUA` — PUA inheritance sensitive in Phase 2 |
| Discount / home-office (DISCHO*) | 5 | Includes shared compat `9DIS25` collision family |
| Closed vs active | All active in quikplan_source | Status `A` on source rows |

---

## 6. Orphan and duplicate analysis

| Check | Result |
|-------|--------|
| Duplicate authoritative PLAN (many LifePRO → one PLAN) | **0** |
| Duplicate LifePRO Coverage_ID in crosswalk | **0** |
| Orphan compat MPLAN (quikridr without quikplan PLAN) | **33 values — pre-fix**; resolved for quikplan post Phase 1 |
| Orphan auth MPLAN after Phase 1 only | **Possible** until Phase 2 P3E |
| New duplicate PLAN values introduced | **Low risk** — 33 unique targets; validated one-to-one |

---

## 7. DISCHO25 (Phase 0 add-on)

| Metric | Value |
|--------|-------|
| In crosswalk | Yes → `9DIS25` |
| In catalog | No (pre-fix) |
| In quikplan output | No (pre-fix) |
| PPBEN usage | Present in batch (discount riders) |
| Package | Same Issue #28 release — not separate issue |

---

## 8. Fleet-wide vs catalog-wide

| Dimension | Scope |
|-----------|-------|
| Product catalog correction | **100% of divergent catalog (33/33 plans)** |
| In-force policy touch (this batch) | **219 policies** (~1.9% PPBEN universe) |
| Future conversions | **All policies** using affected products get correct PLAN |

**Risk note:** Catalog fix is fleet-wide for product definitions; policy count scales with batch — full production book may differ from 219.
