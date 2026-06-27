# Issue #28 — Validation Dependencies

**Gate date:** 2026-06-24  
**Baseline:** v57.34 | **Target:** v57.35

---

## Validation dependency map

```
Development complete
    ├── Issue #28 PLAN mapping validator (NEW)
    ├── Intake comparison script (EXISTING)
    ├── Full batch test (EXISTING)
    ├── Protected issue validators (#25, #26, #21M, #21M-FU, #21K)
    └── Phase 2: P3E MPLAN trace samples (CONDITIONAL)
```

---

## Issue #28 — primary validation

| ID | Validator / script | Status | Purpose | Pass criteria |
|----|-------------------|--------|---------|---------------|
| V-28-01 | `_validate_issue28_plan_mapping.py` | **To create** (Development) | 141 crosswalk rows vs quikplan PLAN | 0 mismatches vs `crosswalk_ql_plan_code` |
| V-28-02 | `Issue_Log_Items/Issue_28/_issue28_intake_analysis.py` | **Exists** | Regenerate comparison CSVs | `mismatches: 0` in `_population_stats.json` |
| V-28-03 | Client example spot check (manual) | **Procedure defined** | 3 client examples | 1CSIMN, 960CWP, 94PDIS in quikplan |
| V-28-04 | `Issue_28_Mapping_Differences.csv` diff | **Baseline exists** | Before/after | All `matches_authoritative=Y` |

---

## DISCHO25 validation

| ID | Check | Pass criteria |
|----|-------|---------------|
| V-D25-01 | Catalog contains `DISCHO25` | Row present in governance + migration catalogs |
| V-D25-02 | quikplan emits PLAN `9DIS25` | Row in quikplan.csv for coverage |
| V-D25-03 | P3C unauthorized manifest | DISCHO25 not listed as MISSING_CATALOG_MAPPING |

**Package:** Same remediation release (Phase 0) — **not a separate issue** (see Dependency Gate § DISCHO25).

---

## quikplan output validation

| ID | Check | Dependency |
|----|-------|------------|
| V-QP-01 | 141 quikplan rows (or documented count if source excludes DISCHO25) | Batch re-run |
| V-QP-02 | No PLAN values with spaces (authoritative codes) | Schema governance |
| V-QP-03 | Unique PLAN count stable (~139–140) | Population summary |
| V-QP-04 | Variation audit regenerated | `variation_code_audit.csv` |
| V-QP-05 | CSO QA review | `cso_mortality_crosswalk_qa.csv` |

---

## quikridr / MPLAN validation (Phase 2)

| ID | Check | Prerequisite |
|----|-------|--------------|
| V-RDR-01 | Sample policies with 0823/0824/10827 riders | Phase 1 quikplan PASS |
| V-RDR-02 | P3E trace — no UNAUTHORIZED for remediated PLAN_CODEs | `QLA_CLOSED_MPLAN_AUTHORITY=1` |
| V-RDR-03 | MPLAN matches authoritative PLAN for client examples | Phase 2 enabled |
| V-RDR-04 | Referential integrity — MPLAN in quikplan PLAN set | phase_p3d pattern |

**Dependency:** Phase 2 validation **cannot run** until Phase 1 quikplan authoritative emit verified.

---

## Protected issue validators (mandatory regression)

| Issue | Script | Location | Must PASS |
|-------|--------|----------|-----------|
| **#25** MPOLICY width | `validate_mpolicy_width.py` | `tools/validators/` (stub: `QLA_Migration/`) | **Yes** |
| **#26** MPREM | `validate_issue26_mprem.py` | `tools/validators/` | **Yes** |
| **#21M** QUIKMEMO | `validate_issue21m_quikmemo.py` | `tools/validators/` | **Yes** |
| **#21M-FU** DBF packaging | `validate_issue21m_dbf_packaging.py` | `tools/validators/` | **Yes** |
| **#21K** MUNIT | `validate_issue21k_munit.py` | `tools/validators/` | **Yes** (env-dependent DBF) |

**Gate assessment:** All scripts **exist**. No #28 change should modify their code paths. Re-run required post v57.35 batch.

---

## Batch orchestration

| Script | Role |
|--------|------|
| `QLA_Migration/_run_full_batch_test.py` | End-to-end batch |
| `validate_output.py` (repo root) | Schema integrity — imported by app |

---

## Validation sequencing (post-Development)

| Order | Activity |
|-------|----------|
| 1 | Full batch re-run → v57.35 output |
| 2 | V-28-01 + V-28-02 (PLAN mapping) |
| 3 | Protected validators #25, #26, #21M, #21M-FU, #21K |
| 4 | V-QP-04, V-QP-05 (enrichment spot check) |
| 5 | Phase 2: V-RDR-* if P3E in scope |
| 6 | Generate validation report for Closure |

---

## Pre-Development validation gap

| Gap | Owner | When resolved |
|-----|-------|---------------|
| V-28-01 not implemented | Development Agent | During Development (G4) |

This gap does **not** block Ownership Decision or Risk Agent.
