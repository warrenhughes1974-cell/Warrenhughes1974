# Issue #32 — QuikLoan Audit Validation

**Engine:** v57.40  
**Audit root:** `plan_analysis/phase_l1_quikloan/`  
**Date:** 2026-06-29  
**Result:** **PASS**

---

## 1. Audit reconciliation summary

| Category | Count | Audit file | Status |
|----------|------:|------------|:------:|
| Emitted loans | 384 | `quikloan_emit_candidates.csv` | ✅ |
| Zero-balance held | 528 | `zero_balance_loan_policies.csv` | ✅ |
| Blocked rows | 1 | `quikloan_emit_exceptions.csv` | ✅ |
| MLOANINTX fallback | 913 | `mloanintx_fallback_audit.csv` | ✅ |
| quikmstr orphans | 0 | `quikmstr_orphan_audit.csv` | ✅ (empty file) |
| Missing/invalid dates | 1 | `missing_invalid_dates.csv` | ✅ |
| Full mapping trace | 913 | `quikloan_mapping_trace.csv` | ✅ |

**Reconciliation:** 384 + 528 + 1 = **913** = `latest_policies` ✅

---

## 2. Exception file breakdown

**File:** `quikloan_emit_exceptions.csv` — **529 rows**

| EXCEPTION_REASON | Count | Status |
|------------------|------:|:------:|
| ZERO_BALANCE_HELD | 528 | ✅ Expected |
| MISSING_MLOANDATE | 1 | ✅ Expected (9011190668) |

---

## 3. MLOANINTX fallback audit

**File:** `mloanintx_fallback_audit.csv` — **913 rows**

| Check | Result |
|-------|--------|
| Row count = mapped population | ✅ |
| All emit policies have audit row | ✅ |
| MLOANINTX_SOURCE = default for invalid plan LOANINTX | ✅ |
| Raw QuikPlan value documented (22) | ✅ |
| Trace policy 9010331768 documented | ✅ |

Sample note field: `QuikPlan LOANINTX missing or invalid; applied mloanintx_default.`

---

## 4. quikmstr orphan audit

**File:** `quikmstr_orphan_audit.csv`

| Check | Result |
|-------|--------|
| Orphan rows | 0 |
| All 384 emit MPOLICY ∈ quikmstr | ✅ Verified independently |

---

## 5. Duplicate prevention

| Check | Source | Result |
|-------|--------|--------|
| duplicate_mpolicy_in_emit | Converter stats | 0 |
| Unique MPOLICY in emit CSV | pandas | 384 unique |
| Latest-row selection | `ploan_latest_row_selection.csv` | 913 policies, 1 row each |

---

## 6. Missing / invalid dates

**File:** `missing_invalid_dates.csv` — **1 row**

| Policy | Issue | Emit disposition |
|--------|-------|------------------|
| 9011190668 | ACCRUAL_DATE missing on latest row | Blocked — MISSING_MLOANDATE |

---

## 7. Supporting audit files (present)

| File | Purpose | Status |
|------|---------|:------:|
| `interest_rate_format_review.csv` | AS_PERCENT verification | ✅ |
| `mloanprin_vs_balance_exceptions.csv` | Gross balance documentation | ✅ |
| `unresolved_mloanintx.csv` | PLOAN cols not used | ✅ |
| `unresolved_mloanbill.csv` | MLOANBILL default only | ✅ |
| `missing_interest_rate.csv` | Rate gaps (0 in fleet) | ✅ |
| `ploan_profile_summary.txt` | Fleet stats | ✅ |
| `ploan_latest_row_selection.csv` | Latest row audit | ✅ |

---

## 8. Batch audit trail

Full batch log confirms audit refresh during QuikLoan stage:

```
QUIKLOAN Issue #32: 384 emit rows, 529 exceptions; MLOANINTX fallback=913
reports -> plan_analysis/phase_l1_quikloan
GATED OUTPUT: QLA_Migration/Output/quikloan.csv (384 rows)
```

Log: `QLA_Migration/Output/_full_batch_test_log.txt`

---

**Audit validation: PASS — all governance outputs present and reconcile to PLOAN population.**
