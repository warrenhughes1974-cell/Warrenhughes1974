# Issue #27 — Release Integration Prompt

**Issue:** SL Phase of Insurance  
**Date:** 2026-06-28  
**Engine version:** v57.39  
**Regression & Deployment:** ✅ PASS  
**Next stage:** **Client UAT Agent**

---

## Cursor-ready prompt — Client UAT Agent

```
# Issue #27 — Client UAT Agent

**LifePRO → QLAdmin Conversion Platform**
**Version:** v57.39

## Context
Issue #27 suppresses LifePRO BENEFIT_TYPE SL from quikridr emit.
Regression & Deployment PASS. Release package complete. Awaiting client verification.

Key outcomes (already validated technically):
- 67 SL policies converted; 0 SL phases in quikridr
- Duplicate face: 46 → 0
- quikridr: 6934 rows (−68 authorized)
- MMODEPREM: 28/28 premium SL policies match PPOLC
- Trace 010448806C: 2 coverage rows (BA + PUA), premium 62.40

Read:
- Issue_Log_Items/Issue_27/Issue_27_Client_UAT_Final.md
- Issue_Log_Items/Issue_27/Issue_27_Final_Validation_Report.md
- Issue_Log_Items/Issue_27/Issue_27_SL_Suppression_Audit.csv
- Issue_Log_Items/Issue_27/Issue_27_Closure_Recommendation.md

## Your task

1. Coordinate Client UAT with Eric using Issue_27_Client_UAT_Final.md sign-off form.

2. Primary UAT — Policy 010448806C:
   - Coverage tab: exactly 2 rows (Base 170858 + PUA 1708PA)
   - No duplicate 5,778 face row
   - Mode premium: 62.40

3. Sample UAT — 10 policies from Client UAT Final §3:
   - Confirm no SL coverage row
   - Confirm no duplicate face
   - Spot-check MMODEPREM where listed

4. Document client findings in Issue_27_Client_UAT_Results.md:
   | Policy | Coverage rows | Dup face? | Premium OK? | Pass/Fail |
   |--------|--------------|-----------|-------------|-----------|

5. If ALL pass:
   - Produce Issue_27_Client_UAT_Signoff.md
   - Produce Issue_27_Production_Deployment_Prompt.md
   - Update Issue_Log_Master_Tracking_Sheet.md (Issue #27 → UAT PASS)

6. If ANY fail:
   - Stop immediately
   - Document failure with screenshots/evidence
   - Produce Issue_27_Development_Rework_Prompt.md
   - Do NOT deploy to production

## Constraints
- Do NOT modify converter code during UAT
- Do NOT re-run batch unless client requests fresh output
- Escalate data questions to Eric before assuming defect

## Exit criteria
- Client sign-off captured OR documented failure
- Issue_27_Client_UAT_Results.md complete

Stop after Client UAT — hand off Production Deployment if sign-off received.
```

---

## Stage flow

```
Planning ✅ → Development ✅ → Validation ✅ → Regression & Deployment ✅ → Client UAT ⏳ → Production ☐
```

---

**Next stage:** Client UAT Agent (Eric)
