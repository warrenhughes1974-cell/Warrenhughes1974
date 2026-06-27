# Issue #28 — Planning Report

**Status:** Planning Complete  
**Priority:** No-Go until remediation implemented and validated  
**Engine version:** v57.34 (baseline) → v57.35 (proposed)  
**Planning date:** 2026-06-24  
**Mode:** Planning only — no code modifications

---

## 1. Executive Summary

Issue #28 is **confirmed** and **fully characterized**. Intake proved 33 of 141 plan mappings emit compatibility passthrough values instead of the client-approved Policy Form Crosswalk (5.22.2026). Planning evaluated four remediation options plus a phased hybrid.

**Recommended approach:** **Option A — promote `crosswalk_ql_plan_code` in `load_product_catalog_crosswalk()`** (Phase 1), followed by **P3E MPLAN alignment** (Phase 2). Add missing **`DISCHO25`** catalog row (Phase 0).

This is an **authority promotion** fix — surgical, aligned with existing P3C architecture, and reversible via compat column retention.

| Decision | Selection |
|----------|-----------|
| Primary option | **A** (score 4.70 / 5.0) |
| Full remediation | **E = A + P3E Phase 2** (score 4.45) |
| Not recommended | B (overlay default), D (feature flag) |
| Fallback | C (catalog data-only) if code change blocked |

---

## 2. Scope

### In scope (Development phase)

- Runtime PLAN authority promotion for 33 `CROSSWALK_DIVERGENT` rows
- DISCHO25 catalog completeness
- Validation tooling and before/after evidence
- Phase 2 quikridr MPLAN alignment (recommended same release)

### Out of scope (unless client expands)

- FORM column alignment to crosswalk form numbers
- Master_Crosswalk product row additions
- Rate table content updates (validate only; separate ownership if gaps found)

### Protected issues

#21M, #21M-FU, #21K, #25, #26 — **no code path changes required**; mandatory regression validators.

---

## 3. Intake findings accepted (not re-investigated)

| Finding | Status |
|---------|--------|
| 33/141 runtime mismatches | Accepted |
| All mismatches = `CROSSWALK_DIVERGENT` | Accepted |
| Runtime reads `ql_plan_code` not `crosswalk_ql_plan_code` | Accepted |
| Overlay disabled by default | Accepted |
| Client 3 examples verified | Accepted |

Full detail: `Issue_28_Intake_Report.md`

---

## 4. Option evaluation summary

See **`Issue_28_Solution_Options.md`**

| Option | Verdict |
|--------|---------|
| **A** — Promote authoritative column in loader | **Recommended** |
| **B** — Overlay default ON | Reject — incomplete, dual-path, scaffold |
| **C** — Catalog CSV data promotion | Acceptable fallback |
| **D** — PLAN_MAPPING_MODE flag | Reject — unnecessary complexity |
| **E** — A + P3E Phase 2 | **Recommended full path** |

---

## 5. DISCHO25 resolution

See **`Issue_28_DISCHO25_Investigation.md`**

| Question | Answer |
|----------|--------|
| Does DISCHO25 map to DISCHO247C? | **NO** — distinct products (`9DIS25` vs `9DS24C`) |
| Data defect? | **Catalog gap** — row missing; quikplan output missing plan |
| Obsolete? | **NO** — active in source and PPBEN |
| Remediation | Add catalog row; include in completeness validation |

Intake hypothesis **rejected with evidence**.

---

## 6. Risk assessment summary

See **`Issue_28_Risk_Assessment.md`**

| Top risks | Mitigation |
|-----------|------------|
| Rate lookup breaks on 33 PLAN changes | Rate sample validation |
| Client UAT baseline invalid | Expected — re-UAT documented |
| P3E before quikplan fix | Enforce Phase 1 → Phase 2 sequence |
| Catalog regen overwrites (Option C) | Prefer Option A |

Protected issues: **low regression risk** (validation-only).

---

## 7. Regression impact summary

See **`Issue_28_Regression_Impact.md`**

- **quikplan:** 33 PLAN values change (intended)
- **quikridr:** MPLAN changes in Phase 2
- **#25, #26, #21M, #21M-FU:** No logic change; re-run validators
- **#21K:** No impact

---

## 8. Decision matrix

See **`Issue_28_Decision_Matrix.md`**

**Rank 1:** Option A (4.70)  
**Rank 2:** Option E (4.45)

---

## 9. Implementation strategy summary

See **`Issue_28_Implementation_Strategy.md`**

| Phase | Deliverable |
|-------|-------------|
| 0 | DISCHO25 catalog row + sync migration copy |
| 1 | `load_product_catalog_crosswalk()` authority promotion → v57.35 |
| 2 | Enable P3E for quikridr MPLAN alignment |
| 3 | Optional governance status updates |

---

## 10. Open questions (for Dependency Gate)

| # | Question | Owner | Blocks? |
|---|----------|-------|---------|
| Q1 | Client confirms Policy Form Crosswalk 5.22.2026 is **binding** for all 33 PLAN code changes | Client | **Yes** |
| Q2 | Client accepts re-UAT scope for product catalog review | Client | **Yes** |
| Q3 | Phase 2 P3E enablement approved for same release? | Client/Tech | Recommended |
| Q4 | FORM column changes explicitly out of scope? | Client | Recommended |
| Q5 | Rate team review needed for 33 PLAN code changes? | Internal | Soft blocker |

---

## 11. Dependency Gate preview

| Check | Status |
|-------|--------|
| Crosswalk xlsx in repo | **Met** |
| Intake + Planning complete | **Met** |
| Example policies / evidence | **Met** (3 client examples + 33-row population) |
| QLAdmin PLAN field target | **Met** (quikplan.PLAN) |
| Client binding confirmation on 33 changes | **Missing** — required |
| Re-UAT acceptance | **Missing** — required |
| Protected issue regression plan | **Met** |

**Predicted gate status:** **CONDITIONAL PASS** pending Q1–Q2 client confirmation.

---

## 12. Planning deliverables index

| File | Purpose |
|------|---------|
| `Issue_28_Planning_Report.md` | This report |
| `Issue_28_Solution_Options.md` | Options A–E analysis |
| `Issue_28_Risk_Assessment.md` | Risk register + protected issue matrix |
| `Issue_28_Regression_Impact.md` | Output/regression analysis |
| `Issue_28_Decision_Matrix.md` | Scored comparison + recommendation |
| `Issue_28_Implementation_Strategy.md` | Phased implementation plan |
| `Issue_28_DISCHO25_Investigation.md` | DISCHO25 conclusive analysis |

---

## 13. Recommendation for next stage

Proceed to **Dependency Gate** to obtain client confirmation on crosswalk binding authority and re-UAT scope. Upon PASS, advance to **Risk Agent** (rate impact) then **Development Agent** (Phase 0–1 minimum).

**Do not implement** until Dependency Gate clears Q1–Q2.

---

## Cursor-ready prompt for Dependency Gate

```
# Cursor Prompt — Issue #28 Dependency Gate

You are continuing work on the **LifePRO → QLAdmin Conversion Project**.

Current converter version: **v57.34** (baseline)
Proposed fix version: **v57.35**

Perform **ONLY the Dependency Gate stage** for **Issue #28**.
Do **NOT** write code. Do **NOT** repeat Intake or Planning analysis.

---

## Read first

1. `AI_Agents/Dependency_Gate.md`
2. `Issue_Log_Items/Issue_28/Issue_28_Planning_Report.md`
3. `Issue_Log_Items/Issue_28/Issue_28_Implementation_Strategy.md`
4. All Intake artifacts in `Issue_Log_Items/Issue_28/`

---

## Planning decisions (authoritative)

- **Recommended fix:** Option A — promote `crosswalk_ql_plan_code` in `load_product_catalog_crosswalk()`
- **Phase 2:** P3E MPLAN alignment after quikplan validated
- **Phase 0:** Add DISCHO25 catalog row (NOT an alias of DISCHO247C — proven)
- **33 PLAN values will change** in quikplan output — client re-UAT required
- **Protected issues #21M, #21M-FU, #21K, #25, #26** — no code path changes; validators must re-run

---

## Your tasks

1. Evaluate the Dependency Gate checklist from `AI_Agents/Dependency_Gate.md` against Issue #28.
2. Mark each item **Met**, **Missing**, or **N/A** with evidence.
3. Publish: `Issue_Log_Items/Issue_28/Issue_28_Dependency_Gate.md`
4. Set status: **PASS** or **FAIL**
5. If FAIL: list exact blockers, owner (Client / Internal), and requested action.
6. Update recommended issue status (Active / Blocked — Awaiting Client Clarification / etc.)

---

## Key dependency questions to resolve

| ID | Question | Required for PASS? |
|----|----------|-------------------|
| Q1 | Client confirms Policy Form Crosswalk 5.22.2026 is binding for all 33 PLAN code changes | YES |
| Q2 | Client accepts re-UAT scope for product catalog / plan review | YES |
| Q3 | Phase 2 P3E MPLAN enablement in same release — approved? | Recommended |
| Q4 | FORM column alignment explicitly out of scope for #28? | Recommended |
| Q5 | Rate team review for 33 PLAN changes — required? | Soft |

If client artifacts (email, issue log sign-off) are not in repo, mark Missing and FAIL with "Awaiting Client Clarification" unless Planning assumptions may proceed with documented waiver.

---

## Regression guards (must confirm Met in plan)

- [ ] Plan preserves Issue #25 MPOLICY padding
- [ ] Plan preserves Issue #26 MPREM mapping
- [ ] Plan does not alter unrelated rulebooks
- [ ] Plan does not modify Issue #21M / #21M-FU / #21K code paths

---

## Stop condition

Stop after publishing `Issue_28_Dependency_Gate.md`.
Do **NOT** proceed to Risk Agent or Development.

At end of gate document, include Cursor-ready prompt for **Risk Agent** if PASS, or hold instructions if FAIL.
```

---

*Planning stage complete. No code modified.*
