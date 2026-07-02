# Issue #32 — Development Validation Results

**Issue:** #32 Policy Loan Conversion  
**Engine:** v57.40  
**Mapping:** v1.2  
**Date:** 2026-06-29  
**Validator:** `tools/validators/validate_quikloan_issue32.py`  
**Evidence JSON:** `Issue_32_Validation_Evidence.json`

---

## 1. Overall result

| Field | Value |
|-------|-------|
| **Overall** | **PASS** |
| Checks run | 17 |
| Failed | 0 |
| emit_passed | 384 |
| emit_exceptions | 529 |

---

## 2. Fleet statistics

| Metric | Value |
|--------|------:|
| raw_rows | 93,858 |
| valid_rows | 93,857 |
| excluded_placeholder_rows | 1 |
| latest_policies | 913 |
| mapped_rows | 913 |
| emit_passed | 384 |
| emit_exceptions | 529 |
| zero_balance_held | 528 |
| mloanintx_fallback_count | 913 |
| quikmstr_orphan_rows | 0 |
| duplicate_mpolicy_in_emit | 0 |

---

## 3. Check results

| Check | Status | Detail |
|-------|--------|--------|
| trace_9010331768_MLOANPRIN | PASS | expected=3707.11 got=3707.11 |
| trace_9010331768_MLOANBAL | PASS | expected=3707.11 got=3707.11 |
| trace_9010331768_MLOANINT | PASS | expected=5.00 got=5.00 |
| trace_9010331768_MLOANINTX | PASS | expected=A got=A |
| trace_9010331768_MLOANIDT | PASS | expected=20250725 got=20250725 |
| trace_9010331768_MLOANDATE | PASS | expected=20250725 got=20250725 |
| trace_9010331768_MLOANACCR | PASS | expected=0.00 got=0.00 |
| trace_9010331768_MLOANBILL | PASS | expected=0.00 got=0.00 |
| emit_row_count | PASS | rows=384 |
| no_duplicate_mpolicy | PASS | |
| mloanaccr_all_zero | PASS | |
| mloanbill_all_zero | PASS | |
| mloanint_rates | PASS | rates=['5.00', '7.40'] |
| mloanintx_ar | PASS | values=['A'] |
| mloandate_populated | PASS | |
| mloanidt_populated | PASS | |
| zero_balance_excluded | PASS | held=528 |

---

## 4. Commands executed

```powershell
$env:QLA_PLOAN_PATH = "QLA_Migration\Source\PLOAN_LoanInformation_Extract_20260530.csv"
$env:QLA_QUIKPLAN_PATH = "plan_governance\staged\uat\quikplan_staged.csv"
$env:QLA_QUIKMSTR_PATH = "QLA_Migration\Output\quikmstr.csv"

python plan_analysis/phase_l1_quikloan/quikloan_runner.py
python tools/validators/validate_quikloan_issue32.py
```

---

## 5. Fleet checks (required)

| Requirement | Result |
|-------------|--------|
| One row per MPOLICY | ✅ 384 unique |
| Expected eligible count (~384) | ✅ 384 |
| No duplicate MPOLICY | ✅ |
| Latest non-zero loans only | ✅ 385 non-zero latest; 1 blocked by date |
| Zero-balance latest excluded | ✅ 528 held |
| Interest rates 5.00 or 7.40 | ✅ |
| Dates populated in emit | ✅ |
| MLOANACCR = 0.00 all rows | ✅ |
| MLOANBILL = 0.00 all rows | ✅ |
| MLOANINTX fallback documented | ✅ 913 rows in audit CSV |

---

## 6. Known exceptions (expected)

| Item | Detail |
|------|--------|
| Blocked policy 9011190668 | MISSING_MLOANDATE — ACCRUAL_DATE blank |
| MLOANINTX all A | QuikPlan LOANINTX=22 invalid fleet-wide |
| Zero-balance emit | Disabled by design (OD-32D deferred) |

---

## 7. Not in scope (Development stage)

- Formal Validation Agent sign-off
- Regression Agent protected-issue suite
- QLAdmin load UAT for interest calculation
- Production enablement of `QLA_ENABLE_QUIKLOAN_EMIT`

---

**Development validation: PASS — proceed to Validation Agent.**
