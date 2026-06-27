# Issue #28 — Dependency Gate Report

**Issue:** #28 — Incorrect Plan Number Mapping  
**Gate date:** 2026-06-24  
**Baseline version:** v57.34  
**Target version:** v57.35 (proposed)  
**Gate stage:** Dependency Gate (Stage 2.5)  
**Mode:** Read-only — no code, catalog, rulebook, or crosswalk modifications

---

## 1. Executive summary

The Dependency Gate evaluated whether Issue #28 remediation (Option A Phase 1 + Phase 0 DISCHO25 + optional Phase 2 P3E) has sufficient dependencies controlled to proceed in the AI Issue Resolution Framework.

**Gate decision: CONDITIONAL PASS**

Planning's predicted **CONDITIONAL PASS** is **confirmed**. Internal/technical dependencies are **satisfied**. Two **client-owned dependencies remain Missing** and block Development (G2) and Release/Production respectively.

| Category | Status |
|----------|--------|
| Crosswalk file & catalog data in repo | **Ready** |
| Runtime code path understood | **Ready** |
| Validation/regression plan | **Ready** |
| Client binding confirmation (5/22/2026) | **Missing** |
| Client re-UAT scope acceptance | **Missing** |
| DISCHO25 catalog row | **Missing** (internal Phase 0) |

**Next stage:** Ownership Decision Agent (may proceed).  
**Development:** Blocked until blocker **B-01** cleared.  
**Release/Production:** Blocked until **B-01** and **B-02** cleared.

---

## 2. Scope of gate review

Reviewed all Issue #28 Intake and Planning artifacts per user manifest, plus:

- `AI_Agents/Dependency_Gate.md`
- `plan_governance/product_catalog_crosswalk.csv` (live verification)
- `qla_core/product_catalog_authority.py` (caller chain)
- `QLA_Migration/Source/` inventory
- Existing validator scripts under `tools/validators/`

Did **not** repeat Intake or Planning analysis.

---

## 3. Dependency domain assessments

### 3.1 Crosswalk authority

| Question | Finding |
|----------|---------|
| Is 5/22/2026 crosswalk in repo? | **Yes** — 141 rows (`Policy Form Crosswalk 5.22.26.xlsx`) |
| Is it ingested into catalog? | **Yes** — `crosswalk_ql_plan_code` on 140/141 IDs |
| Is it binding by client **in writing**? | **No artifact in repo** — issue statement treats it as authoritative; formal sign-off **Missing (B-01)** |

**Dependency:** Client confirmation required before Development.

### 3.2 Product catalog

Gate verification (2026-06-24):

| Metric | Value |
|--------|------:|
| Catalog rows | 140 |
| `crosswalk_ql_plan_code` column | Present |
| Blank authoritative values | 0 |
| Duplicate Coverage_IDs | 0 |
| CROSSWALK_DIVERGENT rows | 33 |
| Divergent catalog vs xlsx mismatches | 0 |
| xlsx IDs missing from catalog | 1 (`DISCHO25`) |

**Verdict:** Catalog **can safely become authoritative** via Option A once `load_product_catalog_crosswalk()` reads `crosswalk_ql_plan_code`. Fallback to `ql_plan_code` when blank is understood.

### 3.3 Runtime code path

**Primary function:**

```text
qla_core/product_catalog_authority.py
  load_product_catalog_crosswalk()  → dict[lifepro_coverage_id → PLAN]
  load_crosswalk_authority()        → merges catalog into product_plan_map
```

**Callers affecting batch conversion:**

| Consumer | Impact of Option A |
|----------|-------------------|
| `app.py` quikplan batch (`convert_quikplan_to_output`) | **PLAN emit changes** (33 rows) |
| `qla_core/quikplan_converter.py` | Uses `crosswalk_authority.product_plan_map` |
| `app.py` `_init_mplan_authority` / P3E | Indirect — benefits after quikplan emits authoritative PLAN |
| `quikridr` default MPLAN (`cw_map`) | **Unchanged in Phase 1** — Phase 2 P3E |
| P3C `load_closed_product_catalog()` | Already uses `crosswalk_ql_plan_code` — **aligned by Option A** |
| Diagnostics / phase runners | Read same authority — consistent post-fix |

**Verdict:** Code dependency **fully mapped**. Phase 1 scope is surgical.

### 3.4 DISCHO25

| Finding | Evidence |
|---------|----------|
| Separate from DISCHO247C | Distinct xlsx rows: `9DIS25` vs `9DS24C` |
| Active product | quikplan_source row 105; PPBEN traces |
| Catalog gap | Only xlsx ID missing from catalog |
| quikplan output gap | Neither DISCHO25 nor 9DIS25 in v57.34 quikplan.csv |

**Package decision:** **Same remediation package (Phase 0)** — not a separate issue. Reason: single catalog completeness gap blocking 141/141 crosswalk coverage; small additive row; same release v57.35.

### 3.5 Validation dependencies

See `Issue_28_Validation_Dependencies.md`. Existing protected validators confirmed. Issue #28 validator **pending Development** — does not block Ownership/Risk stages.

### 3.6 Regression dependencies

v57.34 regression evidence exists for #25, #26, #21M, #21M-FU. Post-fix batch must re-run all protected validators. New PLAN baseline required for #28 — **expected**, not a blocker.

### 3.7 UAT dependencies

See `Issue_28_UAT_Dependencies.md`.

| Timing | Required? |
|--------|-----------|
| Before Development | Client binding (B-01) — **YES** |
| Before Release | Re-UAT scope acceptance (B-02) — **YES** |
| Before Production | Client UAT PASS — **YES** |

### 3.8 Release dependencies

See `Issue_28_Release_Dependencies.md`. v57.35 is appropriate. Release artifact list drafted.

### 3.9 Governance

AGENTS.md surgical rules satisfied by Option A. Protected issues untouched in plan.

---

## 4. Specific dependency questions — answers

### Q1 — Crosswalk binding authority

**Partially established.** Client issue text and Intake designate Policy Form Crosswalk 5/22/2026 as authoritative. **Written client confirmation for all 33 PLAN changes is Missing (B-01).** Required before Development.

### Q2 — Product catalog readiness

**Yes**, with Phase 0 add for DISCHO25. Column populated; 33 divergent mappings verified against xlsx; no duplicates; blank handling documented.

### Q3 — Runtime code path

**Confirmed** — `load_product_catalog_crosswalk()` in `product_catalog_authority.py`. Affects **quikplan PLAN** directly; **quikridr MPLAN** via Phase 2 P3E only; aligns **P3C**; enables **P3E** after quikplan fix.

### Q4 — DISCHO25

**Requires catalog remediation** in **same package** (Phase 0). **Not** an alias of DISCHO247C.

### Q5 — Validation dependencies

Documented in `Issue_28_Validation_Dependencies.md` — 28 primary + protected issue suite.

### Q6 — Regression dependencies

Current v57.34 baselines **sufficient for before-state**. New baselines **required after fix** — planned, not blocking gate.

### Q7 — UAT dependencies

33 PLAN changes require client re-UAT. **Before Development:** binding only. **Before Release/Production:** explicit acceptance + UAT PASS. **Not assumed.**

### Q8 — Release as v57.35

**Yes**, with documented artifacts and blocker clearance sequence.

---

## 5. Protected prior issues

| Issue | Gate impact |
|-------|-------------|
| #21M | No dependency blocker; validator re-run required post-fix |
| #21M-FU | Same |
| #21K | Env-dependent validator; no #28 code overlap |
| #25 | MPOLICY validator mandatory regression |
| #26 | MPREM validator mandatory regression |

Plan preserves all protected paths. Regression must remain PASS.

---

## 6. Gate decision

```text
CONDITIONAL PASS
```

### Conditions

| ID | Condition | Clears stage |
|----|-----------|--------------|
| C-01 | Client written confirmation: 5/22/2026 crosswalk binding for 33 PLAN changes (**B-01**) | **Development** |
| C-02 | Client written acceptance of re-UAT scope (**B-02**) | **Release / Production** |
| C-03 | Phase 0: DISCHO25 catalog row added | Full 141/141 alignment |
| C-04 | Catalog migration copy synced (133→140) | **Production deploy** |
| C-05 | V-28-01 validator implemented | **Validation (G4)** |

### What may proceed now

- Ownership Decision Agent  
- Risk Agent (per Framework, after Ownership)

### What may NOT proceed

- Development Phase 1 (code) until **C-01**  
- Release / Production until **C-01** + **C-02** + validation PASS

---

## 7. Recommended issue status

**Active — Conditional Gate Pass**

Sub-status: **Awaiting Client Clarification** (B-01, B-02) | **Ready for Ownership Decision + Risk Review** (internal)

---

## 8. Deliverables index

| File | Purpose |
|------|---------|
| `Issue_28_Dependency_Gate_Report.md` | This report |
| `Issue_28_Dependency_Checklist.md` | Full checklist Met/Missing/N/A |
| `Issue_28_Blockers_And_Assumptions.md` | Blockers B-01–B-05, assumptions |
| `Issue_28_Validation_Dependencies.md` | Post-dev validation map |
| `Issue_28_UAT_Dependencies.md` | Client UAT timing |
| `Issue_28_Release_Dependencies.md` | v57.35 release artifacts |

---

## 9. Revision of Planning prediction

Planning predicted **CONDITIONAL PASS** pending client crosswalk binding and re-UAT acceptance.

**Gate confirms** that prediction. No contradictory evidence found. Internal dependencies exceed Planning preview (catalog/xlsx alignment verified to 0 divergent mismatches).

---

# Cursor Prompt — Ownership Decision Agent

```markdown
# Cursor Prompt — Issue #28 Ownership Decision Agent

You are continuing work on the **LifePRO → QLAdmin Conversion Project**.

**Baseline converter version:** v57.34  
**Target remediation version:** v57.35 (proposed)  
**Issue:** #28 — Incorrect Plan Number Mapping

Perform **ONLY the Ownership Decision Agent stage** for Issue #28.

Do **NOT** repeat Intake, Planning, or Dependency Gate analysis.  
Do **NOT** perform Development, Validation, or modify code, rulebooks, product catalogs, crosswalks, or converter logic.

---

## Current project status

| Stage | Status |
|-------|--------|
| Intake | **Complete** |
| Planning | **Complete** — Option A Phase 1 recommended |
| Dependency Gate | **Complete** — **CONDITIONAL PASS** |
| Ownership Decision | **YOU ARE HERE** |
| Risk Agent | Not started |
| Development | **Blocked** until client blocker B-01 cleared |

---

## Summary of completed work

### Intake (proven facts)

- Client issue valid: 33/141 plan mappings wrong vs Policy Form Crosswalk 5/22/2026.
- Runtime reads `ql_plan_code` (compat); authoritative values in `crosswalk_ql_plan_code`.
- All 33 mismatches are `CROSSWALK_DIVERGENT`. Client examples traced (10827 MN5K→1CSIMN, 0823 960CH→960CWP, 0824 P DIS→94PDIS).
- `CROSSWALK_OVERLAY=0` by default. No code changed during Intake.

### Planning (decisions)

- **Recommended:** Option A Phase 1 — promote `crosswalk_ql_plan_code` in `load_product_catalog_crosswalk()` (`qla_core/product_catalog_authority.py`).
- **Phase 0:** Add missing `DISCHO25` catalog row (NOT alias of DISCHO247C).
- **Phase 2 (optional):** P3E MPLAN alignment after quikplan validates.
- Protected issues #21M, #21M-FU, #21K, #25, #26 — no planned code path changes.

### Dependency Gate (this stage)

- **Decision: CONDITIONAL PASS**
- **Internal dependencies:** Met (crosswalk in repo, catalog column verified, runtime path mapped, validators identified).
- **Missing blockers:**
  - **B-01:** Client written confirmation 5/22/2026 crosswalk is binding for 33 PLAN changes — **blocks Development**
  - **B-02:** Client written re-UAT scope acceptance — **blocks Release/Production**
  - **B-03:** DISCHO25 catalog row (internal Phase 0)
  - **B-05:** Sync `QLA_Migration/Mapping/product_catalog_crosswalk.csv` (133 vs 140 rows)

---

## Ownership Decision objectives

Formalize **who owns what** for Issue #28 remediation across:

1. **Code ownership** — which module/function/file owns the fix
2. **Data ownership** — catalog CSV, DISCHO25 row, catalog sync
3. **Business authority ownership** — client crosswalk binding
4. **Validation ownership** — who runs/produces evidence
5. **UAT ownership** — client vs internal
6. **Release ownership** — version bump, release notes, rollback
7. **Phase ownership** — Phase 0 / 1 / 2 responsibilities and sequencing
8. **Protected issue ownership** — regression evidence for #21M, #21M-FU, #21K, #25, #26

Produce explicit ownership assignments with rationale and handoff boundaries.

---

## Required files to review

Read under `Issue_Log_Items/Issue_28/`:

**Intake:**
- Issue_28_Intake_Report.md
- Issue_28_Mapping_Inventory.md
- Issue_28_Runtime_Mapping_Flow.md
- Issue_28_Crosswalk_Inventory.csv
- Issue_28_Mapping_Differences.csv
- Issue_28_Trace_Samples.md
- Issue_28_Population_Summary.md

**Planning:**
- Issue_28_Planning_Report.md
- Issue_28_Solution_Options.md
- Issue_28_Risk_Assessment.md
- Issue_28_Regression_Impact.md
- Issue_28_Decision_Matrix.md
- Issue_28_Implementation_Strategy.md
- Issue_28_DISCHO25_Investigation.md

**Dependency Gate:**
- Issue_28_Dependency_Gate_Report.md
- Issue_28_Dependency_Checklist.md
- Issue_28_Blockers_And_Assumptions.md
- Issue_28_Validation_Dependencies.md
- Issue_28_UAT_Dependencies.md
- Issue_28_Release_Dependencies.md

Also review:
- `qla_core/product_catalog_authority.py` (read-only)
- `AI_Agents/Framework.md` (governance)
- `AGENTS.md` (enterprise rules)

---

## Required deliverables

Create under `Issue_Log_Items/Issue_28/`:

```text
Issue_28_Ownership_Decision_Report.md
Issue_28_Ownership_Matrix.md
Issue_28_Phase_Ownership.md
Issue_28_Handoff_To_Risk.md
```

Additional artifacts optional if they improve traceability.

---

## Ownership Decision report must include

1. Executive summary of ownership assignments
2. Primary fix ownership (Option A code vs catalog data)
3. Client vs internal ownership for B-01 and B-02
4. DISCHO25 ownership (same package vs split — Gate decided: **same package**)
5. Phase 0 / 1 / 2 owner and sequencing authority
6. Validation evidence ownership
7. UAT ownership (client actions vs internal actions)
8. Release artifact ownership
9. Protected issue regression ownership
10. Escalation path if client blockers persist
11. Recommendation for Risk Agent scope

---

## Repository constraints

- Surgical edits only (AGENTS.md) — Ownership stage is **read-only**
- Do not modify Issues #21M, #21M-FU, #21K, #25, #26 artifacts or code
- Preserve QLA formatting and QuikPlan schema integrity in all future work
- Version bump to v57.35 only when Development modifies app.py

---

## Regression constraints

Post-remediation, these must PASS (ownership must assign who verifies):

- `validate_mpolicy_width.py` (#25)
- `validate_issue26_mprem.py` (#26)
- `validate_issue21m_quikmemo.py` (#21M)
- `validate_issue21m_dbf_packaging.py` (#21M-FU)
- `validate_issue21k_munit.py` (#21K, env-dependent)
- `_validate_issue28_plan_mapping.py` (to be created in Development)

---

## Stop condition

Stop after Ownership Decision deliverables are complete.

Do **NOT** proceed to:
- Risk Agent (unless your report ends with handoff prompt only — do not execute Risk)
- Development (blocked on B-01)
- Validation, Regression, Closure, or Release Integration

---

## Mandatory handoff

At the end of `Issue_28_Ownership_Decision_Report.md`, include a complete **Cursor-ready prompt for the Risk Agent** under:

```text
# Cursor Prompt — Risk Agent
```

The Risk Agent prompt must assume **no prior conversation history** and include all context needed to quantify impact for Option A + Phase 0 + optional Phase 2, protected issue regression scope, rate/CSO/variation impact, and go/no-go criteria — referencing Dependency Gate CONDITIONAL PASS and remaining blockers B-01/B-02.
```

---

*Dependency Gate complete. No code modified.*
