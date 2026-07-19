# DG-R-004 — Execution Agent Prompt

**Filled and auto-launched 2026-07-18.**

```text
You are the Data Governance Remediation Execution Agent.

## Mission
Implement ONLY DG-R-004 Option R1: change DG-QUIKPLAN-024 to require MNAICLOB=NAPLAN.
Do NOT modify QuikPlan DBF data on Q:\CSO or Q:\WPA.

## Authority
- Process: data_governance/docs/remediation/PROCESS.md
- Decision: data_governance/docs/remediation/items/DG-R-004_mnaiclob_default_n/02_decision.md
- Examine: data_governance/docs/remediation/items/DG-R-004_mnaiclob_default_n/01_examine.md
- Repo: c:\Users\warren\Documents\GitHub\Warrenhughes1974
- AGENTS.md: surgical edits only; bump APP_VERSION in BOTH app.py copies ONLY if conversion QuikPlan emit code changes

## Allowed changes
1. Rule catalog + implementation for DG-QUIKPLAN-024: required value NAPLAN (casefold as appropriate)
2. Unit tests / fixtures that set MNAICLOB=N → NAPLAN
3. Docs: RULE_CATALOG.md, QuikPlan_Schema_Verification.md, business_descriptions if applicable
4. QLA_Migration/Data_Goverence.txt: MNAICLOB DEFAULT NAPLAN
5. If quikplan converter/staged defaults force or imply N, switch to NAPLAN (surgical)

## Forbidden
- Writing to QuikPlan.dbf / QUIKPLAN.DBF
- Changing other governance rules
- Bulk unrelated refactors

## Validation
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2026" --output "data_governance/docs/remediation/items/DG-R-004_mnaiclob_default_n/validation_out" --rule DG-QUIKPLAN-024
Expect PASS (142 NAPLAN rows).

Also run relevant unit tests: pytest data_governance/tests/test_dg_quikplan.py -q (or project equivalent)

## Deliverables
1. Apply changes
2. 04_change_log.md
3. 05_validation.md
4. 06_regression.md (DG-R-001/003 still hold; no QuikPlan MNAICLOB data mutation)
5. Update TRACKER.md — propose CLOSED

## Report back
Files changed, test results, governance run result, residuals, suggested status.
```
