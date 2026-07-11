# Issue #50 — Tracking Sheet

| Field | Value |
|-------|-------|
| Issue ID | 50 |
| Title | Policy Notes Missing |
| Status | **Closed** |
| Gates | G0–G7 complete · Client UAT Pass · **Closed** |
| Engine | **v57.75** |
| Resolution | QUIKMEMO now reads PNOTE notes with commas via fixed-width parse and stores left-padded MEMOKEY in the DBF so QLAdmin Memo tab SEEK matches quikmstr. Policies that previously had no notes but gained them include 01159D276C, 01222DCC, 01330D153C, 014075AC, 018187C, 018253C, 018910C, and 01ML8522C. |
| Reporter | Eric |
| Owner | Warren (Conversion) |
| Example | 018495BC / 9018495B / 1SALML |
| Suspected root cause | PNOTE CSV `on_bad_lines=skip` drops notes with commas in LINE text |
| Engine touch (planned) | `qla_core/quikmemo_converter.py` read path only |
| Related | #21M, #21M-FU, #21J, #25, #28 (context) |

## Deliverables

| Artifact | Path |
|----------|------|
| Intake | `Issue_50_Intake_Summary.md` |
| Planning | `Issue_50_Planning_Report.md` |
| Dependency Gate | `Issue_50_Dependency_Gate.md` |
| Risk Review | `Issue_50_Risk_Review_Report.md` |
| Research script | `scripts/research_issue50_pnote_parse.py` |
| Implementation | `Issue_50_Implementation_Notes.md` |
| Validation | `Issue_50_Validation_Report.md` |
| Regression | `Issue_50_Regression_Report.md` |
| Resolution | `Issue_50_Resolution_Summary.md` |
| Validator | `tools/validators/validate_issue50_pnote_parse.py` |
| Evidence | `evidence/issue50_*.csv` |
