# DG-R-011 — Change Log

**Status:** Applied  
**Date:** 2026-07-19  
**Decision:** Option R1 — revise DG-PLANVALUES-001/002; no DBF writes

## Data region

| Target | Action | Rows |
|--------|--------|-----:|
| CSO QuikPlCv / QuikPlTv / QuikQxs | **No writes** | 0 |
| WPA | **No writes** | 0 |

## Governance / docs changes

| File | Change |
|------|--------|
| `rules/.../dg_planvalues_001_003_refs.py` | `allow_blank=True` for 001/002; blank/null skipped |
| `catalog/governance_items.py` | 001/002 purpose/rule/failure text |
| `reporting/business_descriptions.py` | Blank allowed wording |
| `tests/test_dg_planvalues.py` | Blank/null MORT/ETIMORT expect PASS |
| `QLA_Migration/Data_Goverence.txt` | When populated → QuikQxs |
| `docs/RULE_CATALOG.md` | Blank/null skipped note |
| `docs/Implementation_Notes.md` | DG-R-011 note |

## Conversion

| Check | Result |
|-------|--------|
| `cso_mortality_crosswalk` blank-safe | **Unchanged** |
| `app.py` / APP_VERSION | **Not modified** |
