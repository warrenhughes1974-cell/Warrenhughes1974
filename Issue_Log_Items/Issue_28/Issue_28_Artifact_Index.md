# Issue #28 — Artifact Index

**Issue:** Incorrect Plan Number Mapping  
**Status:** CLOSED  
**Version:** v57.35  
**Index date:** 2026-06-27

---

## Closure deliverables

| Artifact | Stage | Description |
|----------|-------|-------------|
| `Issue_28_Closure_Report.md` | Closure | Official closure + Release Integration handoff |
| `Issue_28_Issue_Log_Entry.md` | Closure | Issue log entry |
| `Issue_28_Final_Summary.md` | Closure | Executive summary |
| `Issue_28_Lessons_Learned.md` | Closure | Process and technical lessons |
| `Issue_28_Artifact_Index.md` | Closure | This index |

---

## Client UAT

| Artifact | Description |
|----------|-------------|
| `Issue_28_Client_UAT_Report.md` | UAT report + Closure Agent handoff |
| `Issue_28_Client_Acceptance_Record.md` | Formal acceptance record |
| `Issue_28_Client_Signoff_Summary.md` | Executive signoff |
| `Issue_28_Final_Business_Approval.md` | Business approval + ops prerequisites |
| `Issue_28_Client_UAT_Package.md` | UAT test script for client |

---

## Regression & Deployment

| Artifact | Description |
|----------|-------------|
| `Issue_28_Regression_Report.md` | Regression baseline + Client UAT handoff |
| `Issue_28_Deployment_Readiness_Report.md` | Deployment readiness decision |
| `Issue_28_Release_Checklist.md` | Release checklist |
| `Issue_28_Deployment_Steps.md` | Ops deployment / rollback steps |
| `Issue_28_Final_Risk_Summary.md` | Final risk posture |

---

## Validation

| Artifact | Description |
|----------|-------------|
| `Issue_28_Validation_Report.md` | Validation decision + Regression handoff |
| `Issue_28_Validation_Results.md` | Validator results summary |
| `Issue_28_Regressions.md` | Protected issue regression |
| `Issue_28_Output_Delta_Report.md` | v57.34 → v57.35 delta |
| `Issue_28_PLAN_Validation_Report.md` | PLAN-specific validation |
| `Issue_28_MPLAN_Validation_Report.md` | P3E MPLAN validation |
| `Issue_28_V16_Rate_Validation.md` | Rate spot-check |
| `Issue_28_Final_Validation_Checklist.md` | Pre/post validation checklist |
| `Issue_28_Validation_Matrix.md` | Validation matrix |
| `Issue_28_PreValidation_Checklist.md` | Dev → Validation handoff |

---

## Development

| Artifact | Description |
|----------|-------------|
| `Issue_28_Development_Report.md` | Dev report + Validation handoff |
| `Issue_28_Code_Changes.md` | Code change detail |
| `Issue_28_File_Modification_Log.md` | File modification log |
| `Issue_28_Implementation_Summary.md` | Implementation summary |
| `Issue_28_Implementation_Strategy.md` | Approved implementation plan |

---

## Planning & Risk

| Artifact | Description |
|----------|-------------|
| `Issue_28_Intake_Report.md` | Root cause intake |
| `Issue_28_Planning_Report.md` | Planning decision |
| `Issue_28_Risk_Review_Report.md` | Risk review |
| `Issue_28_Risk_Assessment.md` | Risk assessment |
| `Issue_28_Regression_Impact.md` | Regression impact analysis |
| `Issue_28_PLAN_Comparison_Report.md` | 33 transition table |
| `Issue_28_DISCHO25_Investigation.md` | DISCHO25 analysis |
| `Issue_28_Population_Impact_Report.md` | Policy population impact |
| `Issue_28_Population_Summary.md` | Population summary |
| `Issue_28_Solution_Options.md` | Solution options |
| `Issue_28_Decision_Matrix.md` | Decision matrix |
| `Issue_28_Dependency_Gate_Report.md` | Dependency gate |
| `Issue_28_Dependency_Checklist.md` | Dependency checklist |
| `Issue_28_Blockers_And_Assumptions.md` | Blockers (B-01–B-05) |
| `Issue_28_Rollback_Checklist.md` | Rollback procedure |
| `Issue_28_Release_Dependencies.md` | Release dependencies |
| `Issue_28_UAT_Dependencies.md` | UAT dependencies |
| `Issue_28_Validation_Dependencies.md` | Validation dependencies |

---

## Analysis & data

| Artifact | Description |
|----------|-------------|
| `_issue28_intake_analysis.py` | Read-only comparison script |
| `Issue_28_Mapping_Differences.csv` | Post-fix mapping comparison |
| `Issue_28_Mapping_Inventory.md` | Mapping inventory |
| `Issue_28_Runtime_Mapping_Flow.md` | Runtime flow documentation |
| `Issue_28_Crosswalk_Inventory.csv` | Crosswalk inventory |
| `Issue_28_Missing_From_Converter.csv` | Intake missing analysis |
| `Issue_28_Extra_In_Converter.csv` | Intake extra analysis |
| `Issue_28_Trace_Samples.md` | Trace samples |
| `Issue_28_Policy_Impact_Summary.csv` | Policy impact |
| `_population_stats.json` | Population statistics |
| `_risk_affected_plans.csv` | Risk affected plans |

---

## Evidence (`evidence/`)

| File | Description |
|------|-------------|
| `v57.34_quikplan.csv` | Pre-fix quikplan baseline |
| `v57.34_quikridr.csv` | Pre-fix quikridr baseline |
| `v57.35_quikplan_plan_diff.csv` | 33 PLAN field changes |
| `validate_issue28_results.txt` | Issue #28 validator output |
| `issue28_intake_analysis_v5735.txt` | Intake analysis JSON output |
| `validate_output_v5735.txt` | Schema validator output |
| `validate_issue25_mpolicy.txt` | Issue #25 regression |
| `validate_issue26_mprem.txt` | Issue #26 regression |
| `validate_issue21m.txt` | Issue #21M regression |
| `validate_issue21m_fu.txt` | Issue #21M-FU regression |
| `validate_issue21k.txt` | Issue #21K regression |

---

## Code & config (v57.35)

| Path | Role |
|------|------|
| `qla_core/product_catalog_authority.py` | Authority promotion + P3E default |
| `plan_governance/product_catalog_crosswalk.csv` | Catalog (141 rows) |
| `QLA_Migration/Mapping/product_catalog_crosswalk.csv` | Migration catalog sync |
| `app.py` | v57.35 + P3E refresh |
| `QLA_Migration/app.py` | Mirror |
| `tools/validators/validate_issue28_plan_mapping.py` | Issue #28 validator |

---

## External authority

| Path | Role |
|------|------|
| `plan_analysis/source_data/crosswalk/Policy Form Crosswalk 5.22.26.xlsx` | Client-approved PLAN authority |

---

## Master tracking

| Path | Update |
|------|--------|
| `Issue_Log_Items/Issue_Log_Master_Tracking_Sheet.md` | Issue #28 marked CLOSED |

**Total Issue #28 markdown artifacts:** 51+ (including this index)  
**Framework stages completed:** 9 (Intake through Closure)
