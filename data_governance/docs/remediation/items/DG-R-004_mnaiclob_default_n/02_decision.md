# DG-R-004 — Business Decision

**Status:** DECIDED  
**Date:** 2026-07-18  
**Approved by:** User (chat)

## Decision

**Option R1 — Change DG-QUIKPLAN-024 required value from `N` to `NAPLAN`.**

- **Do not** rewrite QuikPlan `MNAICLOB` data (CSO or production).
- Align governance catalog, rule implementation, tests, report wording, and `QLA_Migration/Data_Goverence.txt` with production practice (`NAPLAN`).
- Conversion: default/preserve `MNAICLOB=NAPLAN` if QuikPlan emit touches this field; do **not** force `N`.

## Evidence

- Production: `Q:\WPA\WPA_GABIE\QUIKPLAN.DBF` — MNAICLOB = NAPLAN (user confirmed)
- CSO: `Q:\CSO\CSO_Test_6_30_2026\quikplan.dbf` — 142/142 NAPLAN

## Scope of code/doc changes

| Area | Change |
|------|--------|
| `governance_items_quikplan.py` RULE_DG_QUIKPLAN_024 | Expected value NAPLAN |
| `dg_quikplan_016_024_defaults_refs.py` (024 logic) | Compare to NAPLAN |
| Tests (`test_dg_quikplan.py`, fixtures) | Expect NAPLAN |
| `business_descriptions.py` / RULE_CATALOG / QuikPlan schema notes if they say default N | NAPLAN |
| `QLA_Migration/Data_Goverence.txt` | `MNAICLOB- DEFAULT NAPLAN` |
| Conversion QuikPlan path | If MNAICLOB is emitted/defaulted, use NAPLAN not N |

## Out of scope

- Mass UPDATE of QuikPlan DBF  
- Other DG-QUIKPLAN rules  
- Changing production WPA_GABIE data  

## Risk acceptance

- Prior written “DEFAULT N” was incorrect relative to production; corrected under this decision.
