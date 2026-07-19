# DG-R-006 — Business Decision

**Status:** DECIDED  
**Date:** 2026-07-18  
**Approved by:** User (chat)

## Decision

**Retire DG-QUIKPLAN-022** — remove the rule from data governance entirely.

- **Do not** rewrite QuikPlan `PLANVALOPT` / `*VARY*` data (CSO or WPA).
- Remove rule definition, runner registration, report wording, and tests for `DG-QUIKPLAN-022`.
- Correct `QLA_Migration/Data_Goverence.txt`: delete the incorrect line requiring PLANVALOPT=F when BACTIVE=F.
- Conversion: leave R7B / Sync_Rulebook PLANVALOPT=Y behavior unchanged (rate-file / PVO driven).

## Evidence

- QLAdmin Help: PVO (`PLANVALOPT`) enables plan-values options and rate-file lookup; not tied to open/closed status.
- WPA production: PLANVALOPT=T on 1847/1848 plans; all 1157 closed plans still have it on; 0 closed with it off.
- CSO: same pattern (121 closed with PLANVALOPT on). Turning it off risks breaking rate/value lookup for in-force policies on closed plans.
- Same pattern as DG-R-004: written rule disagreed with production and the product manual → change the rule, not the data.

## Scope of code/doc changes

| Area | Change |
|------|--------|
| `governance_items_quikplan.py` | Remove `RULE_DG_QUIKPLAN_022` from definition + `ALL_QUIKPLAN_RULES` |
| `governance_items.py` | Drop import/re-export of 022 |
| `registry.py` | Unregister 022 |
| `dg_quikplan_016_024_defaults_refs.py` | Remove `run_dg_quikplan_022` |
| `business_descriptions.py` | Remove 022 description |
| `test_dg_quikplan.py` | Remove 022 assertions |
| `RULE_CATALOG.md` | Note 022 retired |
| `Data_Goverence.txt` | Remove BACTIVE→PLANVALOPT=F line |

## Out of scope

- Any QuikPlan DBF writes  
- Changing R7B / Sync_Rulebook PLANVALOPT defaults  
- Other DG-QUIKPLAN rules  

## Risk acceptance

- Prior written “IF BACTIVE IS F THEN PLANVALOPT NEEDS TO BE FALSE” was incorrect relative to QLAdmin PVO behavior and production practice; retired under this decision.
