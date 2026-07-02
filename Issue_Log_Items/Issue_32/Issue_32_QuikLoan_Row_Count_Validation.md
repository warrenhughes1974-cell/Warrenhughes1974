# Issue #32 — QuikLoan Row Count Validation

**Engine:** v57.40  
**Extract:** `PLOAN_LoanInformation_Extract_20260530.csv`  
**Output:** `QLA_Migration/Output/quikloan.csv`  
**Date:** 2026-06-29  
**Result:** **PASS**

---

## 1. PLOAN population

| Metric | Expected | Actual | Status |
|--------|--------:|-------:|:------:|
| Raw PLOAN rows | 93,858 | 93,858 | ✅ |
| Valid data rows | 93,857 | 93,857 | ✅ |
| Excluded placeholder/separator | 1 | 1 | ✅ |
| Unique policies (latest row) | 913 | 913 | ✅ |

---

## 2. Emit population

| Metric | Expected | Actual | Status |
|--------|--------:|-------:|:------:|
| **Emit passed** | **384** | **384** | ✅ |
| Latest non-zero balance | 385 | 385 | ✅ |
| Blocked (missing date) | 1 | 1 | ✅ |
| Zero-balance held | 528 | 528 | ✅ |
| **Total reconciliation** | **913** | **384 + 528 + 1 = 913** | ✅ |

**Formula:** `emit_passed + zero_balance_held + blocked = latest_policies`

---

## 3. Integrity checks

| Check | Expected | Actual | Status |
|-------|----------|--------|:------:|
| Duplicate MPOLICY in emit | 0 | 0 | ✅ |
| quikmstr orphan rows | 0 | 0 | ✅ |
| Emit rows in quikmstr | 384/384 | 384/384 | ✅ |
| quikloan.csv row count | 384 | 384 | ✅ |
| Converter vs CSV match | identical | identical | ✅ |

---

## 4. Blocked policy detail

| Field | Value |
|-------|-------|
| SOURCE_POLICY | 9011190668 |
| MPOLICY | 011190668C |
| LOAN_BALANCE | 621.78 |
| EXCEPTION_REASON | MISSING_MLOANDATE |
| ACCRUAL_DATE | blank on latest row |

Held in `quikloan_emit_exceptions.csv` — not in `quikloan.csv`.

---

## 5. Zero-balance exclusion

| Metric | Value |
|--------|------:|
| Count | 528 |
| Reason code | ZERO_BALANCE_HELD |
| Audit file | `zero_balance_loan_policies.csv` |
| In emit CSV | No |

Example: `9010300689` → `010300689C` — latest LOAN_BALANCE = 0.00, held not emitted.

---

## 6. Interest rate distribution (emit)

| MLOANINT | Policies in emit |
|----------|-----------------:|
| 5.00 | 69 |
| 7.40 | 315 |
| **Total** | **384** |

*(Derived from emit CSV — aligns with non-zero subset of fleet rate mix.)*

---

## 7. Validation sources

| Source | Path |
|--------|------|
| Emit CSV | `QLA_Migration/Output/quikloan.csv` |
| Staging emit | `plan_analysis/phase_l1_quikloan/quikloan_emit_candidates.csv` |
| Exceptions | `plan_analysis/phase_l1_quikloan/quikloan_emit_exceptions.csv` |
| Validator JSON | `Issue_32_Validation_Evidence.json` |

---

**Row count validation: PASS**
