# Issue #32 — Approved Field Mapping

**Version:** 1.2  
**Status:** **Approved for Development** (Conditional PASS)  
**Authority:** Manual/business guidance + screenshot evidence (9010331768) + Dependency Gate  
**Generated:** 2026-06-29  
**Engine target:** v57.40+ (surgical `quikloan_converter` + derivation rules)

---

## 1. Scope

| Item | Value |
|------|-------|
| Source table | `PLOAN` (`PLOAN_LoanInformation_Extract_*.csv`) |
| Target table | `QuikLoan` (key `MPOLICY`) |
| Row grain | One row per policy — latest PLOAN snapshot |
| Emit filter (default) | `LOAN_BALANCE ≠ 0` unless config changed |
| Interest calculation | **QLAdmin** — not converter |

---

## 2. Row Selection (Unchanged)

1. Exclude invalid/separator rows  
2. Sort per `POLICY_NUMBER` by `ACCRUAL_DATE`, `LAST_CHG_DATE`, `LAST_CHG_TIME`  
3. Take **last row** per policy  
4. Emit if `LOAN_BALANCE ≠ 0` and required fields present (config)

---

## 3. Approved Mapping

| QuikLoan Field | Type | Approved Source / Rule | Transform | Notes |
|----------------|------|----------------------|-----------|-------|
| **MPOLICY** | C(10) | `PLOAN.POLICY_NUMBER` | Master_Crosswalk → QLAdmin format | e.g. `9010331768` → `010331768C` |
| **MLOANPRIN** | N(10,2) | `PLOAN.LOAN_BALANCE` | Latest row, 2 dp | Gross loan principal/balance per manual |
| **MLOANBAL** | N(10,2) | `PLOAN.LOAN_BALANCE` | Latest row, 2 dp | Same as MLOANPRIN; QLAdmin calculates net/display |
| **MLOANINT** | N(5,2) | `PLOAN.INTEREST_RATE × 100` | `AS_PERCENT` | `.0500`→`5.00`; `.0740`→`7.40` |
| **MLOANINTX** | C(1) | **QuikPlan `LOANINTX`** via policy plan; fallback **`A`** | Normalize A/R only | See MLOANINTX review; not PLOAN columns |
| **MLOANIDT** | D(8) | **`PLOAN.ACCRUAL_DATE`** | `YYYYMMDD` | Interest paid-to / last accrued date |
| **MLOANDATE** | D(8) | **`PLOAN.ACCRUAL_DATE`** | `YYYYMMDD` | Loan balance as-of date |
| **MLOANACCR** | N(10,2) | **Constant `0.00`** | Fixed | QLAdmin calculates interest |
| **MLOANBILL** | N(10,2) | **Constant `0.00`** | Fixed | No PLOAN source |

---

## 4. Fields Explicitly Not Mapped

| PLOAN / other | Reason |
|---------------|--------|
| `ACCRUED_INT_AMT` | Always 0.00 in extract; QLAdmin calculates |
| `ORIG_LOAN_AMOUNT` | Row-open principal; not LifePRO screen Principal |
| `INTEREST_TYPE` (F) | Fixed-rate label — not MLOANINTX |
| `INT_METHOD` (D) | Not Advance/Arrears in extract |
| `LOAN_AMT_ADDED` | History delta — absorbed in balance |
| LifePRO UI Interest | Not converted |

---

## 5. Config Targets (`quikloan_derivation_rules.json`)

When Development executes, update to:

| Key | Approved value |
|-----|----------------|
| `mloanint_scale` | `AS_PERCENT` |
| `mloanprin_source` | `LOAN_BALANCE` |
| `mloanbal_source` | `LOAN_BALANCE` |
| `mloanaccr_source` | `ZERO_AT_CONVERSION` *(or fixed 0.00 default)* |
| `mloanintx_source` | `QUIKPLAN_LOANINTX` |
| `mloanintx_default` | `A` |
| `mloanidt_precedence` | `["ACCRUAL_DATE", "LAST_REPAY_DATE", "CAPITALIZED_DATE"]` |
| `mloandate_source` | `ACCRUAL_DATE` |
| `mloanbill_default` | `0.00` |
| `emit_zero_balance_loans` | `false` *(unchanged pending OD-32D)* |

---

## 6. Expected Output — Trace Policy 9010331768

| Field | Approved emit value |
|-------|--------------------:|
| MPOLICY | 010331768C |
| MLOANPRIN | 3707.11 |
| MLOANBAL | 3707.11 |
| MLOANINT | 5.00 |
| MLOANINTX | A |
| MLOANIDT | 20250725 |
| MLOANDATE | 20250725 |
| MLOANACCR | 0.00 |
| MLOANBILL | 0.00 |

**Post-load UAT:** QLAdmin should calculate/display interest consistent with LifePRO (~18.19 advance unearned semantics per manual).

---

## 7. Fleet Expectations (May 2026 extract)

| Metric | Value |
|--------|------:|
| Emit candidates (default rules) | ~384 |
| Unique MPOLICY | 384 (no duplicates) |
| MLOANIDT blank (ACCRUAL-first) | 0 |
| MLOANACCR | 0.00 all rows |
| Rate mix | 5.00% (198 policies) / 7.40% (715 policies) at latest row |

---

## 8. Sign-Off Record

| Decision | Authority | Date | Status |
|----------|-----------|------|--------|
| MLOANACCR = 0; QLAdmin calc | Manual / business | 2026-06-29 | **Approved** |
| MLOANPRIN/MLOANBAL = LOAN_BALANCE | Manual + screenshot | 2026-06-29 | **Approved** |
| MLOANINT AS_PERCENT | Screenshot | 2026-06-29 | **Approved** |
| MLOANIDT/MLOANDATE = ACCRUAL_DATE | Screenshot + fleet profile | 2026-06-29 | **Approved** |
| MLOANINTX fallback A | Manual + rulebook + screenshot | 2026-06-29 | **Approved (conditional)** |
| Zero-balance emit | — | — | **Deferred** |

---

**Approved for Development** under Issue #32 Dependency Gate Conditional PASS.
