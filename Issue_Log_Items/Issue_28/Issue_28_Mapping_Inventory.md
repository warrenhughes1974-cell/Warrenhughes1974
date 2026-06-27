# Issue #28 — Mapping Artifact Inventory

**Engine version reviewed:** v57.34  
**Intake date:** 2026-06-24  
**Mode:** Read-only investigation — no repository modifications

---

## 1. Authoritative Business Source

| Artifact | Path | Role | Rows |
|----------|------|------|------|
| Policy Form Crosswalk (5.22.2026) | `plan_analysis/source_data/crosswalk/Policy Form Crosswalk 5.22.26.xlsx` | Client-approved authoritative LifePRO Coverage_ID → QL Plan Code | 141 |
| Client attachment (verified identical structure) | `%TEMP%\Policy Form Crosswalk 5.22.26 (2).xlsx` | Same workbook supplied with Issue #28 | 141 |

**Columns:** LifePRO Coverage_ID, (unused), QL Plan Code, QL Form Number, QL Plan Description, QL Friendly Name

---

## 2. Runtime Mapping Tables

| Artifact | Path | Runtime use | Notes |
|----------|------|---------------|-------|
| Master_Crosswalk.csv | `QLA_Migration/Mapping/Master_Crosswalk.csv` | Policy-number crosswalk + legacy product PLAN map (`cw_map`) | ~5,400 rows total; ~427 non-policy (product) rows |
| product_catalog_crosswalk.csv (governance) | `plan_governance/product_catalog_crosswalk.csv` | **Primary runtime product catalog** (140 rows) | Loaded by `load_crosswalk_authority()` and P3E MPLAN resolver |
| product_catalog_crosswalk.csv (migration copy) | `QLA_Migration/Mapping/product_catalog_crosswalk.csv` | Mirror copy (133 rows — **7 rows behind governance**) | Not the default runtime path |
| legacy_product_crosswalk_quarantine.csv | `plan_governance/quarantine/legacy_product_crosswalk_quarantine.csv` | Quarantined legacy product rows from P2E separation | Not loaded at batch runtime |
| crosswalk_governance_manifest.csv | `plan_governance/manifests/crosswalk_governance_manifest.csv` | Governance tracking manifest | Analysis/governance only |

---

## 3. Rulebooks & Translation

| Artifact | Path | PLAN-related rule |
|----------|------|-------------------|
| Sync_Rulebook_quikplan.csv | `QLA_Migration/Configs/Sync_Rulebook_quikplan.csv` | `COVERAGE_ID → PLAN` ("Map to crosswalk via engine") |
| Sync_Rulebook_quikridr.csv | `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv` | `PLAN_CODE → MPLAN` |
| Master_Value_Translation.csv | `QLA_Migration/Mapping/Master_Value_Translation.csv` | Value translations (not primary PLAN authority) |

---

## 4. Source Data Feeds

| Artifact | Path | Role |
|----------|------|------|
| quikplan_source.csv | `plan_analysis/quikplan_source.csv` | Distinct PCOMP/PPBEN coverage rows → quikplan conversion |
| PPBEN (LifePRO export) | Batch `Source/` package | Rider PLAN_CODE for quikridr MPLAN |
| PCOMP | Batch `Source/` package | Component metadata joined via rulebook lookups |

---

## 5. Converter Modules (Code — Read Only)

| Module | Path | PLAN/MPLAN responsibility |
|--------|------|---------------------------|
| app.py | `app.py` / `QLA_Migration/app.py` v57.34 | Batch orchestration; loads crosswalk; quikridr MPLAN crosswalk + optional P3E authority |
| quikplan_converter.py | `qla_core/quikplan_converter.py` | quikplan row conversion; `_apply_crosswalk_value()` for PLAN |
| product_catalog_authority.py | `qla_core/product_catalog_authority.py` | Layered authority: `load_crosswalk_authority()`, `load_product_catalog_crosswalk()`, P3C/P3E closed catalog |
| crosswalk_enrichment.py | `qla_core/crosswalk_enrichment.py` | Optional xlsx overlay (`CROSSWALK_OVERLAY`, default OFF) |
| product_authority_diagnostics.py | `qla_core/product_authority_diagnostics.py` | Diagnostic tooling (not batch runtime) |

---

## 6. Generated / Staged Outputs (Evidence)

| Artifact | Path | Role |
|----------|------|------|
| quikplan.csv | `QLA_Migration/Output/quikplan.csv` | 141 plan rows; PLAN column = emitted QLAdmin plan codes |
| quikridr.csv | `QLA_Migration/Output/quikridr.csv` | 7,002 rider rows; MPLAN column |
| variation_code_audit.csv | Batch output dir | Variation classification audit |

---

## 7. Prior Phase Analysis (Historical — Not Runtime)

| Artifact | Path | Relevance to #28 |
|----------|------|------------------|
| phase_p2e_authority_separation_runner.py | `plan_analysis/phase_p2e_authority_separation/` | **Created** `product_catalog_crosswalk.csv` seeded from stable emit |
| phase_p3b_strict_authority/ | `plan_analysis/phase_p3b_strict_authority/` | Documented passthrough PLAN values vs crosswalk |
| phase_p3c_closed_product_authority/ | `plan_analysis/phase_p3c_closed_product_authority/` | Identified `CROSSWALK_DIVERGENT` rows including client examples |
| phase_p3d_mplan_authority_impact_analysis/ | `plan_analysis/phase_p3d_mplan_authority_impact_analysis/` | quikplan vs quikridr authority path divergence |
| plan_change_manifest.csv | `plan_governance/manifests/plan_change_manifest.csv` | Records intended PLAN changes for divergent rows |
| unresolved_passthrough_ids.csv | `plan_analysis/phase_p2d_governance_audit/scaffold/` | Lists passthrough IDs requiring QL Plan Code assignment |

---

## 8. Environment Flags Affecting Mapping

| Flag | Default | Effect |
|------|---------|--------|
| `CROSSWALK_OVERLAY` | `0` (OFF) | When OFF, Policy Form Crosswalk xlsx is **not** applied to quikplan output |
| `QLA_CLOSED_MPLAN_AUTHORITY` | `0` (OFF) | When OFF, quikridr MPLAN uses raw `Master_Crosswalk` passthrough |
| `QLA_ALLOW_LEGACY_MPLAN_FALLBACK` | `0` (OFF) | When OFF, P3E resolver rejects non-authoritative MPLAN |
| `QLA_PRODUCT_UAT_OVERLAY` | `0` (OFF) | Isolated product-setup UAT overlay only |

---

## 9. Hardcoded / In-Code Mapping

| Location | Content |
|----------|---------|
| `app.py` | `PAID_UP_ADDITION_PRODUCTS`, `PAID_UP_ADDITION_LIFEPRO_SOURCE_CODES` — PUA rider MPLAN inheritance |
| `qla_core/product_business_test_cut.py` | Business test cut includes divergent examples (`0823 960CH`, `0824 P DIS`, `10827 MN5K`) |
| `qla_core/non_product_row_governance.py` | BENEFIT_SEQ 99 / BENEFIT_TYPE UV governance (non-PLAN) |

---

## 10. Key Structural Finding

The product catalog CSV maintains **dual PLAN columns**:

| Column | Purpose | Used at batch runtime? |
|--------|---------|------------------------|
| `ql_plan_code` | Compatibility / stable emit (often LifePRO passthrough) | **YES** — via `load_product_catalog_crosswalk()` |
| `crosswalk_ql_plan_code` | Policy Form Crosswalk 5.22.2026 authoritative QL Plan Code | **NO** in default batch path; used by P3C closed catalog analysis and P3E resolver index |

Rows where these differ are flagged `mapping_status=CROSSWALK_DIVERGENT` (33 rows).
