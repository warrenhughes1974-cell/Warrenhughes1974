# Issue #32 — QuikLoan Field Mapping Final (As Implemented)

**Version:** 1.2 (implemented)  
**Engine:** v57.40  
**Status:** Development complete — pending Validation Agent  
**Authority:** `Issue_32_Approved_Field_Mapping.md` + `quikloan_derivation_rules.json` + `qla_core/quikloan_converter.py`  
**Generated:** 2026-06-29

---

## 1. Scope

| Item | Value |
|------|-------|
| Source | `PLOAN` (`PLOAN_LoanInformation_Extract_20260530.csv`) |
| Target | `QuikLoan` (`quikloan.csv`) |
| Key | `MPOLICY` (one row per policy) |
| Interest calculation | **QLAdmin** — converter sets MLOANACCR=0.00 |

---

## 2. Row selection (implemented)

1. Exclude invalid/separator rows (1 excluded in May 2026 extract)
2. Sort by `POLICY_NUMBER` using `ACCRUAL_DATE`, `LAST_CHG_DATE`, `LAST_CHG_TIME`
3. Take **last row** per policy
4. Emit if `LOAN_BALANCE ≠ 0` and `MLOANDATE` (ACCRUAL_DATE) present
5. `emit_zero_balance_loans: false` — zero-balance policies audited, not emitted

---

## 3. Final field mapping

| QuikLoan Field | Type | Source / Rule | Transform | Implemented |
|----------------|------|---------------|-----------|-------------|
| **MPOLICY** | C(10) | `PLOAN.POLICY_NUMBER` | `Master_Crosswalk` → QLAdmin format | ✅ |
| **MLOANPRIN** | N(10,2) | `PLOAN.LOAN_BALANCE` | Latest row, 2 dp | ✅ |
| **MLOANBAL** | N(10,2) | `PLOAN.LOAN_BALANCE` | Gross balance; no UI interest subtraction | ✅ |
| **MLOANINT** | N(5,2) | `PLOAN.INTEREST_RATE × 100` | `AS_PERCENT` | ✅ |
| **MLOANINTX** | C(1) | QuikPlan `LOANINTX` via plan join; fallback `A` | Normalize A/R only | ✅ |
| **MLOANIDT** | D(8) | `PLOAN.ACCRUAL_DATE` | `YYYYMMDD` | ✅ |
| **MLOANDATE** | D(8) | `PLOAN.ACCRUAL_DATE` | `YYYYMMDD` | ✅ |
| **MLOANACCR** | N(10,2) | Constant `0.00` | `ZERO_AT_CONVERSION` | ✅ |
| **MLOANBILL** | N(10,2) | Constant `0.00` | Config default | ✅ |

---

## 4. Config keys (`quikloan_derivation_rules.json` v1.2)

| Key | Value |
|-----|-------|
| `mloanint_scale` | `AS_PERCENT` |
| `mloanprin_source` | `LOAN_BALANCE` |
| `mloanbal_source` | `LOAN_BALANCE` |
| `mloanaccr_source` | `ZERO_AT_CONVERSION` |
| `mloanintx_source` | `QUIKPLAN_LOANINTX` |
| `mloanintx_default` | `A` |
| `mloanidt_precedence` | `["ACCRUAL_DATE", "LAST_REPAY_DATE", "CAPITALIZED_DATE"]` |
| `mloandate_source` | `ACCRUAL_DATE` |
| `mloanbill_default` | `0.00` |
| `emit_zero_balance_loans` | `false` |
| `hold_missing_mloandate` | `true` |

---

## 5. Fields explicitly not mapped

| Source | Reason |
|--------|--------|
| `ACCRUED_INT_AMT` | Always 0.00 in extract; QLAdmin calculates |
| LifePRO UI Interest (~18.19 on trace policy) | Not in PLOAN; QLAdmin responsibility |
| `INTEREST_TYPE` (100% F) | Not MLOANINTX |
| `INT_METHOD` (100% D) | Not Advance/Arrears in extract |
| `ORIG_LOAN_AMOUNT` | Historical; not screen Principal |

---

## 6. MLOANINTX implementation note

- Join: PLOAN `PLAN_CODE` → QuikPlan `PLAN` → `LOANINTX`
- Valid values: `A`, `R` (after normalization)
- **Fleet finding:** Staged QuikPlan UAT file has `LOANINTX=22` for all plans → **913/913 policies use fallback `A`**
- Audit: `plan_analysis/phase_l1_quikloan/mloanintx_fallback_audit.csv`
- PLOAN `INTEREST_TYPE` / `INT_METHOD` are **not** used (documented in `unresolved_mloanintx.csv`)

---

## 7. Trace policy — expected vs actual

Policy `9010331768` → `010331768C`

| Field | Expected | Actual | Match |
|-------|--------:|-------:|:-----:|
| MLOANPRIN | 3707.11 | 3707.11 | ✅ |
| MLOANBAL | 3707.11 | 3707.11 | ✅ |
| MLOANINT | 5.00 | 5.00 | ✅ |
| MLOANINTX | A | A | ✅ |
| MLOANIDT | 20250725 | 20250725 | ✅ |
| MLOANDATE | 20250725 | 20250725 | ✅ |
| MLOANACCR | 0.00 | 0.00 | ✅ |
| MLOANBILL | 0.00 | 0.00 | ✅ |

---

## 8. Fleet expectations (May 2026 extract)

| Metric | Value |
|--------|------:|
| Emit rows | 384 |
| Unique MPOLICY | 384 |
| MLOANINT values | 5.00, 7.40 only |
| MLOANINTX values | A only (all fallback) |
| MLOANACCR | 0.00 all rows |
| MLOANBILL | 0.00 all rows |
| MLOANIDT/MLOANDATE blank in emit | 0 |

---

**Mapping frozen at v1.2 for Validation Agent review. No further mapping changes without SME re-approval.**
