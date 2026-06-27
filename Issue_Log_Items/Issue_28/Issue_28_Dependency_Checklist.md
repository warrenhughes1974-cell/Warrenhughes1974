# Issue #28 — Dependency Checklist

**Gate date:** 2026-06-24  
**Baseline version:** v57.34  
**Target version:** v57.35 (proposed)

Legend: **Met** | **Missing** | **N/A** | **Conditional**

---

## 1. Source data readiness

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1.1 | LifePRO extracts present in `QLA_Migration/Source/` | **Met** | 12 files including `PPBEN_PolicyBenefit_Extract_20260530.csv`, `PCOVR_Coverage_Extract_20260530.csv`, `PPOLC_PolicyMaster_Extract_20260530.csv` |
| 1.2 | Extract row count > 0 | **Met** | PPBEN and PCOVR used in batch; Issue #26 validated 7,002 quikridr rows |
| 1.3 | quikplan source (`plan_analysis/quikplan_source.csv`) available | **Met** | 141 coverage rows; Intake traces use this feed |
| 1.4 | Column headers documented | **Met** | Rulebooks + `Sync_Rulebook_quikplan.csv` (`COVERAGE_ID → PLAN`) |
| 1.5 | Extract date matches batch under test | **Met** | Source dated 20260530; output at `QLA_Migration/Output/` |
| 1.6 | Re-extract required for #28 | **N/A** | Remediation is authority/config — not missing LifePRO data |

---

## 2. Crosswalk authority readiness

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 2.1 | Policy Form Crosswalk 5.22.2026 in repo | **Met** | `plan_analysis/source_data/crosswalk/Policy Form Crosswalk 5.22.26.xlsx` (141 rows) |
| 2.2 | Crosswalk structurally complete | **Met** | `Issue_28_Crosswalk_Inventory.csv` — 141 unique Coverage_IDs |
| 2.3 | Crosswalk designated binding by **client in writing** | **Missing** | Issue text states crosswalk is authoritative; **no signed client waiver / email / issue sign-off artifact in repo** |
| 2.4 | Internal engineering acceptance of crosswalk as emit authority | **Met** | Intake + Planning + P3C module docstring align on `crosswalk_ql_plan_code` |

---

## 3. Product catalog readiness

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 3.1 | `crosswalk_ql_plan_code` column exists | **Met** | `plan_governance/product_catalog_crosswalk.csv` — 140 rows |
| 3.2 | No blank authoritative values (catalog rows present) | **Met** | 0 blank `crosswalk_ql_plan_code` in 140 catalog rows |
| 3.3 | 33 divergent rows match xlsx authoritative values | **Met** | Gate script: 0 mismatches between catalog `crosswalk_ql_plan_code` and xlsx for `CROSSWALK_DIVERGENT` rows |
| 3.4 | No duplicate `lifepro_coverage_id` in catalog | **Met** | 0 duplicates |
| 3.5 | DISCHO25 catalog row present | **Missing** | Only xlsx ID absent from catalog: `DISCHO25` |
| 3.6 | Migration catalog copy synchronized | **Conditional** | `QLA_Migration/Mapping/product_catalog_crosswalk.csv` = 133 rows vs governance 140 — **must sync before release** |
| 3.7 | Null/blank fallback rule documented | **Met** | Planning: prefer `crosswalk_ql_plan_code` when non-blank, else `ql_plan_code` |

---

## 4. Runtime code dependency readiness

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 4.1 | Target function identified | **Met** | `load_product_catalog_crosswalk()` in `qla_core/product_catalog_authority.py:417–439` |
| 4.2 | Call chain mapped | **Met** | `load_crosswalk_authority()` → `product_plan_map` → `quikplan_converter._apply_crosswalk_value()`; batch via `app.py:5065–5076` |
| 4.3 | Change scope bounded | **Met** | ~15–25 lines; no rulebook change required for Phase 1 |
| 4.4 | P3E Phase 2 dependency understood | **Met** | quikridr MPLAN requires quikplan authoritative PLAN universe first |
| 4.5 | Version bump path clear | **Met** | AGENTS.md → v57.35 on `app.py` / `QLA_Migration/app.py` |

---

## 5. Validation dependency readiness

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 5.1 | Issue #28 validator defined | **Missing** | `_validate_issue28_plan_mapping.py` planned — **not yet created** (Development deliverable) |
| 5.2 | Intake comparison script exists | **Met** | `Issue_Log_Items/Issue_28/_issue28_intake_analysis.py` |
| 5.3 | Protected issue validators exist | **Met** | `validate_mpolicy_width.py` (#25), `validate_issue26_mprem.py` (#26), `validate_issue21m_quikmemo.py` (#21M), `validate_issue21m_dbf_packaging.py` (#21M-FU), `validate_issue21k_munit.py` (#21K) |
| 5.4 | Full batch runner available | **Met** | `QLA_Migration/_run_full_batch_test.py` |
| 5.5 | Before-state baseline captured | **Met** | v57.34 `QLA_Migration/Output/quikplan.csv` + `Issue_28_Mapping_Differences.csv` |

---

## 6. Regression dependency readiness

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 6.1 | Protected issue regression plan documented | **Met** | `Issue_28_Regression_Impact.md` |
| 6.2 | v57.34 regression evidence available | **Met** | `Release_Notes/v57.34_Release_Notes.md` — #25/#26/#21M PASS |
| 6.3 | Post-fix baseline generation plan | **Met** | Implementation Strategy § Validation |
| 6.4 | Rate/CSO downstream review identified | **Conditional** | phase_r3 `PLAN_NOT_IN_TARGET` — internal rate review recommended (Q5) |

---

## 7. Client UAT dependency readiness

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 7.1 | Client examples identified | **Met** | 10827 MN5K, 0823 960CH, 0824 P DIS |
| 7.2 | Before-state measurable | **Met** | v57.34 quikplan output lines 9, 14, 19 |
| 7.3 | Client re-UAT scope **accepted in writing** | **Missing** | 33 PLAN changes require re-UAT — **no client acceptance artifact in repo** |
| 7.4 | UAT test script drafted | **Met** | `Issue_28_Implementation_Strategy.md` § Client UAT |

---

## 8. Release / deployment dependency readiness

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 8.1 | Release version slot available | **Met** | v57.35 proposed; v57.34 released |
| 8.2 | Release notes template | **Met** | `Release_Notes/v57.34_Release_Notes.md` pattern |
| 8.3 | Rollback path documented | **Met** | Compat column preserved; git revert on single function |
| 8.4 | Catalog copy sync in deploy checklist | **Conditional** | Required before production — migration copy lag |

---

## 9. Governance dependency readiness

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 9.1 | AGENTS.md surgical-change rules | **Met** | Option A is single-function change |
| 9.2 | Protected issues list enforced | **Met** | #21M, #21M-FU, #21K, #25, #26 — no planned code touch |
| 9.3 | plan_change_manifest.csv available | **Met** | 33 divergent transitions documented |
| 9.4 | Issue tracking update path | **Conditional** | `Issue_Log_Master_Tracking_Sheet.md` update deferred to Closure |

---

## Framework checklist (`AI_Agents/Dependency_Gate.md`)

| Section | Overall |
|---------|---------|
| Source data | **Met** |
| Field definitions | **Met** (quikplan.PLAN) |
| Client clarification | **Missing** (Q1, Q2) |
| Evidence | **Met** |
| Regression guards | **Met** (plan preserves #25/#26; no rulebook change) |

---

## Summary counts

| Status | Count |
|--------|------:|
| Met | 38 |
| Missing | 5 |
| Conditional | 4 |
| N/A | 1 |
