# Issue #28 — Regression Impact Analysis

**Engine version:** v57.34  
**Planning date:** 2026-06-24

---

## Scope of change

| Category | Rows affected | Fields affected |
|----------|---------------|-----------------|
| quikplan PLAN remapping | 33 (`CROSSWALK_DIVERGENT`) | `PLAN` |
| quikplan catalog completeness | 1 (`DISCHO25`) | New plan row |
| quikplan unchanged | 108 (`STABLE_EMIT`) | — |
| quikridr MPLAN (Phase 2) | Subset of riders on 33 plans | `MPLAN` |

---

## Output table impact

| Table | Expected delta | Mechanism |
|-------|----------------|-----------|
| **quikplan** | 33 PLAN values change; possibly +1 row (DISCHO25) | Catalog authority promotion |
| **quikridr** | MPLAN changes for riders referencing 33 LifePRO PLAN_CODEs (Phase 2 P3E) | P3E resolver after quikplan universe update |
| **quikmstr** | None | No PLAN field mapping change |
| **quikclnt / quikclid** | None | Policy crosswalk unchanged |
| **quikmemo** | None | #21M path independent |
| **quikactg** | Potential MPLAN alignment (Phase 2) | Accounting extract PLAN references |

---

## Protected issue regression matrix

| Issue | Validator / check | Pre-fix baseline | Expected post-fix | Regression risk |
|-------|-------------------|------------------|-------------------|-----------------|
| **#25 MPOLICY** | MPOLICY width = 10 | PASS (279,222 values) | PASS | **Low** — no MPOLICY logic change |
| **#26 MPREM** | quikridr.MPREM populated | PASS (7,002 rows) | PASS | **Low** — MPREM rulebook unchanged |
| **#21M** | QUIKMEMO row count / MEMOKEY | PASS | PASS | **Low** |
| **#21M-FU** | One row per MEMOKEY | PASS | PASS | **Low** |
| **#21K** | MUNIT width (environment) | Env-dependent | Unchanged | **None** for #28 |

---

## Downstream enrichment impact

| Enrichment | Keyed on PLAN? | 33-plan change impact |
|------------|----------------|----------------------|
| Rate variation flags (R7B) | Yes | Re-run; verify PLANVALOPT |
| CSO mortality crosswalk | Yes | Review `cso_mortality_crosswalk_qa.csv` missing plans |
| Variation classification audit | Yes | Re-generate `variation_code_audit.csv` |
| PAAGERAT / premium rates | Yes | **Highest risk** — phase_r3 flagged PLAN_NOT_IN_TARGET |
| P3C closed authority diagnostics | Yes | Should **improve** (fewer unauthorized) |
| P3E MPLAN traces | Yes | Phase 2 required for rider alignment |

---

## Before / after — client examples

| LifePRO ID | v57.34 PLAN | Target PLAN | quikridr MPLAN (default today) | MPLAN after A+P3E |
|------------|-------------|-------------|-------------------------------|-------------------|
| 10827 MN5K | 10827 MN5K | 1CSIMN | 10827 MN5K (if present) | 1CSIMN |
| 0823 960CH | 0823 960CH | 960CWP | 0823 960CH | 960CWP |
| 0824 P DIS | 0824 P DIS | 94PDIS | 0824 P DIS | 94PDIS |

---

## Batch metrics — expected movement

| Metric | Before | After Option A |
|--------|--------|----------------|
| Crosswalk exact matches (runtime) | 108 / 141 | **141 / 141** (excl. DISCHO25 completeness) |
| quikplan unique PLAN | 139 | ~139–140 (passthrough IDs replaced by codes) |
| quikplan rows with spaces in PLAN | Present (passthrough) | **Reduced** — authoritative codes space-free |
| P3C unauthorized emit (33 rows) | Present | **Cleared** |

---

## Option-specific regression comparison

| Regression area | Option A | Option B | Option C | Option D |
|-----------------|----------|----------|----------|----------|
| quikplan PLAN | Fixed | Fixed (if flag on) | Fixed | Mode-dependent |
| quikridr MPLAN | Needs Phase 2 | Needs Phase 2 | Needs Phase 2 | Needs Phase 2 |
| Env/config drift | Low | **High** | Low | **High** |
| Catalog regen overwrite | Low | Medium | **High** | Medium |
| Code surface | Small | Small (defaults) | None | Medium |
| Test matrix size | Small | Medium (flag on/off) | Small | Large |

---

## Required regression test suite (Development phase)

### Mandatory (must PASS)

1. `_validate_issue25_mpolicy.py` (or equivalent MPOLICY width check)
2. `_validate_issue26_mprem.py`
3. `_validate_issue21m.py` / 21M-FU memo merge check
4. **New:** `_validate_issue28_plan_mapping.py` — 141 crosswalk rows vs quikplan PLAN
5. Full batch `_run_full_batch_test.py`
6. `Issue_28_Mapping_Differences.csv` regenerated — 0 mismatches

### Recommended

7. CSO crosswalk QA output review
8. Variation audit diff (33 plans)
9. Sample rate reconciliation for changed PLAN codes
10. P3E MPLAN trace sample (Phase 2) on policies with 0823/0824/10827 riders

### Out of scope (unless client expands)

- FORM column alignment to crosswalk form numbers
- Master_Crosswalk product row additions for passthrough IDs

---

## Rollback regression

| Rollback action | Restores v57.34 behavior? |
|-----------------|---------------------------|
| Revert `load_product_catalog_crosswalk()` change | **Yes** — immediate |
| Revert catalog CSV only (Option C rollback) | **Yes** if no code deployed |
| Disable overlay (Option B) | **Yes** |
| Set PLAN_MAPPING_MODE=compatibility (Option D) | **Yes** |

Compat column `ql_plan_code` preserved under Option A enables diff-based rollback verification.
