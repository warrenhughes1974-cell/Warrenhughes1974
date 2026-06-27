# Issue #28 — Development Report

**Issue:** #28 — Incorrect Plan Number Mapping  
**Development Agent date:** 2026-06-24  
**Baseline version:** v57.34  
**Delivered version:** **v57.35**  
**Prior stages:** Intake ✅ | Planning ✅ | Dependency Gate ✅ (CONDITIONAL PASS) | Risk ✅ (CONDITIONAL GO)  
**Development authorization:** CONDITIONAL GO — approved remediation only  
**Status:** Development complete — **stop before Validation**

---

## 1. Executive summary

Development implemented all three approved phases for Issue #28:

1. **Phase 0** — Added missing `DISCHO25 → 9DIS25` catalog row; synced `QLA_Migration/Mapping/product_catalog_crosswalk.csv` to governance (141 data rows).
2. **Phase 1** — Promoted `crosswalk_ql_plan_code` to runtime authority in `load_product_catalog_crosswalk()`, correcting 33 PLAN mappings at emit time without modifying rulebooks or Master_Crosswalk.
3. **Phase 2** — Enabled P3E closed MPLAN authority by default and added batch post-quikplan resolver refresh so QUIKRIDR.MPLAN aligns with corrected quikplan PLAN universe.

No validation, regression testing, or batch re-run was executed per Development stop condition.

---

## 2. Pre-development verification

| Check | Result |
|-------|--------|
| Implementation matches Planning recommendation | ✅ Option A Phase 1 + Phase 0 + Phase 2 |
| Repository assumptions unchanged since Risk Agent | ✅ No conflicting commits detected |
| New blockers since Risk Agent | None |
| Protected issue code paths | ✅ Not modified |

---

## 3. Implementation detail

### Phase 0 — DISCHO25 catalog completeness

**Evidence:** `Issue_28_DISCHO25_Investigation.md` — DISCHO25 is distinct from DISCHO247C (`9DIS25` vs `9DS24C`).

**Row added** to `plan_governance/product_catalog_crosswalk.csv` (inserted after DISCHO247C):

| Field | Value |
|-------|-------|
| lifepro_coverage_id | DISCHO25 |
| ql_plan_code | 9DIS25 |
| crosswalk_ql_plan_code | 9DIS25 |
| authority_source | POLICY_FORM_CROSSWALK |
| mapping_status | STABLE_EMIT |

Migration copy fully synced via file copy from governance.

### Phase 1 — Runtime authority promotion

**File:** `qla_core/product_catalog_authority.py`  
**Function:** `load_product_catalog_crosswalk()`

Logic: for each catalog row, use `crosswalk_ql_plan_code` when non-blank; otherwise fall back to `ql_plan_code`. Compat column preserved.

**Spot-check (Python REPL, post-change):**

| Coverage_ID | Runtime PLAN |
|-------------|--------------|
| 10827 MN5K | 1CSIMN |
| 0823 960CH | 960CWP |
| 0824 P DIS | 94PDIS |
| DISCHO25 | 9DIS25 |
| DISCHO247C | 9DS24C |

Catalog map size: 141 entries.

### Phase 2 — P3E MPLAN alignment

**Changes:**

1. `closed_mplan_authority_enabled()` — default `QLA_CLOSED_MPLAN_AUTHORITY=1` (opt-out with `0|false|no`).
2. Batch loop in `app.py` and `QLA_Migration/app.py` — after quikplan.csv write, call `_init_mplan_authority()` to refresh resolver with current batch quikplan output.

**Discovery during implementation:** Batch previously initialized P3E resolver at startup using **prior-run** quikplan.csv. Without post-quikplan refresh, Phase 2 would resolve MPLAN against stale PLAN universe. Refresh hook added surgically after quikplan emit.

### Version bump — v57.35

Updated in `app.py` and `QLA_Migration/app.py`:

- Header version block + change note
- Window title
- Header label
- Batch initialization log string

---

## 4. Files modified

| File | Phase |
|------|-------|
| `plan_governance/product_catalog_crosswalk.csv` | 0 |
| `QLA_Migration/Mapping/product_catalog_crosswalk.csv` | 0 |
| `qla_core/product_catalog_authority.py` | 1, 2 |
| `app.py` | 1, 2 |
| `QLA_Migration/app.py` | 1, 2 |

## 5. Files created

| File | Purpose |
|------|---------|
| `tools/validators/validate_issue28_plan_mapping.py` | Issue #28 PLAN validator for Validation Agent |
| `Issue_28_Code_Changes.md` | Detailed diffs and rationale |
| `Issue_28_File_Modification_Log.md` | Modification inventory |
| `Issue_28_Implementation_Summary.md` | Executive summary |
| `Issue_28_PreValidation_Checklist.md` | Validation handoff checklist |
| `Issue_28_Development_Report.md` | This report |

---

## 6. Functions modified

| Function | File | Change |
|----------|------|--------|
| `load_product_catalog_crosswalk()` | `qla_core/product_catalog_authority.py` | Authority column precedence |
| `closed_mplan_authority_enabled()` | `qla_core/product_catalog_authority.py` | Default ON |
| `process_data()` batch loop | `app.py`, `QLA_Migration/app.py` | Post-quikplan P3E refresh |

---

## 7. Deferred work

| Item | Phase | Reason |
|------|-------|--------|
| `mapping_status` → AUTHORITY_ALIGNED for 33 rows | 3 | Optional governance cleanup |
| `plan_change_manifest.csv` refresh | 3 | Post-validation |
| P2E generator compat seed update | 3 | Only if catalog regenerated |
| RUN_GUIDE env var documentation | Release | Release Integration scope |
| Batch re-run + evidence archive | Validation | Explicitly excluded from Development |

---

## 8. Assumptions discovered during implementation

1. **Stale P3E resolver at batch start** — Required post-quikplan refresh; not documented in Planning but necessary for correct Phase 2 behavior.
2. **Migration catalog drift (B-05)** — Resolved by full file sync (141 rows); was 133 rows with missing DISCHO20 B, DISCHO80, DISCHO90, DISCHO25.
3. **Catalog row count** — 141 authoritative crosswalk mappings + DISCHO25 = 141 total data rows in catalog (crosswalk xlsx has 141; DISCHO25 was the missing catalog gap).

---

## 9. Protected issues

No code changes in Issue #21M, #21M-FU, #21K, #25, or #26 implementation paths. Regression compatibility must be confirmed by Validation Agent.

---

## 10. Syntax verification

```
python -m py_compile qla_core/product_catalog_authority.py  → PASS
python -m py_compile tools/validators/validate_issue28_plan_mapping.py  → PASS
ast.parse(app.py)  → PASS
```

Runtime spot-check of `load_product_catalog_crosswalk()` → PASS (see Section 3).

---

## 11. Development stop condition

Development Agent **stops here**. Do not proceed to Validation, Regression, Client UAT, Closure, or Release Integration in this stage.

---

# Cursor Prompt — Validation Agent

You are continuing work on the **LifePRO → QLAdmin Conversion Project**.

**Current converter version:** **v57.35**

**Target validation version:** v57.35 (no further code changes unless Validation finds defects)

**Issue:** **Issue #28 — Incorrect Plan Number Mapping**

The following stages have been completed:

* Intake Agent ✅
* Planning Agent ✅
* Dependency Gate ✅ (CONDITIONAL PASS)
* Ownership Decision ✅
* Risk Agent ✅ (CONDITIONAL GO)
* **Development Agent ✅**

Do **not** repeat prior stages.

Begin **Validation Agent** only.

---

## Repository Governance

This repository follows the AI Issue Resolution Framework.

Validation is authorized under the **CONDITIONAL GO** from Risk Agent.

Execute validation and produce validation reports only.

Do **not** perform Client UAT, Closure, or Release Integration unless explicitly instructed after Validation PASS.

Stop after Validation stage deliverables are complete.

---

## Required Reading

Review all Issue #28 artifacts before validating:

```text
Issue_Log_Items/Issue_28/
```

**Required:**

* `Issue_28_Intake_Report.md`
* `Issue_28_Planning_Report.md`
* `Issue_28_Risk_Review_Report.md`
* `Issue_28_Implementation_Strategy.md`
* `Issue_28_Validation_Matrix.md`
* `Issue_28_Rollback_Checklist.md`
* `Issue_28_PLAN_Comparison_Report.md`
* `Issue_28_DISCHO25_Investigation.md`
* **`Issue_28_Development_Report.md`** (this file)
* **`Issue_28_Code_Changes.md`**
* **`Issue_28_PreValidation_Checklist.md`**

---

## Summary of completed Development work

### Phase 0 — DISCHO25 catalog row

* Added `DISCHO25 → 9DIS25` to `plan_governance/product_catalog_crosswalk.csv`
* Synced `QLA_Migration/Mapping/product_catalog_crosswalk.csv` (141 data rows)

### Phase 1 — Runtime authority

* `qla_core/product_catalog_authority.py` → `load_product_catalog_crosswalk()` now prefers `crosswalk_ql_plan_code`, falls back to `ql_plan_code`
* Corrects **33** CROSSWALK_DIVERGENT PLAN mappings at quikplan emit

### Phase 2 — P3E MPLAN alignment

* `closed_mplan_authority_enabled()` default ON (`QLA_CLOSED_MPLAN_AUTHORITY=1`)
* Batch post-quikplan `_init_mplan_authority()` refresh in `app.py` and `QLA_Migration/app.py`

### Version

* **v57.35** in `app.py` and `QLA_Migration/app.py`

### New validator (not yet run)

* `tools/validators/validate_issue28_plan_mapping.py`

---

## Key Development findings for Validation

1. **No batch re-run was performed** — all quikplan/quikridr output in `QLA_Migration/Output/` is still v57.34 baseline until Validation runs full batch.
2. **Post-quikplan P3E refresh** was added — verify P3E traces use corrected PLAN universe, not stale pre-batch quikplan.
3. **Migration catalog sync** resolved B-05 — confirm governance and migration copies are identical before batch.
4. **DISCHO25** is independent of the 33 divergent rows — validate PLAN `9DIS25` appears in quikplan output.

---

## Repository constraints

* Surgical validation only — do not refactor unrelated code
* Preserve QLA formatting and QuikPlan schema integrity
* Do not modify protected issue implementations (#21M, #21M-FU, #21K, #25, #26)
* AGENTS.md: preserve field ordering/types/lengths; no blank MRIDRID regressions
* Rollback reference: v57.34 tagged output + `Issue_28_Rollback_Checklist.md`

---

## Validation objectives

### P0 — Issue #28 core

| ID | Objective | Pass criteria |
|----|-----------|---------------|
| V-01 | Re-run `_issue28_intake_analysis.py` on v57.35 output | `mismatches: 0` |
| V-02 | Run `tools/validators/validate_issue28_plan_mapping.py` | 141/141 authoritative match |
| V-03 | Client examples in quikplan.csv | 10827 MN5K→1CSIMN, 0823 960CH→960CWP, 0824 P DIS→94PDIS |
| V-04 | Schema integrity | `validate_output.py` PASS |
| V-05 | Full batch | `_run_full_batch_test.py` completes without error |
| V-11 | DISCHO25 | PLAN=9DIS25 in quikplan |
| V-18 | Catalog sync | Governance = migration copy, 141 data rows |

### P0 — Protected issues (mandatory regression)

| ID | Validator | Issue |
|----|-----------|-------|
| V-06 | `tools/validators/validate_mpolicy_width.py` | #25 |
| V-07 | `tools/validators/validate_issue26_mprem.py` | #26 |
| V-08 | `tools/validators/validate_issue21m_quikmemo.py` | #21M |
| V-09 | `tools/validators/validate_issue21m_dbf_packaging.py` | #21M-FU |

### P1 — Phase 2 / downstream

| ID | Objective |
|----|-----------|
| V-12 | P3E trace — MPLAN on sample riders (960CWP, 94PDIS, 1CSIMN) |
| V-13 | quikridr MPLAN ∈ quikplan.PLAN referential integrity |
| V-14 | `variation_code_audit.csv` — review 33 plan keys |
| V-15 | `cso_mortality_crosswalk_qa.csv` — review missing plans |
| V-16 | Rate sample for changed PLAN codes (Risk sign-off) |

---

## Execution order

```
1. Verify v57.35 code + catalog (PreValidation Checklist)
2. Full batch re-run (_run_full_batch_test.py or app batch)
3. V-01, V-02, V-04, V-05 (Issue #28 core)
4. V-06 through V-09 (protected issues — ALL must PASS)
5. V-11, V-18, V-19 (DISCHO25 + catalog + P3C)
6. V-12, V-13 (P3E — default ON)
7. V-14, V-15, V-16 (downstream review)
8. Archive before/after evidence in Issue_Log_Items/Issue_28/evidence/
```

---

## Environment for batch

| Variable | v57.35 default | Notes |
|----------|----------------|-------|
| `QLA_CLOSED_MPLAN_AUTHORITY` | **1** (enabled) | Set `0` only to test Phase 1 without P3E |
| `QLA_ALLOW_LEGACY_MPLAN_FALLBACK` | 0 | Unchanged |
| `CROSSWALK_OVERLAY` | 0 | Unchanged |

---

## Regression constraints

* **Expected PLAN changes:** exactly the 33 mappings in `Issue_28_PLAN_Comparison_Report.md` plus DISCHO25 addition
* **Must NOT change:** unrelated PLAN mappings, quikclnt/quikclid/quikmemo behavior, MPOLICY width (#25), MPREM (#26)
* **Population reference:** `Issue_28_Policy_Impact_Summary.csv` — 219 policies / 239 PPBEN / 241 quikridr rows

---

## Protected issues

Regression compatibility **required** for:

* Issue #21M
* Issue #21M-FU
* Issue #21K
* Issue #25
* Issue #26

Do not modify their implementation during Validation unless a defect is proven and escalated.

---

## Open dependencies (not Validation blockers)

| ID | Item | Blocks |
|----|------|--------|
| B-02 | Re-UAT scope acceptance | Release / Production only |
| B-01 | Client crosswalk binding | Resolved per Dependency Gate update |

---

## Required validation deliverables

Create in `Issue_Log_Items/Issue_28/`:

```text
Issue_28_Validation_Report.md
Issue_28_Validation_Results.md
Issue_28_Before_After_Comparison.md
Issue_28_Regression_Results.md
Issue_28_Validation_Summary.md
```

Archive evidence:

```text
Issue_Log_Items/Issue_28/evidence/
```

---

## Fail actions

| Fail type | Action |
|-----------|--------|
| Protected issue validator FAIL | STOP — escalate; do not proceed to UAT |
| Issue #28 validator unexpected drift | STOP — compare against 33-row transition table |
| P3E UNAUTHORIZED on remediated PLAN_CODEs | Investigate resolver refresh + catalog |
| Schema / row-count regression | STOP — consult Rollback Checklist |

---

## Explicit stop conditions

Stop Validation Agent after:

* Full batch re-run on v57.35
* All P0 validators executed with documented results
* Validation deliverables created
* Validation Agent handoff prompt generated (for Regression Agent if PASS)

Do **not** proceed to:

* Client UAT Agent (unless Validation PASS + explicit instruction)
* Closure Agent
* Release Integration Agent

---

## Mandatory handoff (Validation → Regression)

At conclusion of Validation, generate a **Cursor-ready prompt** for the **Regression & Deployment Agent** in `Issue_28_Validation_Report.md` under heading `# Cursor Prompt — Regression Agent`. Assume the next AI has no prior conversation history.

---

## Quick reference — client examples

| LifePRO Coverage_ID | v57.34 quikplan.PLAN | Expected v57.35 PLAN |
|---------------------|----------------------|----------------------|
| 10827 MN5K | 10827 MN5K | **1CSIMN** |
| 0823 960CH | 0823 960CH | **960CWP** |
| 0824 P DIS | 0824 P DIS | **94PDIS** |
| DISCHO25 | (missing) | **9DIS25** |

---

## Code paths to verify post-batch

```
load_product_catalog_crosswalk()  → crosswalk_ql_plan_code authority
load_crosswalk_authority()        → product_plan_map for quikplan PLAN
convert_quikplan_to_output()      → PLAN field emit
_init_mplan_authority()           → post-quikplan refresh + quikridr MPLAN
write_p3e_governance_outputs()    → P3E trace artifacts
```

**Catalog path (runtime default):** `plan_governance/product_catalog_crosswalk.csv`

**Output path:** `QLA_Migration/Output/quikplan.csv`, `quikridr.csv`

**Begin Validation now.**
