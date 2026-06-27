# Issue #28 — Lessons Learned

**Issue:** Incorrect Plan Number Mapping  
**Closed:** 2026-06-27  
**Version:** v57.35

---

## 1. Authority column precedence must be explicit at runtime

**Finding:** The product catalog CSV held both `ql_plan_code` (compat/passthrough) and `crosswalk_ql_plan_code` (authoritative), but runtime loaded only the compat column. All 33 divergent rows had correct authoritative values sitting unused in the catalog.

**Lesson:** When governance separates compat vs authoritative columns, the loader must document and enforce precedence. A single-column fallback is insufficient when both columns coexist.

**Recommendation:** P2E generator and catalog regen should seed compat from authoritative on future regen; consider `mapping_status=AUTHORITY_ALIGNED` update in a future governance pass.

---

## 2. Catalog completeness is a hard gate for quikplan emission

**Finding:** DISCHO25 existed in Master_Crosswalk and quikplan_source but not in `product_catalog_crosswalk.csv`, blocking quikplan output and causing incorrect P3E resolution for the DISCHO family.

**Lesson:** Runtime catalog is the emit authority (P3C). Master_Crosswalk legacy rows do not substitute for missing catalog rows.

**Recommendation:** Catalog row-count parity checks against Policy Form Crosswalk xlsx should be part of release validation (141/141).

---

## 3. P3E resolver timing in batch order matters

**Finding:** Initializing the MPLAN resolver at batch startup used stale quikplan.csv from a prior run. Phase 2 required a post-quikplan refresh hook.

**Lesson:** Any downstream authority that intersects with quikplan PLAN universe must re-init **after** quikplan emit in the same batch run.

**Recommendation:** Document batch ordering dependency in RUN_GUIDE; log "refreshed resolver after quikplan emit" as operational verification.

---

## 4. Validation layering reduces release risk

**Finding:** Combination of `_issue28_intake_analysis.py`, dedicated `validate_issue28_plan_mapping.py`, and pandas diff against v57.34 baseline provided repeatable 141/141 proof.

**Lesson:** Issue-specific validators alongside general schema validation catch domain regressions that generic validators miss.

**Recommendation:** Retain Issue #28 validator in regression suite for future catalog or authority changes.

---

## 5. Client UAT scope must be explicit for PLAN corrections

**Finding:** Engineering validation PASS did not automatically satisfy B-02 (client re-UAT scope for 33 PLAN changes). Formal client sign-off was required before production eligibility.

**Lesson:** Data correction issues affecting product catalog require business acceptance even when automated validation is clean.

**Recommendation:** Include primary examples + spot-check worksheet in UAT package for all crosswalk-affecting issues.

---

## 6. Protected issue isolation preserved release velocity

**Finding:** Issue #28 touched only `product_catalog_authority.py` and catalog CSVs. Issues #25, #26, #21M, #21M-FU validators remained PASS without code changes to their paths.

**Lesson:** Surgical authority-layer fixes minimize blast radius when governance architecture (P2E/P3C/P3E) is respected.

---

## 7. Informational observations are not defects

**Finding:** V-16 rate gaps, CSO missing-plan lists, P3E PUA referential check, and #21K DBF artifact were documented as observations — none blocked Issue #28 closure after client acceptance.

**Lesson:** Distinguish **issue defects** from **downstream operational follow-ups** in validation and closure documentation.

---

## Process improvements for future issues

| Area | Improvement |
|------|-------------|
| Intake | Compare runtime loader column vs catalog authoritative column early |
| Planning | Always verify DISCHO/catalog gaps independently of main mismatch set |
| Development | Add batch refresh hook when enabling cross-table authority |
| Validation | Archive v57.N baseline before batch for diff evidence |
| Closure | Update master issue log and artifact index in same stage |
