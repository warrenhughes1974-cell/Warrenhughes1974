# DG-R-003 — Execution Agent Prompt

**Filled and auto-launched 2026-07-18.**

```text
You are the Data Governance Remediation Execution Agent.

## Mission
Implement ONLY remediation item DG-R-003 — QuikDate prior-month-end.
Two parts: (1) live DBF patch, (2) surgical conversion emit so QuikDate always follows DG-QUIKDATE-001/002/003 (+ ACH defaults 004/005/006 when emitting).

## Authority
- Process: data_governance/docs/remediation/PROCESS.md
- Decision: data_governance/docs/remediation/items/DG-R-003_quikdate_prior_month_end/02_decision.md
- Examine: data_governance/docs/remediation/items/DG-R-003_quikdate_prior_month_end/01_examine.md
- Tracker: data_governance/docs/remediation/TRACKER.md
- Repo: c:\Users\warren\Documents\GitHub\Warrenhughes1974
- Follow AGENTS.md: surgical edits only; bump APP_VERSION in BOTH app.py and QLA_Migration/app.py

## Part 1 — Live data region
Path: Q:\CSO\CSO_Test_6_30_2026
Backup: Q:\CSO\CSO_Test_6_30_2026_backup_DG-R-003_20260718 (QUIKDATE.* before write)

Set single QuikDate row:
- PACBILL = 2026-06-30
- DIRBILL = 2026-06-30
- REINBILL = 2026-06-30
Leave ACHFILEID, ACHFILEID2, ESC_DATE, PROCDATE, other fields unchanged.

Validate:
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2026" --output "<item>/validation_out" --item DG-QUIKDATE

## Part 2 — Conversion always follows DG-R-003
- QuikDate is NOT emitted today (Converted_Tables says "not needed"). Add surgical emit/apply-defaults:
  - PACBILL/DIRBILL/REINBILL = prior_month_end(conversion_run_date)
  - ACHFILEID=0, ACHFILEID2=A, ESC_DATE blank
- Reuse same prior-month-end definition as data_governance.data_access.normalization.prior_month_end (share helper; do not diverge)
- Wire into conversion surgically; bump APP_VERSION both app.py copies
- Minimal tests if a pattern exists; document Output now may include quikdate.csv
- Do NOT redesign architecture or edit unrelated converters

## Deliverables
1. Apply Part 1 + Part 2
2. Write 04_change_log.md
3. Write 05_validation.md (governance DG-QUIKDATE pass on live region)
4. Write 06_regression.md (DG-R-001 still holds; non-target QuikDate fields unchanged; conversion unrelated tables unchanged)
5. Update TRACKER.md — propose CLOSED

## Forbidden
- Other DG-R items
- Changing governance rule logic to silence findings
- Editing GRPBILL/APLBILL/etc. unless required for a minimal valid QuikDate row schema

## Report back
What changed, row counts, APP_VERSION, validation/regression, residuals, suggested status.
```
