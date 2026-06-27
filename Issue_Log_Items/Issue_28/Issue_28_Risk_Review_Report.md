# Issue #28 — Risk Review Report

**Issue:** #28 — Incorrect Plan Number Mapping (Product Catalog Crosswalk Corrections)  
**Risk Agent date:** 2026-06-24  
**Baseline version:** v57.34  
**Proposed fix version:** v57.35  
**Mode:** Risk analysis only — no code, catalog, or crosswalk modifications

---

## 1. Risk summary

Issue #28 corrects **33 of 141** product catalog PLAN mappings to align with the client-confirmed **Policy Form Crosswalk (5/22/2026)**. The fix promotes authoritative `crosswalk_ql_plan_code` values at runtime (Option A Phase 1) plus a **DISCHO25** catalog row (Phase 0).

| Risk dimension | Level | Rationale |
|----------------|-------|-----------|
| Technical implementation | **Low** | Single-function surgical change; proven root cause |
| Product catalog integrity | **Low** | One-to-one mappings; no duplicates; column populated |
| Protected issue regression (#25/#26/#21M) | **Low** | Orthogonal code paths; mandatory re-validation |
| quikplan output delta | **Medium–High (intended)** | 33 PLAN values change — client approved (B-01) |
| quikridr MPLAN (Phase 1 only) | **Medium** | Unchanged until P3E — referential orphan persists |
| Rate / CSO downstream | **Medium** | Auth PLAN codes may lack rate table entries |
| Production deploy | **Medium** | Requires UAT (B-02) + rate spot-check |

### Overall recommendation

```text
CONDITIONAL GO
```

| Stage | Authorization |
|-------|---------------|
| **Development (Phase 0 + 1)** | **GO** — B-01 satisfied; bounded risk |
| **Development (Phase 2 P3E)** | **GO** — recommended same release; sequenced after Phase 1 validation |
| **Release / Production** | **CONDITIONAL** — requires B-02 client UAT acceptance + V-16 rate review |

**Not NO-GO:** Client has confirmed crosswalk authority. Remaining risks are quantified, mitigatable, and do not outweigh correcting 23.4% of product catalog PLAN codes that violate approved mappings.

---

## 2. Framework status update

| Stage | Status |
|-------|--------|
| Intake | Complete |
| Planning | Complete — Option A |
| Dependency Gate | Complete — CONDITIONAL PASS |
| Ownership Decision | Complete (per user) |
| **B-01 Client crosswalk binding** | **Complete** |
| B-02 Re-UAT scope acceptance | Open — blocks **Release/Production** only |
| **Risk Agent** | **Complete (this report)** |
| Development | **Authorized Phase 0+1**; not yet executed |

---

## 3. Population affected

See **`Issue_28_Population_Impact_Report.md`**

| Dimension | Count |
|-----------|------:|
| Plans corrected (catalog) | **33** (+ DISCHO25 add) |
| quikplan rows with PLAN change | **34** |
| Policies touching affected PLAN_CODEs (batch PPBEN) | **219** |
| PPBEN benefit rows affected | **239** |
| quikridr rows with compat MPLAN (Phase 2 scope) | **241** / **222 policies** |
| Unchanged STABLE_EMIT plans | 108 |
| Many-to-one mapping conflicts | **0** |

**Key insight:** Correction is **catalog-wide** for 33 products; in-force policy touch in the current batch is **~1.9%** of PPBEN benefits but **100%** of divergent product definitions.

---

## 4. Runtime impact

### 4.1 quikplan (Phase 1 — primary)

| Field | Impact |
|-------|--------|
| **PLAN** | **Changes** for 33 products — passthrough → authoritative QL Plan Code |
| FORM | Unchanged in Phase 1 (overlay not enabled) — **out of scope** unless client expands |
| DESCR / PLANNAME | Unchanged in Phase 1 |
| Enrichment (R7B, CSO) | **Indirect** — keyed on PLAN; re-audit required (V-14, V-15) |

**Loader path:** `load_product_catalog_crosswalk()` → `load_crosswalk_authority().product_plan_map` → `quikplan_converter._apply_crosswalk_value()`

### 4.2 quikridr (Phase 1 vs Phase 2)

| Mode | MPLAN impact |
|------|--------------|
| Phase 1 only | **No change** — still `Master_Crosswalk` passthrough for PLAN_CODE |
| Phase 2 (P3E ON) | **Changes** on up to 241 rows — authoritative MPLAN aligned to quikplan PLAN universe |

**Risk if Phase 2 deferred:** quikridr MPLAN remains passthrough (orphan vs quikplan) — **medium referential integrity risk**; mitigated by Phase 2 in same release.

### 4.3 Phase 1 / Phase 2 inheritance

| Mechanism | Impact |
|-----------|--------|
| MPHASE 1 base coverage | Base MPLAN inherits from PLAN mapping — Phase 2 only |
| **PUA inheritance** | 3 affected PUA products (`621 PUA`, `961 PUA`, `970 PUA`) — base MPLAN prefix drives PUA MPLAN; **validate after Phase 2** |
| P3C closed catalog | **Improves** — runtime aligns with `crosswalk_ql_plan_code` |
| P3E resolver | **Enabled** after quikplan emits auth PLAN set |
| Crosswalk overlay | **Not used** — no change to overlay path |
| Master_Crosswalk policy rows | **Unchanged** |

### 4.4 Other outputs

| Output | Affected? |
|--------|-----------|
| quikmstr | No direct PLAN field change |
| quikclnt / quikclid | No |
| quikmemo (#21M) | No |
| MPOLICY (#25) | No logic change |
| MPREM (#26) | No logic change |
| quikactg | Possible MPLAN references — Phase 2 |
| Claims pipelines | Low — MPLAN linkage if riders on affected plans |

---

## 5. Regression assessment

See **`Issue_28_Regression_Impact.md`** (Planning) + validation matrix.

| Protected issue | Code path overlap | Regression risk | Required check |
|-----------------|-------------------|-----------------|----------------|
| **#25** MPOLICY padding | None | **Low** | V-06 |
| **#26** MPREM | None | **Low** | V-07 |
| **#21M** QUIKMEMO | None | **Low** | V-08 |
| **#21M-FU** MEMOKEY merge | None | **Low** | V-09 |
| **#21K** MUNIT | None | **Low** (env) | V-10 |
| **P3C** governance | **Positive alignment** | Low | V-19 |
| **P3E** MPLAN | **Requires Phase 2** | Medium if skipped | V-12, V-13 |

**Conclusion:** Protected issues remain **unaffected at code level**. Regression risk is **validation discipline**, not architectural collision.

---

## 6. Data integrity

| Question | Answer |
|----------|--------|
| Will historical policies receive different PLAN values? | **Yes** — quikplan product catalog rows change; rider MPLAN changes in Phase 2 for in-batch policies on affected products |
| Do policies change insurance product identity? | **Semantically yes** — PLAN code aligns to QLAdmin product catalog client approved; not a different LifePRO benefit — **correction** |
| Duplicate PLAN values introduced? | **No** — 33 unique authoritative targets; one-to-one |
| Orphan mappings? | **Pre-fix:** 33 orphan compat MPLAN; **Post Phase 1:** quikplan orphans cleared; **Post Phase 2:** quikridr orphans cleared |
| Passthrough IDs with spaces removed? | **Yes** — improves QLAdmin schema compliance |

**DISCHO25:** Adding catalog row completes 141/141 coverage; does not alter the 33-mapping set.

---

## 7. Downstream risks (quantified)

| Risk ID | Description | Likelihood | Impact | Mitigation |
|---------|-------------|------------|--------|------------|
| R-RATE | Rate tables keyed on old/passthrough PLAN | Medium | Medium | V-16 sample; rate team review |
| R-CSO | CSO crosswalk missing auth PLAN | Medium | Low | V-15 QA CSV |
| R-VAR | Variation classification keyed on PLAN | Low | Low | V-14 audit diff |
| R-MPLAN | Phase 1 quikridr/quikplan MPLAN mismatch | **High (certain)** if P3E off | Medium | **Phase 2 mandatory for full fix** |
| R-PUA | PUA MPLAN inheritance after auth change | Low | Medium | Sample PUA policies in Phase 2 |
| R-UAT | Client rejects post-fix catalog | Low (B-01 received) | High | B-02 before production |
| R-CATALOG-SYNC | Migration copy 133 vs 140 rows | Medium | Low | Sync in Development (B-05) |

---

## 8. Validation requirements

See **`Issue_28_Validation_Matrix.md`**

**Minimum for Development closure:** V-01, V-02, V-04–V-09, V-11, V-18  
**Minimum for Production:** Above + V-03 (client UAT) + V-16 (rate) + Phase 2 V-12/V-13 if riders in scope

---

## 9. Rollback strategy

See **`Issue_28_Rollback_Checklist.md`**

- **Primary:** Git revert `product_catalog_authority.py` + version → v57.34
- **Catalog:** Compat column preserved; optional DISCHO25 row revert
- **Crosswalk xlsx:** No revert (client authority)
- **Recovery time:** Single batch re-run after code revert

---

## 10. Risk decision matrix

| Criterion | Assessment |
|-----------|------------|
| Client authority confirmed | **Yes (B-01)** |
| Root cause proven | **Yes** |
| Blast radius bounded | **Yes** — one function + optional catalog row |
| Rollback safe | **Yes** |
| Protected issues safe | **Yes** (with validators) |
| Unmitigated high risk | **Rate tables** — conditional on V-16 |
| UAT before production | **Required (B-02)** |

---

## 11. Conditions for full GO (production)

| # | Condition | Status |
|---|-----------|--------|
| C-1 | B-01 client crosswalk binding | **Met** |
| C-2 | Phase 0+1 Development + validation PASS | Pending |
| C-3 | Phase 2 P3E enabled and V-12/V-13 PASS | Recommended |
| C-4 | B-02 client re-UAT acceptance | **Open** |
| C-5 | Rate spot-check (V-16) | Pending |
| C-6 | Catalog copies synchronized | Pending (Development) |

---

## 12. Supporting artifacts

| File | Purpose |
|------|---------|
| `Issue_28_Population_Impact_Report.md` | Fleet/catalog quantification |
| `Issue_28_PLAN_Comparison_Report.md` | 33 transition table |
| `Issue_28_Policy_Impact_Summary.csv` | Per-product PPBEN/quikridr counts |
| `_risk_affected_plans.csv` | Machine-readable affected list |
| `Issue_28_Validation_Matrix.md` | Post-dev validation |
| `Issue_28_Rollback_Checklist.md` | Rollback procedure |

---

## 13. Recommendation summary

| Decision | Value |
|----------|-------|
| **Risk recommendation** | **CONDITIONAL GO** |
| Development Phase 0 + 1 | **Approved to proceed** |
| Development Phase 2 (P3E) | **Strongly recommended** in v57.35 |
| Production release | **Hold** until C-4, C-5 satisfied |
| Issue status | **Ready for Development** |

---

# Cursor Prompt — Development Agent

```markdown
# Cursor Prompt — Issue #28 Development Agent

You are continuing work on the **LifePRO → QLAdmin Conversion Project**.

**Baseline version:** v57.34  
**Target version:** v57.35  
**Issue:** #28 — Incorrect Plan Number Mapping (Product Catalog Crosswalk Corrections)

Perform **ONLY the Development Agent stage** for Issue #28.

Do **NOT** repeat Intake, Planning, Dependency Gate, Ownership Decision, or Risk analysis.

---

## Framework status (authoritative)

| Stage | Status |
|-------|--------|
| Intake | Complete — 33/141 PLAN mismatches proven |
| Planning | Complete — **Option A Phase 1** recommended |
| Dependency Gate | CONDITIONAL PASS |
| Ownership Decision | Complete |
| Risk Agent | **CONDITIONAL GO** — Development **authorized** |
| Client B-01 (crosswalk binding) | **Complete** |
| Client B-02 (re-UAT before production) | Open — does not block Development |

---

## Risk Agent findings (must honor)

1. **33 quikplan PLAN values** change from compat passthrough → authoritative crosswalk codes.
2. **219 policies** / **239 PPBEN rows** / **241 quikridr rows** touch affected products in current batch.
3. **Phase 1** fixes quikplan only; **Phase 2 P3E** strongly recommended for quikridr MPLAN (241 rows / 222 policies).
4. **DISCHO25** catalog row required (Phase 0) — separate from DISCHO247C.
5. Protected issues **#21M, #21M-FU, #21K, #25, #26** — do not modify their code paths.
6. Rate/CSO downstream review required before production (not blocking dev).

---

## Approved implementation (Option A)

### Phase 0 — Catalog completeness

1. Add `DISCHO25` row to `plan_governance/product_catalog_crosswalk.csv` from xlsx (`9DIS25`).
2. Sync `QLA_Migration/Mapping/product_catalog_crosswalk.csv` to match governance (140→141 rows).

### Phase 1 — Runtime authority (primary)

**File:** `qla_core/product_catalog_authority.py`  
**Function:** `load_product_catalog_crosswalk()`

Change column precedence:
- Use `crosswalk_ql_plan_code` when non-blank
- Fall back to `ql_plan_code`
- Preserve existing normalize/strip behavior
- **Do not remove** compat column

**Version bump:** `app.py` and `QLA_Migration/app.py` → **v57.35**

### Phase 2 — P3E MPLAN alignment (recommended same release)

After Phase 1 validates:
- Enable/document `QLA_CLOSED_MPLAN_AUTHORITY=1` for batch
- Verify quikridr MPLAN resolves to authoritative PLAN for sample riders (0823 960CH→960CWP, 0824 P DIS→94PDIS, 10827 MN5K→1CSIMN)
- Validate PUA products: 621 PUA, 961 PUA, 970 PUA

---

## Files to modify (expected)

| File | Change |
|------|--------|
| `qla_core/product_catalog_authority.py` | Authority column precedence (~15–25 lines) |
| `app.py` | Version v57.35 |
| `QLA_Migration/app.py` | Version v57.35 |
| `plan_governance/product_catalog_crosswalk.csv` | DISCHO25 row |
| `QLA_Migration/Mapping/product_catalog_crosswalk.csv` | Full sync |
| `tools/validators/_validate_issue28_plan_mapping.py` | **Create** — 141 crosswalk vs quikplan PLAN |

## Files NOT to modify

- `Sync_Rulebook_quikplan.csv` / `Sync_Rulebook_quikridr.csv` (unless Risk explicitly required — default: no)
- `Master_Crosswalk.csv`
- Issue #21M / #21M-FU / #21K / #25 / #26 logic in `app.py`
- Policy Form Crosswalk xlsx

---

## Required files to read first

```
Issue_Log_Items/Issue_28/Issue_28_Risk_Review_Report.md
Issue_Log_Items/Issue_28/Issue_28_Implementation_Strategy.md
Issue_Log_Items/Issue_28/Issue_28_PLAN_Comparison_Report.md
Issue_Log_Items/Issue_28/Issue_28_Validation_Matrix.md
Issue_Log_Items/Issue_28/Issue_28_Rollback_Checklist.md
Issue_Log_Items/Issue_28/Issue_28_Mapping_Differences.csv
qla_core/product_catalog_authority.py
AGENTS.md
```

---

## Validation after Development (mandatory)

Run in order:

1. Full batch: `QLA_Migration/_run_full_batch_test.py`
2. `_validate_issue28_plan_mapping.py` → **0 mismatches**
3. Re-run `Issue_Log_Items/Issue_28/_issue28_intake_analysis.py`
4. `validate_mpolicy_width.py` (#25)
5. `validate_issue26_mprem.py` (#26)
6. `validate_issue21m_quikmemo.py` (#21M)
7. `validate_issue21m_dbf_packaging.py` (#21M-FU)

Save evidence to `Issue_Log_Items/Issue_28/evidence/`

**Pass criteria:**
- Client examples: 1CSIMN, 960CWP, 94PDIS in quikplan
- 141/141 crosswalk alignment (or 141 with DISCHO25)
- All protected validators PASS

---

## Repository constraints (AGENTS.md)

- Surgical edits only — no wholesale app.py rewrite
- Preserve QLA formatting and QuikPlan schema
- Preserve field order/types/lengths
- Version bump required when modifying app.py
- Do not break Issues #21M, #21M-FU, #21K, #25, #26

---

## Deliverables (Development stage)

```
Issue_Log_Items/Issue_28/Issue_28_Development_Report.md
Issue_Log_Items/Issue_28/evidence/ (before/after diffs, validator output)
tools/validators/_validate_issue28_plan_mapping.py
```

Update release notes only if repo convention requires at Development — otherwise defer to Closure.

---

## Rollback

If protected validator fails: revert `product_catalog_authority.py` + version; re-run v57.34 batch. See `Issue_28_Rollback_Checklist.md`.

---

## Stop condition

Stop after Development + mandatory validators PASS (or report failure with rollback recommendation).

Do **NOT** proceed to:
- Client UAT (B-02 still open for production)
- Closure / Release Integration
- Production deploy

At end of Development Report, include **Cursor-ready prompt for Validation Agent** with full context for the next chat.
```

---

*Risk Agent complete. No code modified.*
