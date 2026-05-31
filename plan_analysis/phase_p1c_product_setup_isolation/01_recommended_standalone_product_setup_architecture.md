# Recommended Standalone Product Setup Architecture (Phase P1C)

**Date:** 2026-05-23  
**Scope:** Architecture design only — no conversion rewrite  
**Principle:** Preserve existing rulebook-driven product logic; isolate lifecycle from policy batch

---

## Business Context (Confirmed)

`quikplan.dbf` / `quikplan.csv` is the **Master Product Configuration Table** for QLAdmin. It correctly includes:

- Base plans
- Riders
- Supplemental coverages
- Disability products
- ADB products
- Fee products
- Optional coverages

`quikmstr` + `quikridr` are **policy-level transactional tables** that reference configured PLAN records from quikplan.

**This architecture does NOT decompose products or move riders out of quikplan.**

---

## What Is Working (Preserve As-Is)

The current conceptual pipeline is correct:

```
LifePRO Coverage_ID (quikplan_source.csv)
    → join Product Crosswalk (Policy Form Crosswalk 5.22.26)
    → configuration enrichment (PLAN, FORM, DESCR, PLANNAME)
    → Sync_Rulebook_quikplan.csv (mappings + defaults + transformations)
    → PCOMP lookup (MINUNIT/MAXUNIT)
    → Master_Value_Translation (field value translation)
    → Master_Crosswalk plan map (COVERAGE_ID → QL Plan Code on PLAN field)
    → output/quikplan.csv
```

This is **configuration enrichment**, not semantic redesign.

---

## Architectural Goal

**Isolate product setup from the main conversion batch** because:

| Property | Product Setup | Policy Conversion |
|---|---|---|
| Frequency | Load once; business maintains | Rerun per migration batch |
| Nature | Static configuration catalog | Transactional policy data |
| Governance | Product / actuarial review | Claims / policy review |
| Blast radius | Affects all policies referencing PLAN | Per-policy |

---

## Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  app.py v55.7 — Orchestration Shell                             │
│  ┌──────────────────────┐  ┌────────────────────────────────┐ │
│  │ Policy Batch Tab     │  │ Product Setup Conversion Tab   │ │
│  │ (existing)           │  │ (new — launcher only)          │ │
│  └──────────┬───────────┘  └───────────────┬────────────────┘ │
└─────────────┼──────────────────────────────┼──────────────────┘
              │                              │
              │ subprocess                   │ subprocess
              ▼                              ▼
   ┌──────────────────────┐    ┌──────────────────────────────────┐
   │ Policy conversion    │    │ Product Setup Conversion Runner  │
   │ (quikmstr, quikridr, │    │ plan_governance/phase_p2/        │
   │  quikclnt, claims…)  │    │ product_setup_runner.py          │
   └──────────────────────┘    └──────────────────────────────────┘
              │                              │
              │ reads                        │ reads
              ▼                              ▼
   output/quikplan.csv ◄────── staged/emitted quikplan.csv
   (pre-built catalog)          (from isolated runner)
```

### Core Design Rules

1. **Single transformation engine** — one shared module implements rulebook processing; app.py and subprocess both call it (no duplicated logic).
2. **Crosswalk = enrichment overlay** — Policy Form Crosswalk supplies PLAN/FORM/DESCR/PLANNAME; all other fields remain rulebook-driven.
3. **Rulebook is authoritative for behavior** — `Sync_Rulebook_quikplan.csv` is never bypassed, replaced, or hardcoded around.
4. **Additive governance only** — diagnostics and manifests; no silent row drops unless explicitly enabled.
5. **Policy batch skips quikplan** when isolated mode is active — reads existing `output/quikplan.csv`.

---

## Pipeline Stages (Product Setup Runner)

| Stage | Action | Changes Behavior? |
|---|---|---|
| 1. Load Source | Read `plan_analysis/quikplan_source.csv` | No |
| 2. Crosswalk Join | Join Policy Form Crosswalk on `COVERAGE_ID` | Enrichment only |
| 3. Rulebook Transform | Apply `Sync_Rulebook_quikplan.csv` exactly as app.py | **No — preserved** |
| 4. Crosswalk Overlay | Apply crosswalk PLAN/FORM/DESCR/PLANNAME when matched | Enrichment (business authority) |
| 5. Plan Code Map | Apply plan crosswalk map (currently Master_Crosswalk plan rows) | Preserved until segregated |
| 6. PCOMP Lookup | MINUNIT/MAXUNIT via rulebook lookup | No |
| 7. Governance Diagnostics | Duplicate PLAN, missing crosswalk, orphan MPLAN | **Additive only** |
| 8. Stage | Write `plan_governance/staged/quikplan_staged.csv` | New path |
| 9. Validate | Schema order, PLAN key, row count audit | Additive |
| 10. Emit | Copy to `output/quikplan.csv` (gated) | Same output contract |
| 11. DBF (optional) | Generate `quikplan.dbf` from emitted CSV | Mirror Phase 21B pattern |

---

## Shared Module Extraction (Future P2 Implementation)

Extract from `app.py` into `qla_core/quikplan_converter.py`:

- `TABLE_SCHEMAS["quikplan"]` field list
- `normalize()` 
- Rulebook row loop (source → target mapping)
- quikplan-specific handlers: PAR pass-through, ROUTE_PAY_*, ROUTE_INS_*, age zfill
- PCOMP lookup loader
- `cw_map` application on PLAN field
- `trans_map` application

app.py `process_data()` calls `convert_quikplan(...)` instead of inline loop for quikplan table only. Policy tables remain inline until separately extracted.

---

## Isolation Mode for Policy Batch

Environment flag (proposed):

```
QLA_PRODUCT_SETUP_ISOLATED=1
```

When set, batch processing:

- **Skips** `quikplan` in table loop
- **Requires** existing `output/quikplan.csv`
- **Logs** product catalog timestamp / manifest reference
- **Runs** orphan MPLAN diagnostic (read-only) against quikridr if present

Default: `0` (current behavior — quikplan still in batch until cutover validated).

---

## Validation Before Cutover

Parallel-run acceptance test:

1. Run current app.py single-table quikplan conversion
2. Run isolated product setup runner with identical inputs
3. Diff `output/quikplan.csv` — must match field order, values, row count
4. Only then enable `QLA_PRODUCT_SETUP_ISOLATED=1` in batch

---

## Explicit Non-Goals (This Architecture)

- Moving riders out of quikplan
- Redesigning Sync_Rulebook_quikplan
- HRIGPKEY population
- Actuarial rate loads (QuikPlbd)
- Modifying claims orchestration
- Mutating source extracts
