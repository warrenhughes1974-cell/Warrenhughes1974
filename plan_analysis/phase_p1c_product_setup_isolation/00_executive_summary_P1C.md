# Phase P1C Executive Summary — Product Setup Isolation

**Date:** 2026-05-23  
**Phase:** P1C — Product Setup Isolation + Crosswalk Enrichment Preservation  
**Status:** Architecture & design complete — **no code changes**

---

## Objective

Isolate product setup conversion from the policy batch **without redesigning product semantics**, preserving `Sync_Rulebook_quikplan.csv` mappings, defaults, and transformation behavior exactly.

---

## Confirmed Business Architecture (Honored)

| Table | Role |
|---|---|
| **quikplan** | Master Product Configuration — base plans, riders, supplemental, ADB, fees, disability |
| **quikmstr + quikridr** | Policy-level transactional tables referencing quikplan.PLAN |
| **Crosswalk** | Configuration enrichment: Coverage_ID → PLAN, FORM, DESCR, PLANNAME |

**Not in scope:** moving riders out of quikplan, semantic decomposition, rulebook rewrite.

---

## Core Recommendation

Extract the existing quikplan rulebook engine into a **shared module** (`qla_core/quikplan_converter.py`), invoke it from:

1. A new **Product Setup Conversion subprocess** (primary)
2. app.py (during transition — same function, zero behavior change)

Policy batch optionally **skips quikplan** when `QLA_PRODUCT_SETUP_ISOLATED=1`, reading pre-built `output/quikplan.csv`.

---

## Ten Deliverables

| # | Deliverable | Location |
|---|---|---|
| 1 | Standalone product setup architecture | `01_recommended_standalone_product_setup_architecture.md` |
| 2 | Folder structure | `02_recommended_folder_structure.md` |
| 3 | Subprocess execution model | `03_recommended_subprocess_execution_model.md` |
| 4 | UI integration approach | `04_recommended_ui_integration_approach.md` |
| 5 | Dependency analysis | `05_product_setup_dependency_analysis.csv` |
| 6 | Validation/governance enhancements | `06_validation_governance_enhancement_recommendations.md` |
| 7 | Minimal-impact implementation plan | `07_minimal_impact_implementation_plan.md` |
| 8 | Code isolation/reuse map | `08_code_isolation_reuse_map.md` |
| 9 | Rollback strategy | `09_recommended_rollback_strategy.md` |
| 10 | Future actuarial extension points | `10_future_actuarial_extension_points.md` |

---

## Key Dependencies (from P1C Analysis)

| Asset | Preservation Requirement |
|---|---|
| `Sync_Rulebook_quikplan.csv` | **MUST NOT bypass** — 80 mapping/default rules |
| `plan_analysis/quikplan_source.csv` | Read-only primary source (133 rows) |
| `Policy Form Crosswalk 5.22.26` | Business enrichment authority (141 rows) |
| `PCOMP.csv` | Rulebook lookup for MINUNIT/MAXUNIT |
| `Master_Value_Translation.csv` | Field value translation (trans_map) |
| `Master_Crosswalk.csv` plan rows | Current PLAN code map (~237 rows) — segregate in P3 |
| `app.py TABLE_SCHEMAS['quikplan']` | 79-field output schema order |
| `output/quikplan.csv` | Catalog consumed by quikridr.MPLAN (11,698 rows) |

---

## Governance (Additive Only)

Default: **WARN + manifest**, emit proceeds.

| Diagnostic | Current Finding |
|---|---|
| Duplicate PLAN | 1 (`9DIS25` × 2) |
| Crosswalk FORM mismatch | 94 of 102 matched plans |
| Orphan MPLAN | 7 codes (56 quikridr rows) |
| Blank MPLAN | 2,348 quikridr rows (policy data quality) |

No auto-remediation. No silent overrides.

---

## Implementation Roadmap

```
P1C ✅  Architecture (this phase)
P2A     Extract qla_core/quikplan_converter.py + parallel diff validation
P2B     Product setup subprocess runner
P2C     app.py UI launcher (~155 lines)
P2D     Batch isolation cutover
P3      Crosswalk authority migration (business-gated)
P4      quikplan.dbf generation (mirror Phase 21B)
P5+     HRIGPKEY / actuarial loads (future)
```

**Validation gate:** isolated runner must produce identical `quikplan.csv` to current app.py before batch cutover.

---

## app.py Impact (Future P2)

| Change | Est. Lines |
|---|---|
| Import shared converter | ~5 |
| Product Setup tab + subprocess launcher | ~155 |
| Batch skip quikplan flag | ~15 |
| **Claims orchestration** | **0 changes** |

---

## Explicit Non-Actions (P1C)

- No app.py modifications
- No Sync_Rulebook_quikplan changes
- No source extract mutation
- No rider/plan semantic redesign
- No HRIGPKEY / actuarial implementation
- No claims governance changes

---

## Next Step

**P2A — Shared module extraction** with parallel-run diff validation against current `output/quikplan.csv` (133 rows, 132 unique PLAN).

Re-run dependency analysis:

```bash
python plan_analysis/phase_p1c_product_setup_isolation/phase_p1c_dependency_analysis_runner.py
```
