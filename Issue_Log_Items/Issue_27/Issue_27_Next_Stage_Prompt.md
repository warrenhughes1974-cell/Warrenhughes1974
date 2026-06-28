# Issue #27 — Next Stage Prompt

**Issue:** SL Phase of Insurance  
**Date:** 2026-06-28  
**Validation:** ✅ PASS  
**Recommended next stage:** **Regression & Deployment Agent**

---

## Cursor-ready prompt — Regression & Deployment Agent

```
# Issue #27 — Regression & Deployment Agent

**LifePRO → QLAdmin Conversion Platform**
**Version:** v57.39
**Validation:** PASS — see Issue_27_Final_Validation_Report.md

## Context
Issue #27 suppresses LifePRO BENEFIT_TYPE SL from quikridr emit.
Validation confirmed:
- 67 SL policies converted; 0 SL phases in quikridr
- Duplicate face: 46 → 0
- MMODEPREM: 28/28 premium SL policies match PPOLC
- quikridr: 6934 rows (−68 authorized)
- Audit: 68 rows in Issue_27_SL_Suppression_Audit.csv

Read:
- Issue_Log_Items/Issue_27/Issue_27_Final_Validation_Report.md
- Issue_Log_Items/Issue_27/Issue_27_Regression_Report.md
- Issue_Log_Items/Issue_27/Issue_27_Release_Recommendation.md
- Issue_Log_Items/Issue_27/Issue_27_Client_UAT_Package.md

## Your task

1. Update validator baselines:
   - quikridr expected count: 6934 (was 7002)
   - Document in validator comments or baseline config

2. Git hygiene (if authorized by user):
   - Stage v57.39 changes: app.py, QLA_Migration/app.py, qla_core/sl_benefit_governance.py, validators
   - Commit with message referencing Issue #27

3. Protected issue baseline refresh:
   - Re-run validate_issue21m_quikmemo.py with updated quikridr baseline
   - Investigate quikclnt 13514 vs 13846 delta (NOT #27 caused — document finding)

4. Client UAT coordination:
   - Deliver Issue_27_Client_UAT_Package.md to Eric
   - Request sign-off on trace policy 010448806C

5. Produce deliverables:
   - Issue_27_Deployment_Report.md
   - Issue_27_Baseline_Update_Log.md
   - Updated release notes if needed

## Constraints
- Do NOT revert Issue #27 SL suppression
- Do NOT modify rulebooks or crosswalks unless explicitly authorized
- Preserve protected issues #21M, #21M-FU, #21K, #21D, #21J, #25, #26, #28

## Exit criteria
- Baselines updated for quikridr 6934
- Client UAT package delivered
- Deployment report complete

Stop after Deployment Report — hand off to Client UAT sign-off.
```

---

## Stage flow (complete)

```
Planning ✅ → Ownership Decision ✅ → Development ✅ → Validation ✅ → Deployment ⏳
```

---

**Next stage:** Regression & Deployment Agent
