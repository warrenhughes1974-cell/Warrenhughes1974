# Issue #28 — Release Dependencies

**Gate date:** 2026-06-24  
**Proposed release:** v57.35

---

## Release readiness assessment

| Dependency | Ready? | Notes |
|------------|--------|-------|
| Technical fix defined (Option A) | **Yes** | Planning complete |
| Version bump path | **Yes** | v57.34 → v57.35 |
| Client crosswalk binding (B-01) | **No** | Blocks Development start |
| Client re-UAT acceptance (B-02) | **No** | Blocks Release |
| Validation tooling | **Partial** | V-28-01 pending Development |
| Catalog sync | **No** | Migration copy 133 vs 140 rows |

**Can ship as v57.35?** **Yes, technically** — after Development + Validation. **Not before** client dependencies and regression PASS.

---

## Expected release artifacts

| Artifact | Owner | When | Status |
|----------|-------|------|--------|
| `Release_Notes/v57.35_Release_Notes.md` | Development/Closure | Post-validation | **Not created** |
| `Release_Manifest_v57.35.md` | Closure | Post-validation | **Not created** |
| `Issue_Log_Items/Issue_28/evidence/` before/after diffs | Validation | Post-batch | **Not created** |
| Issue #28 validation report | Validation Agent | G5 | **Not created** |
| Rollback instructions | Implementation Strategy | In release notes | **Drafted** in Planning |
| Client UAT packet | UAT Dependencies doc | Pre-Release | **Drafted** |
| `Issue_Log_Master_Tracking_Sheet.md` update | Closure | G7 | **Pending** |

---

## Release scope (proposed v57.35)

### In scope

| Phase | Change |
|-------|--------|
| Phase 0 | DISCHO25 catalog row + catalog sync |
| Phase 1 | `load_product_catalog_crosswalk()` authority promotion |
| Phase 1 | `_validate_issue28_plan_mapping.py` |
| Phase 1 | Version bump app.py / QLA_Migration/app.py |

### Optional same release

| Phase | Change |
|-------|--------|
| Phase 2 | P3E MPLAN alignment enablement |
| Phase 3 | `mapping_status` governance cleanup |

### Explicitly out of scope (unless client expands)

- FORM column alignment to crosswalk form numbers
- Master_Crosswalk product row additions
- Rate table content updates

---

## Deployment dependencies

| Step | Dependency |
|------|------------|
| 1 | Merge v57.35 code + catalog CSV changes |
| 2 | Sync `plan_governance/product_catalog_crosswalk.csv` → `QLA_Migration/Mapping/` |
| 3 | Run full batch on production source package |
| 4 | Run validator suite (V-28 + protected issues) |
| 5 | Deliver client UAT packet |
| 6 | Client UAT PASS |
| 7 | Production deploy |

---

## Rollback release dependencies

| Rollback trigger | Action | Time to restore |
|------------------|--------|---------------|
| Client UAT fail on PLAN codes | Revert v57.35 commit; re-run v57.34 batch | Same day |
| Protected issue regression fail | Revert; do not partial-deploy | Immediate |
| Rate lookup failures | Assess per-plan; may revert or rate patch | Case-by-case |

Rollback does **not** require crosswalk or xlsx revert — compat column preserved.

---

## Version numbering

| Item | Value |
|------|-------|
| Baseline | v57.34 |
| Target | **v57.35** |
| Bump required? | **Yes** — conversion behavior change per AGENTS.md |
| Parallel QLA_Migration/app.py | **Yes** — mirror version |

---

## Release dependency on protected issues

| Issue | Release constraint |
|-------|-------------------|
| #21M / #21M-FU | Must remain PASS — no regression in release notes |
| #21K | Validator env note — not blocking #28 release if env missing |
| #25 | MPOLICY validator mandatory in release checklist |
| #26 | MPREM validator mandatory in release checklist |

---

## Changelog entries (draft — for Release Notes)

- **Issue #28:** Promote Policy Form Crosswalk 5/22/2026 authoritative PLAN codes (`crosswalk_ql_plan_code`) at runtime for quikplan conversion (33 plan mappings corrected).
- **Issue #28 Phase 0:** Add DISCHO25 product catalog row.
- **Issue #28 (optional Phase 2):** Enable P3E closed MPLAN authority alignment for quikridr.

---

## Gate verdict for release

Release dependencies are **understood and documented**. Release **blocked** until:

1. B-01 (client binding) — before Development  
2. Development + Validation complete  
3. B-02 (re-UAT acceptance) — before Release  
4. Client UAT PASS — before Production
