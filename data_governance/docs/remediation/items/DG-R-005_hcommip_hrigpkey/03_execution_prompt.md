# DG-R-005 — Execution Agent Prompt

**Filled and auto-launched 2026-07-18.**

```text
You are the Data Governance Remediation Execution Agent.

## Mission
Implement ONLY DG-R-005 Option A: set HCOMMIP and HRIGPKEY to False on non-MEDS QuikPlan rows in CSO.
Do not change DG-QUIKPLAN-030 rule logic. Do not touch WPA.

## Authority
- data_governance/docs/remediation/items/DG-R-005_hcommip_hrigpkey/02_decision.md
- Repo: c:\Users\warren\Documents\GitHub\Warrenhughes1974

## Data region
Q:\CSO\CSO_Test_6_30_2026
Backup first: Q:\CSO\CSO_Test_6_30_2026_backup_DG-R-005_20260718 (QuikPlan.*)

## Allowed
1. QuikPlan: for rows where PLANTYPE (trim/casefold) != MEDS, set HCOMMIP=False and HRIGPKEY=False (DBF logical .F.)
2. If any MEDS rows exist: set both True (expect 0 on CSO)
3. Optional surgical conversion default False unless MEDS; bump APP_VERSION both app.py only if emit changes

## Forbidden
- Q:\WPA writes
- Changing rule 030 expected logic
- Other QuikPlan fields / other DG-R items

## Pre-flight
Confirm ~142 rows, 0 MEDS, raw mostly ? before write. If counts diverge, STOP.

## Validate
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2026" --output ".../DG-R-005_hcommip_hrigpkey/validation_out" --rule DG-QUIKPLAN-030
Expect PASS.

## Deliverables
04_change_log.md, 05_validation.md, 06_regression.md, update TRACKER propose CLOSED.
```
