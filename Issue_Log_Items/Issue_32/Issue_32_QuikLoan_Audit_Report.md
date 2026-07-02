# Issue #32 — QuikLoan Audit Report

**Issue:** #32 Policy Loan Conversion  
**Engine:** v57.40  
**Extract:** `PLOAN_LoanInformation_Extract_20260530.csv`  
**Generated:** 2026-06-29  
**Audit root:** `plan_analysis/phase_l1_quikloan/`

---

## 1. Summary

| Category | Count | Audit file |
|----------|------:|------------|
| **Included (emit)** | **384** | `quikloan_emit_candidates.csv` |
| **Excluded — zero balance** | **528** | `zero_balance_loan_policies.csv` / `quikloan_emit_exceptions.csv` |
| **Blocked — missing date** | **1** | `missing_invalid_dates.csv` / `quikloan_emit_exceptions.csv` |
| **MLOANINTX fallback to A** | **913** | `mloanintx_fallback_audit.csv` |
| **quikmstr orphan** | **0** | `quikmstr_orphan_audit.csv` |
| **Duplicate MPOLICY in emit** | **0** | Validator check |
| **Total latest policies** | **913** | `ploan_latest_row_selection.csv` |

**Reconciliation:** 384 + 528 + 1 = 913 ✅

---

## 2. Included policies (emit)

**File:** `quikloan_emit_candidates.csv`  
**Columns:** MPOLICY, MLOANPRIN, MLOANBAL, MLOANINT, MLOANINTX, MLOANIDT, MLOANDATE, MLOANACCR, MLOANBILL

| Check | Result |
|-------|--------|
| Row count | 384 |
| One row per MPOLICY | ✅ |
| MLOANACCR all 0.00 | ✅ |
| MLOANBILL all 0.00 | ✅ |
| MLOANINT in {5.00, 7.40} | ✅ |
| MLOANINTX in {A} | ✅ (all fallback) |
| Dates populated | ✅ |

---

## 3. Excluded — zero-balance policies

**Reason code:** `ZERO_BALANCE_HELD`  
**Rule:** `emit_zero_balance_loans: false` — latest snapshot has `LOAN_BALANCE = 0`

| Metric | Value |
|--------|------:|
| Count | 528 |
| Audit file | `zero_balance_loan_policies.csv` |
| Exception file | `quikloan_emit_exceptions.csv` (528 rows) |

Zero-balance policies retain mapped values in exception audit for traceability but are **not** written to emit CSV.

---

## 4. Blocked rows

| SOURCE_POLICY | MPOLICY | Balance | Reason | Detail |
|---------------|---------|--------:|--------|--------|
| 9011190668 | 011190668C | 621.78 | `MISSING_MLOANDATE` | Latest row ACCRUAL_DATE blank; `hold_missing_mloandate=true` |

**File:** `missing_invalid_dates.csv`  
**Impact:** 385 non-zero latest policies → 384 emit (1 blocked)

---

## 5. MLOANINTX fallback audit

**File:** `mloanintx_fallback_audit.csv`  
**Count:** 913 (all policies with PLOAN latest row)

| Finding | Detail |
|---------|--------|
| QuikPlan raw LOANINTX | `22` for all matched plans |
| Normalized valid A/R | 0 |
| Applied default | `A` (913) |
| Source column | `MLOANINTX_SOURCE=default` |

**Sample (trace policy):**

| SOURCE_POLICY | MPOLICY | PLAN | MLOANINTX | SOURCE | RAW |
|---------------|---------|------|-----------|--------|-----|
| 9010331768 | 010331768C | 960 PO | A | default | 22 |

**Note:** Fallback is expected until QuikPlan LOANINTX is corrected in plan staging. Not a converter defect.

---

## 6. quikmstr orphan audit

**File:** `quikmstr_orphan_audit.csv`  
**Rows:** 0

All 913 mapped MPOLICY values exist in `quikmstr.csv` emit set.

---

## 7. Duplicate MPOLICY prevention

Latest-row selection collapses PLOAN history to one row per `POLICY_NUMBER` before emit. Validator confirms:

- `duplicate_mpolicy_in_emit: 0`
- `emit_passed` unique MPOLICY count = 384

---

## 8. Full mapping trace

**File:** `quikloan_mapping_trace.csv` (913 rows)

Trace columns include: SOURCE_POLICY, MPOLICY, crosswalk status, plan codes, balance sources, MLOANINT scale, MLOANINTX source, PLOAN INTEREST_TYPE/INT_METHOD (informational only), emit disposition.

---

## 9. Supporting audit files

| File | Purpose |
|------|---------|
| `interest_rate_format_review.csv` | AS_PERCENT verification |
| `mloanprin_vs_balance_exceptions.csv` | Documents MLOANPRIN=MLOANBAL=LOAN_BALANCE (not net) |
| `unresolved_mloanintx.csv` | PLOAN columns not used for MLOANINTX |
| `unresolved_mloanbill.csv` | MLOANBILL has no PLOAN source |
| `missing_interest_rate.csv` | Interest rate gaps (0 in fleet) |
| `ploan_profile_summary.txt` | Fleet statistics |

---

## 10. Environment / output controls

| Control | Default | Effect |
|---------|---------|--------|
| `QLA_ENABLE_QUIKLOAN_EMIT` | off | Batch skips QuikLoan unless `=1` |
| `QLA_QUIKLOAN_WRITE_OUTPUT` | off | No `quikloan.csv` unless `=1` |

Audit CSVs are always written by `quikloan_runner.py` and batch staging path to `plan_analysis/phase_l1_quikloan/`.

---

**Audit status:** Complete for Development stage. Validation Agent to re-run and sign off.
