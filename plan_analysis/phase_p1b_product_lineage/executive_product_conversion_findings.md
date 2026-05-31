# Executive Product Conversion Findings — Phase P1B

**Date:** 2026-05-26  
**Scope:** Analysis + governance scaffold only — no conversion code changes  
**Primary Source:** `plan_analysis/quikplan_source.csv`

---

## Executive Summary

Phase P1B confirms that product setup conversion is a **distinct governance domain** upstream of policy and claims conversion. Plan identity currently flows through multiple authorities (LifePRO source, PCOMP, Master_Crosswalk plan rows, Policy Form Crosswalk, rulebook defaults) with material semantic and FORM alignment risk.

---

## Key Metrics

| Metric | Value |
|---|---|
| LifePRO source coverages (quikplan_source) | 133 |
| PCOMP component rows | 184 |
| Policy Form Crosswalk rows | 141 |
| Current quikplan output rows | 133 |
| Unique output PLAN codes | 132 |
| quikridr rows | 11698 |
| Distinct quikridr MPLAN values | 140 |
| MPLAN orphan (not in quikplan.PLAN) | 7 |
| Blank quikridr MPLAN rows | 2348 |
| Master_Crosswalk plan-like mappings | 237 |
| FORM conflicts (crosswalk vs output) | 94 |
| Duplicate PLAN in output | 1 |
| High-priority semantic review rows | 40 |
| Authority conflict rows | 353 |

---

## Critical Findings

### 1. Join Key Ambiguity (Highest Risk)

- Source `COVERAGE_ID` uses LifePRO plan identifiers (e.g., `0822 620`, `L17 1`).
- Output `PLAN` uses QL plan codes (e.g., `920ADB`) for ~77% of rows via mapping.
- Policy Form Crosswalk links LifePRO Coverage_ID → QL Plan Code — **correct business join path**.
- Master_Crosswalk.csv contains ~237 plan mappings mixed with policy numbers — **violates stated policy-only authority** and creates collision risk with claims crosswalk.

### 2. FORM Authority Divergence

Only **8** of **102** crosswalk-matched plans have FORM aligned to QL Form Number. LifePRO `POLICY_FORM_NUM` is currently winning in rulebook routing — business crosswalk should override after signoff.

### 3. quikridr Dependency Explosion

- **11,698** quikridr rows depend on **140** MPLAN values.
- **7** MPLAN codes have no quikplan catalog row (1L15GD, 1L16GD, 9DIS80, 9DIS90, DISCHO20 B, L16POLFEE, L17 BASE).
- **2,348** rows have blank MPLAN — linkage integrity risk.

### 4. Semantic Blurring (LifePRO vs QLAdmin)

LifePRO mixes base plans, riders, supplemental coverages, and form variants in one source table. PCOMP `COMPONENT_TYPE` (BA, WP, AD, etc.) and EXHIBIT_CODE (SUP, WHO, etc.) provide separation signals QLAdmin expects via QuikPlan vs QuikRidr.

### 5. Future Actuarial Attachment Not Ready

- HRIGPKEY: **0/133** populated (correct — not implemented).
- PLANTYPE: **blank on all rows**.
- GDVARYGP/BDVARY* defaulted; UWVARY/STVARY blank — rate attachment dimensions undefined.

### 6. Effective Date / Versioning Gap

Policy Form Crosswalk has **no effective-date dimension**. PCOMP END_DATE is uniformly 20991231. Product versioning and grandfathering cannot be governed without business date keys.

---

## Confirmed Business Decisions Honored

- MPHASE 1 = base coverage; riders MPHASE > 1
- Master_Crosswalk.csv stated role: policy numbers only (current state deviates — flagged)
- No HRIGPKEY implementation in this phase
- No silent auto-remediation
- Rulebook-driven architecture preserved

---

## Recommendations (Next Phases)

1. **P1C — Join Key Proof:** Validate LifePRO COVERAGE_ID → Crosswalk join with business signoff sample set.
2. **Segregate plan mappings** from Master_Crosswalk into Policy Form Crosswalk authority path.
3. **Stand up plan_governance/** with hold manifests mirroring claims Phase 22 pattern.
4. **Build isolated product runner** — do not integrate into core batch until governance cleared.
5. **FORM override policy** — crosswalk FORM wins over LifePRO POLICY_FORM_NUM after review.
6. **Orphan MPLAN remediation** — 7 codes + 2,348 blank rows require product review before UAT.

---

## Deliverables Produced (Phase P1B)

1. `plan_dependency_map.csv`
2. `product_semantic_classification_workbench.csv`
3. `plan_crosswalk_authority_analysis.csv`
4. `future_rate_attachment_analysis.csv`
5. `plan_effective_date_governance_analysis.csv`
6. `proposed_product_governance_model.md`
7. `plan_source_to_output_lineage.csv`
8. `recommended_plan_governance_folder_structure.md`
9. `recommended_product_runner_architecture.md`
10. `executive_product_conversion_findings.md`

---

## Explicit Non-Actions (This Phase)

- No app.py changes
- No quikplan conversion rewrite
- No claims orchestration changes
- No HRIGPKEY / actuarial load implementation
- No source extract mutation
