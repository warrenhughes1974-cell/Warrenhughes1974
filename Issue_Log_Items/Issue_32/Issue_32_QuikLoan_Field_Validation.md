# Issue #32 — QuikLoan Field Validation

**Engine:** v57.40  
**Mapping:** v1.2  
**Emit rows validated:** 384  
**Date:** 2026-06-29  
**Result:** **PASS** (0 field mapping failures)

---

## 1. Schema validation

| Check | Result |
|-------|--------|
| Columns match `QUIKLOAN_SCHEMA` | ✅ PASS |
| Column order | MPOLICY, MLOANPRIN, MLOANBAL, MLOANINT, MLOANINTX, MLOANIDT, MLOANDATE, MLOANACCR, MLOANBILL |
| Batch CSV matches converter output | ✅ PASS |

---

## 2. Field rules — fleet-wide (384 rows)

Validation method: join `quikloan.csv` → mapping trace → PLOAN latest row; compare each field per v1.2 rules.

| Field | Rule | Failures | Status |
|-------|------|--------:|:------:|
| MLOANPRIN | = LOAN_BALANCE (2 dp) | 0 | ✅ |
| MLOANBAL | = LOAN_BALANCE (gross) | 0 | ✅ |
| MLOANINT | = INTEREST_RATE × 100 | 0 | ✅ |
| MLOANINTX | A or R (plan or fallback) | 0 | ✅ |
| MLOANIDT | = ACCRUAL_DATE (YYYYMMDD) | 0 | ✅ |
| MLOANDATE | = ACCRUAL_DATE (YYYYMMDD) | 0 | ✅ |
| MLOANACCR | = 0.00 | 0 | ✅ |
| MLOANBILL | = 0.00 | 0 | ✅ |

**Evidence:** `Issue_32_Formal_Field_Validation.json` → `field_mapping_failures: 0`

---

## 3. Value domain checks

| Field | Allowed values (emit) | Actual | Status |
|-------|----------------------|--------|:------:|
| MLOANINT | 5.00, 7.40 | 5.00, 7.40 only | ✅ |
| MLOANINTX | A, R | A only (all fallback) | ✅ |
| MLOANACCR | 0.00 | 0.00 all rows | ✅ |
| MLOANBILL | 0.00 | 0.00 all rows | ✅ |
| MLOANIDT | non-blank | 384/384 populated | ✅ |
| MLOANDATE | non-blank | 384/384 populated | ✅ |

---

## 4. Explicit non-rules verified

| Prohibited behavior | Verified absent |
|--------------------|-----------------|
| MLOANBAL = LOAN_BALANCE − UI interest | ✅ Not applied |
| MLOANACCR from PLOAN ACCRUED_INT_AMT | ✅ Not applied (always 0.00) |
| MLOANINTX from PLOAN INTEREST_TYPE / INT_METHOD | ✅ Not applied |
| LifePRO accrued interest calculation | ✅ Not in converter output |

---

## 5. MLOANINT scale examples

| INTEREST_RATE (PLOAN) | MLOANINT (emit) | Status |
|----------------------|-----------------|:------:|
| .0500 | 5.00 | ✅ |
| .0740 | 7.40 | ✅ |

---

## 6. MLOANINTX resolution

| Metric | Value |
|--------|------:|
| Policies with valid QuikPlan A/R | 0 |
| Fallback to default A | 913 (mapped population) |
| Emit rows with MLOANINTX=A | 384 |

All emit rows use fallback `A` because staged QuikPlan `LOANINTX=22` is invalid — documented in `mloanintx_fallback_audit.csv`.

---

## 7. Validator cross-check

`validate_quikloan_issue32.py` field-related checks:

| Check | Status |
|-------|--------|
| mloanaccr_all_zero | PASS |
| mloanbill_all_zero | PASS |
| mloanint_rates | PASS |
| mloanintx_ar | PASS |
| mloandate_populated | PASS |
| mloanidt_populated | PASS |

---

**Field validation: PASS — all 384 emit rows conform to v1.2 mapping.**
