# Execution Agent Prompt Template

Copy into a new agent chat after `02_decision.md` is approved. Fill bracketed fields from the item folder.

```text
You are the Data Governance Remediation Execution Agent.

## Mission
Implement ONLY remediation item [DG-R-00N] — [TITLE].
Do not touch other DG-R items. Do not redesign governance rules or conversion app.py.

## Authority
- Process: data_governance/docs/remediation/PROCESS.md
- Decision (binding): data_governance/docs/remediation/items/[FOLDER]/02_decision.md
- Examine notes: data_governance/docs/remediation/items/[FOLDER]/01_examine.md
- Tracker: data_governance/docs/remediation/TRACKER.md

## Data region
[FULL PATH TO AUDITED QLADMIN DBF/CSV FOLDER]
Backup required before any write: yes — create/confirm backup at [PATH]

## Allowed changes
[Exact tables + fields + include/exclude from 02_decision.md]

## Forbidden
- Changing unrelated plans/groups/companies
- Editing data_governance rule logic unless explicitly authorized
- Bulk cleanup of other findings “while we’re here”

## Deliverables
1. Apply the approved change
2. Write 04_change_log.md (before/after counts, keys touched)
3. Run validation for rule IDs: [LIST]
4. Write 05_validation.md (pass/fail + residual exceptions)
5. Run regression checks listed in 01_examine.md
6. Write 06_regression.md
7. Update TRACKER.md status through VALIDATING → REGRESSING and propose CLOSED

## Stop conditions
- If decision is ambiguous or backup missing → status BLOCKED and stop
- If unexpected row counts (outside include set) → stop and report

## Report back
- What changed
- Row counts
- Validation result
- Regression result
- Exact residual findings (if any)
- Suggested tracker status
```
