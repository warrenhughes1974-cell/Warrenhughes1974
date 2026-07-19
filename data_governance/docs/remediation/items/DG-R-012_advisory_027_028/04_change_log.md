# DG-R-012 — Change Log

**Status:** Applied  
**Date:** 2026-07-19  
**Decision:** Option R1 — revise 028; accept 027; no DBF writes

## Data region

| Target | Action | Rows |
|--------|--------|-----:|
| CSO / WPA annuity & value tables | **No writes** | 0 |

## Governance / docs changes

| File | Change |
|------|--------|
| `rules/.../dg_quikplan_025_030_supporting.py` | 028: Aint+Aexp required; Aing **or** Ainf |
| `catalog/governance_items_quikplan.py` | 028 business rule / failure conditions |
| `reporting/business_descriptions.py` | 028 wording |
| `tests/test_dg_quikplan.py` | `test_annuity_supporting_tables_aing_or_ainf` |
| `QLA_Migration/Data_Goverence.txt` | Clarified Aing/Ainf OR |
| `docs/RULE_CATALOG.md` / `Implementation_Notes.md` | DG-R-012 notes |

## Conversion

| Check | Result |
|-------|--------|
| `app.py` / APP_VERSION | **Not modified** |
