# Issue #32 — Next Stage Prompt

**Route to:** **Regression & Deployment Agent**  
**Prior stage:** Validation Agent ✅ PASS  
**Engine:** v57.40  
**Production emit:** NO-GO (until Regression + UAT)  
**Generated:** 2026-06-29

---

## Context

Issue #32 formal Validation **PASS**:

- 384 QuikLoan emit rows; 528 zero-balance held; 1 blocked (9011190668)
- v1.2 field mapping verified on all emit rows (0 failures)
- Trace policy `010331768C` matches expected output
- Full batch with QuikLoan flags completed successfully
- Protected issues show no #32-attributable regression
- Emit remains env-gated

**Validation evidence:** `Issue_32_Final_Validation_Report.md`, `Issue_32_Validation_Evidence.json`

---

# Regression & Deployment Agent — Prompt

```
# Issue #32 — Regression & Deployment Agent

**Project:** LifePRO → QLAdmin Conversion Platform
**Version:** v57.40
**Issue:** #32 — Policy Loan Conversion (PLOAN → QuikLoan)
**Prior stage:** Validation Agent ✅ PASS
**Production emit:** NO-GO until this stage + client UAT

## Objective

Execute formal regression sign-off and prepare controlled deployment/UAT package for QuikLoan.
Do NOT enable default production emit without explicit release authority after UAT PASS.

## Constraints

- Do NOT modify converter code unless regression finds a defect (then route back to Development)
- Do NOT modify rulebooks or crosswalks
- Do NOT change default env flag behavior in code
- Preserve Issues #21D, #21J, #21K, #21M, #21M-FU, #25, #26, #27, #28, #31

## Required regression steps

### 1. Baseline batch (flags OFF)

Run standard batch WITHOUT QuikLoan flags:

```powershell
cd <repo_root>
Remove-Item Env:QLA_ENABLE_QUIKLOAN_EMIT -ErrorAction SilentlyContinue
Remove-Item Env:QLA_QUIKLOAN_WRITE_OUTPUT -ErrorAction SilentlyContinue
python tools/batch_tests/run_full_batch_test.py
```

Confirm:
- quikmstr: 5083, quikridr: 6934, quikplan: 141, quikmemo: 4380, quikclnt: 13514
- quikloan.csv NOT created (or stale from prior run — document)
- Log shows "Skipping QUIKLOAN"

### 2. Gated QuikLoan batch (flags ON)

```powershell
$env:QLA_ENABLE_QUIKLOAN_EMIT = "1"
$env:QLA_QUIKLOAN_WRITE_OUTPUT = "1"
python tools/batch_tests/run_full_batch_test.py
```

Confirm:
- quikloan.csv: 384 rows
- All other table counts unchanged vs step 1
- Batch log: v57.40, "384 emit rows"

### 3. Protected issue validator suite

Run and document:

```powershell
python tools/validators/validate_issue27_sl_quikridr.py
python tools/validators/validate_issue26_mprem.py
python tools/validators/validate_issue28_plan_mapping.py
python tools/validators/validate_issue21m_quikmemo.py
python tools/validators/validate_issue21d_mdepint.py
python tools/validators/validate_issue21d_blank_names.py
python tools/validators/validate_quikloan_issue32.py
```

Expected:
- #27, #26, #28, #21D: PASS
- #21M: PASS on memo metrics; quikclnt baseline 13846 is known pre-existing drift (actual 13514)
- #21K DBF: optional — CSV PASS sufficient for batch regression

### 4. Schema / packaging check

- quikloan.csv columns match QUIKLOAN_SCHEMA (9 fields)
- Field formats: dates YYYYMMDD, amounts 2 dp, MLOANINT 2 dp
- If DBF packaging required: confirm QLAdmin QuikLoan load path with client

### 5. Client UAT package

Prepare for client verification on policy 010331768C:

| Field | Expected after load |
|-------|--------------------:|
| MLOANPRIN | 3707.11 |
| MLOANBAL | 3707.11 |
| MLOANINT | 5.00 |
| MLOANINTX | A |
| MLOANIDT | 20250725 |
| MLOANDATE | 20250725 |
| MLOANACCR | 0.00 (QLAdmin calc after load) |
| MLOANBILL | 0.00 |

**UAT question:** Does QLAdmin calculate/display loan interest consistent with LifePRO (~18.19 advance semantics)?

Include:
- quikloan.csv row for 010331768C
- Issue_32_Policy_9010331768_Validation.md
- Issue_32_LifePRO_Screenshot_Evidence_Trace.md

### 6. Known items for regression sign-off

Document as accepted (not defects):
- MLOANINTX fallback A (913 policies) until QuikPlan LOANINTX fixed
- 9011190668 blocked (missing ACCRUAL_DATE)
- 528 zero-balance policies excluded
- MLOANACCR=0.00 by design

## Deliverables (Regression Agent)

Create under Issue_Log_Items/Issue_32/:

1. Issue_32_Formal_Regression_Report.md
2. Issue_32_Batch_Flags_OFF_Results.md
3. Issue_32_Batch_Flags_ON_Results.md
4. Issue_32_UAT_Handoff_Package.md
5. Issue_32_Release_Readiness_Checklist.md
6. Issue_32_Next_Stage_Prompt.md (Deployment/UAT closure prompt if PASS)

Update Release_Notes/v57.40_Release_Notes.md if regression adds new findings.

## Pass / fail criteria

**PASS when:**
- Flags OFF batch: no quikloan output; core counts stable
- Flags ON batch: 384 quikloan rows; core counts stable
- Protected validators PASS (known baselines documented)
- UAT package complete

**FAIL when:**
- Any protected issue row count changes with flags OFF
- QuikLoan mapping drift from validation baseline
- Schema integrity failure

## Production enablement (post-regression + UAT)

Only after Regression PASS AND client UAT PASS:

1. Release authority documents UAT evidence
2. Production cut sets QLA_ENABLE_QUIKLOAN_EMIT=1 and QLA_QUIKLOAN_WRITE_OUTPUT=1 for migration run
3. Optional: remediate QuikPlan LOANINTX before cut if A/R distinction required

## Exit

Regression PASS + UAT PASS → Issue #32 closure / production enablement
Regression FAIL → Development Agent (surgical fix)
UAT FAIL on interest calc → QLAdmin vendor escalation; emit remains NO-GO
```

---

## Document index

| File | Purpose |
|------|---------|
| `Issue_32_Final_Validation_Report.md` | Validation summary |
| `Issue_32_Regression_Report.md` | Protected issue check (validation stage) |
| `Issue_32_Production_Gate_Status.md` | Emit controls |
| `Issue_32_Sample_Policy_Validation.md` | UAT trace reference |

---

## Required conclusion

| Question | Answer |
|----------|--------|
| Validation PASS? | **Yes** |
| Production emit enabled? | **No** |
| Route next? | **Regression & Deployment Agent** |
| Client UAT required? | **Yes** — 010331768C interest calc |

---

**Stop point:** Route to Regression & Deployment Agent. Do not enable production emit in this task.
