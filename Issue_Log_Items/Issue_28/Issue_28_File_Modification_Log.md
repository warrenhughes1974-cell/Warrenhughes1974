# Issue #28 — File Modification Log

**Development date:** 2026-06-24  
**Engine version:** v57.35

---

## Modified files

| # | File | Phase | Change type | Lines affected (approx.) |
|---|------|-------|-------------|--------------------------|
| 1 | `plan_governance/product_catalog_crosswalk.csv` | 0 | Data — add DISCHO25 row | +1 row (141 total data rows) |
| 2 | `QLA_Migration/Mapping/product_catalog_crosswalk.csv` | 0 | Data — full sync from governance | Replaced (141 data rows) |
| 3 | `qla_core/product_catalog_authority.py` | 1, 2 | Code — authority + P3E default | ~25 lines |
| 4 | `app.py` | 1, 2 | Version + P3E refresh hook | ~12 lines |
| 5 | `QLA_Migration/app.py` | 1, 2 | Mirror of app.py changes | ~12 lines |

---

## Created files

| # | File | Purpose |
|---|------|---------|
| 1 | `tools/validators/validate_issue28_plan_mapping.py` | Issue #28 PLAN mapping validator |
| 2 | `Issue_Log_Items/Issue_28/Issue_28_Development_Report.md` | Development stage report |
| 3 | `Issue_Log_Items/Issue_28/Issue_28_Code_Changes.md` | Detailed code change log |
| 4 | `Issue_Log_Items/Issue_28/Issue_28_File_Modification_Log.md` | This file |
| 5 | `Issue_Log_Items/Issue_28/Issue_28_Implementation_Summary.md` | Executive summary |
| 6 | `Issue_Log_Items/Issue_28/Issue_28_PreValidation_Checklist.md` | Pre-validation checklist |

---

## Functions modified

| Function | File | Change |
|----------|------|--------|
| `load_product_catalog_crosswalk()` | `qla_core/product_catalog_authority.py` | Prefer `crosswalk_ql_plan_code`; fallback `ql_plan_code` |
| `closed_mplan_authority_enabled()` | `qla_core/product_catalog_authority.py` | Default ON (opt-out) |
| `process_data()` (batch loop) | `app.py`, `QLA_Migration/app.py` | Post-quikplan P3E resolver refresh |

---

## Version updates

| Location | Old | New |
|----------|-----|-----|
| `app.py` header | v57.34 | v57.35 |
| `app.py` UI title | v57.34 | v57.35 |
| `app.py` batch init log | v57.34 | v57.35 |
| `QLA_Migration/app.py` header | v57.34 | v57.35 |
| `QLA_Migration/app.py` UI title | v57.34 | v57.35 |
| `QLA_Migration/app.py` batch init log | v57.34 | v57.35 |

---

## Code paths affected

```
Batch init
  └─ closed_mplan_authority_enabled() [default ON]
  └─ _init_mplan_authority() [uses load_crosswalk_authority → load_product_catalog_crosswalk]

quikplan conversion
  └─ load_crosswalk_authority()
       └─ load_product_catalog_crosswalk() [crosswalk_ql_plan_code authority]
  └─ convert_quikplan_to_output() → _apply_crosswalk_value() [PLAN field]

Post-quikplan (batch)
  └─ _init_mplan_authority() [refresh resolver with new quikplan.csv]

quikridr conversion
  └─ mplan_resolver.resolve() [P3E authoritative MPLAN]
  └─ write_p3e_governance_outputs()
```

---

## Assumptions verified at development time

| Assumption | Status |
|------------|--------|
| Planning recommendation unchanged | Verified — read Implementation Strategy + Risk Report |
| 33 CROSSWALK_DIVERGENT rows in catalog | Verified — unchanged CSV structure |
| DISCHO25 distinct from DISCHO247C | Verified — separate authoritative codes |
| No new blockers since Risk Agent | None discovered |
| Protected issue code paths untouched | Verified — no edits in those modules |
