# DG-R-004 — Change Log

**Status:** Applied  
**Date:** 2026-07-18  
**Data region:** `Q:\CSO\CSO_Test_6_30_2026` (read-only for this item)  
**Decision:** Option R1 — change DG-QUIKPLAN-024 required value to `NAPLAN`; no QuikPlan data rewrite  
**APP_VERSION:** unchanged (no QuikPlan conversion emit code changes)

---

## Scope of changes

Rule/docs/tests only. **Zero** writes to `quikplan.dbf` / `QUIKPLAN.DBF` on `Q:\CSO` or `Q:\WPA`.

| Area | File | Change |
|------|------|--------|
| Catalog | `data_governance/catalog/governance_items_quikplan.py` | RULE_DG_QUIKPLAN_024: required value `N` → `NAPLAN` |
| Rule impl | `data_governance/rules/plan_setup_integrity/dg_quikplan_016_024_defaults_refs.py` | Compare MNAICLOB to `NAPLAN`; fail message/expected updated |
| Report text | `data_governance/reporting/business_descriptions.py` | Check/required/problem text → NAPLAN |
| Tests | `data_governance/tests/test_dg_quikplan.py` | Fixture `MNAICLOB` → `NAPLAN` |
| Tests | `data_governance/tests/conftest.py` | Both QuikPlan fixtures `MNAICLOB` → `NAPLAN` |
| Schema notes | `data_governance/docs/QuikPlan_Schema_Verification.md` | Default NAPLAN |
| Catalog summary | `data_governance/docs/RULE_CATALOG.md` | Note 024 = NAPLAN |
| Business defaults | `QLA_Migration/Data_Goverence.txt` | `MNAICLOB- DEFAULT NAPLAN` |

---

## Conversion path (checked, not modified)

| Check | Result |
|-------|--------|
| Grep `MNAICLOB` in `app.py` / `QLA_Migration/app.py` | No matches |
| Grep in `qla_core` | Schema field list only (`schema_constants.py`) |
| `QLA_Migration/Configs/Sync_Rulebook_quikplan.csv` | Already `,MNAICLOB,NAPLAN,,,` — no change needed |
| APP_VERSION bump | **Not required** (no emit/default logic change) |

---

## Data mutation counts

| Table / path | Rows mutated |
|--------------|-------------:|
| CSO `quikplan.dbf` | **0** |
| WPA `QUIKPLAN.DBF` | **0** |
| Any QuikPlan DBF | **0** |

---

## Not changed

- Other DG-QUIKPLAN rules (001–023, 025–033)
- QuikList / QuikDate / QuikChrt data or rules
- Conversion converters / `app.py`
