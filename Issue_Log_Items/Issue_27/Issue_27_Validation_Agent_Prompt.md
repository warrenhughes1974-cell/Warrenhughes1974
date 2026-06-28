# Issue #27 — Validation Agent Prompt

**Issue:** SL Phase of Insurance  
**Date:** 2026-06-28  
**Engine version:** v57.39  
**Development:** ✅ COMPLETE

---

## Cursor-ready prompt — Validation Agent

```
# Issue #27 — Validation Agent

**LifePRO → QLAdmin Conversion Platform**
**Version:** v57.39

## Context
Development complete. SL (Substandard Life) suppressed from quikridr emit.
Business rule: SL is rating metadata, not coverage. QLAdmin rating structure handles substandard.

Read:
- Issue_Log_Items/Issue_27/Issue_27_Development_Report.md
- Issue_Log_Items/Issue_27/Issue_27_SL_Suppression_Audit.csv
- Issue_Log_Items/Issue_27/Issue_27_Validation_Results.md
- Issue_Log_Items/Issue_27/Issue_27_Regression_Results.md

## Your task

1. Re-run full batch: python tools/batch_tests/run_full_batch_test.py
2. Run validators:
   - python tools/validators/validate_issue27_sl_quikridr.py
   - python tools/validators/validate_issue28_plan_mapping.py
   - python tools/validators/validate_issue21d_mdepint.py
   - python tools/validators/validate_issue26_mprem.py (if baseline available)
   - python tools/validators/validate_issue21m_quikmemo.py
3. Verify audit CSV: 68 rows, SL_TABLE_CODE populated (66+), SUPPRESSION_REASON = Issue #27
4. Spot-check policies:
   - 010448806C: 2 quikridr rows, MMODEPREM=62.40, audit SL_TABLE_CODE=32
   - 010799083C: no duplicate 25,000 face, MMODEPREM=175.73
5. Confirm quikridr 6934 rows, quikmstr 5083 rows unchanged vs v57.39 dev batch
6. Produce Issue_27_Validation_Report.md with PASS/FAIL and sign-off recommendation

## Pass criteria
- 0 SL phases in quikridr
- 0 duplicate face on 67 SL policies
- MMODEPREM unchanged on premium-bearing SL population
- Protected issues #21M, #21M-FU, #21K, #21D, #21J, #25, #26, #28 PASS
- Audit CSV complete with table codes

## Constraints
- Do NOT modify code unless validation finds a defect
- Document any FAIL with root cause before proposing fix

Stop after Validation Report — hand off Release/Governance if PASS.
```

---

**Next stage:** Validation Agent
