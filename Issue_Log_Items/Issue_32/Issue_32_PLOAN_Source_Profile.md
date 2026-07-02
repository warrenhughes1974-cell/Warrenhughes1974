# Issue #32 — PLOAN Source Profile

**Source file:** `QLA_Migration/Source/PLOAN_LoanInformation_Extract_20260530.csv`  
**Profile run:** 2026-06-29 (Phase L1 runner + extended analytics)  
**Engine:** v57.39 / `qla_core/quikloan_converter.py`

---

## 1. File Structure

### Header fields (34 columns)

```
COMPANY_CODE, POLICY_NUMBER, ACCRUAL_DATE, STATUS_CODE, TYPE_CODE, PLAN_CODE,
ORIG_LOAN_AMOUNT, LOAN_AMT_ADDED, LOAN_BALANCE, ACCRUED_INT_AMT, INTEREST_RATE,
INTEREST_TYPE, INT_METHOD, LAST_REPAY_DATE, LAST_REPAY_AMOUNT, CAPITALIZED_DATE,
CAPITALIZED_AMOUNT, TAXABLE_AMOUNT, SPEC_CLS_LOAN_BAL, SPEC_CLS_INT_RATE,
SPEC_CLS_CAPD_AMT, LAST_CHG_DATE, LAST_CHG_TIME, ENTRY_OPERATOR, ACTG_CNTRL_NUMBER,
BANKERS_YEAR_IND, SPEC_CLS_LOAN_CHNG, ACTG_TYPE, LOAN_BASIS, INT_START_DATE,
INT_DELAY_DAYS, LOAN_UPD_COUNT, LOAN_KEY0, ROW_COLUMN
```

LifePRO values are space-padded character fields; numeric amounts include leading spaces and decimal alignment.

---

## 2. Row Counts

| Metric | Value |
|--------|------:|
| Total rows (incl. header separator) | 93,858 |
| Valid data rows | 93,857 |
| Excluded placeholder/separator rows | 1 |
| Unique `POLICY_NUMBER` values | 913 |
| Blank / dash policy rows | 1 |

---

## 3. Balance and Amount Flags (All Valid Rows)

| Condition | Row count |
|-----------|----------:|
| `LOAN_BALANCE > 0` | 93,036 |
| `LOAN_BALANCE = 0` | 821 |
| `ACCRUED_INT_AMT > 0` | **0** |
| `ORIG_LOAN_AMOUNT > 0` | 93,190 |
| `SPEC_CLS_LOAN_BAL > 0` | **0** |

**Observation:** Accrued interest and special-class loan balances are **zero across the entire extract**. Loan economics appear fully capitalized into `LOAN_BALANCE` via `LOAN_AMT_ADDED` adjustments.

---

## 4. Latest-Row Profile (One Row Per Policy)

Selection: max(`ACCRUAL_DATE`, `LAST_CHG_DATE`, `LAST_CHG_TIME`) per policy — matches Phase L1 config.

| Metric | Value |
|--------|------:|
| Latest-row policies | 913 |
| Non-zero `LOAN_BALANCE` | 385 |
| Zero `LOAN_BALANCE` | 528 |
| `ORIG_LOAN_AMOUNT > 0` on latest row | 910 |
| `ACCRUED_INT_AMT > 0` on latest row | **0** |
| Total `LOAN_BALANCE` (all latest) | $1,554,200.67 |
| Total `LOAN_BALANCE` (non-zero latest only) | $1,554,200.67 |
| Total `ACCRUED_INT_AMT` (latest) | $0.00 |

---

## 5. STATUS_CODE Distribution

### All valid rows

| STATUS_CODE | Rows | Interpretation (LifePRO loan lifecycle) |
|-------------|-----:|----------------------------------------|
| H | 91,766 | History / superseded snapshot |
| R | 1,818 | Repayment-related |
| A | 273 | Active accrual period |

### Latest row per policy

| STATUS_CODE | Policies |
|-------------|--------:|
| H | 576 |
| A | 240 |
| R | 97 |

### Non-zero balance latest rows (385 policies)

| STATUS_CODE | Policies |
|-------------|--------:|
| A | 240 |
| R | 88 |
| H | 57 |

**Planning note:** 57 policies with non-zero balance carry latest STATUS `H` (history). Staging does **not** filter by STATUS — selection is date-driven only. SME must confirm whether STATUS `H` with non-zero balance is valid for emit.

---

## 6. TYPE_CODE Distribution

### All valid rows

| TYPE_CODE | Rows |
|-----------|-----:|
| R | 70,580 |
| A | 22,395 |
| (blank) | 882 |

### Latest row per policy

| TYPE_CODE | Policies |
|-----------|--------:|
| R | 447 |
| (blank) | 351 |
| A | 115 |

### Non-zero balance latest rows

| TYPE_CODE | Policies |
|-----------|--------:|
| R | 250 |
| A | 115 |
| (blank) | 20 |

**Interpretation:** `R` = regular accrual movement; `A` = adjustment row. Blank TYPE on 351 latest rows (mostly zero-balance closed loans) — likely post-payoff state.

---

## 7. Interest Attributes

### INTEREST_TYPE (latest row — all 913 policies)

| Value | Policies |
|-------|--------:|
| F (fixed) | 913 |

No `A` (advance) or `R` (arrears) values appear in PLOAN. QLAdmin `MLOANINTX` expects `A` or `R` — direct mapping is **not supported** without BA rule.

### INT_METHOD (latest row — all 913 policies)

| Value | Policies |
|-------|--------:|
| D | 913 |

Likely daily accrual method in LifePRO; no QLAdmin target field in QuikLoan schema.

### INTEREST_RATE (latest row)

| Raw value | Policies | Staging emit (UNRESOLVED_REVIEW) | As percent candidate |
|-----------|--------:|----------------------------------|---------------------:|
| .0740 | 715 | 0.074 | 7.40% |
| .0500 | 198 | 0.05 | 5.00% |

Missing interest rate on latest row: **0**

**Critical open question:** QLAdmin `MLOANINT` N(5,2) — should `.0500` load as `0.05`, `5.00`, or `0.50`?

---

## 8. Date Field Completeness (Latest Row)

| Field | Missing / invalid on latest row |
|-------|--------------------------------:|
| ACCRUAL_DATE | 1 |
| LAST_REPAY_DATE | 118 |
| CAPITALIZED_DATE | 586 |
| INT_START_DATE | (not separately counted; often populated) |

**ACCRUAL_DATE range (all valid rows):** 2003-09-23 to **2218-01-11** (future date outlier — data quality flag for SME)

**Blocked emit:** Policy `9011190668` — active balance $621.78 but blank `ACCRUAL_DATE` → held `MISSING_MLOANDATE`.

**MLOANIDT gap:** 12 of 384 emit candidates have blank `MLOANIDT` because both `LAST_REPAY_DATE` and `CAPITALIZED_DATE` are zero/blank on latest row.

---

## 9. Multi-Row / Duplicate Policy Analysis

| Metric | Value |
|--------|------:|
| Policies with >1 PLOAN row | 913 (100%) |
| Minimum rows per policy | 2 |
| Median rows per policy | 45 |
| Maximum rows per policy | 871 |

**Conclusion:** Multiple rows are **accrual history**, not duplicate extract errors. Each row represents a loan snapshot at `ACCRUAL_DATE` with movement via `LOAN_AMT_ADDED`.

### Principal arithmetic check

For all 913 latest rows: `ORIG_LOAN_AMOUNT + LOAN_AMT_ADDED = LOAN_BALANCE` within $0.01 — **100% match**. No `ORIG_PLUS_ADDED_NE_BALANCE` exceptions.

This supports treating `LOAN_BALANCE` as the authoritative current balance but does **not** resolve whether `MLOANPRIN` should equal balance or original principal.

### Sample history — policy 9010331768 (88 rows)

| ACCRUAL_DATE | STATUS | TYPE | LOAN_BALANCE | ORIG_LOAN_AMOUNT | LOAN_AMT_ADDED |
|--------------|--------|------|-------------:|-----------------:|---------------:|
| 20240731 | H | R | 3,847.31 | 3,658.54 | 188.77 |
| 20250724 | H | R | 4,049.80 | 3,847.31 | 202.49 |
| 20250725 | H | R | 3,847.85 | 4,049.80 | -201.95 |
| 20250725 | H | R | 3,522.25 | 3,847.85 | -325.60 |
| 20250725 | A | R | **3,707.11** | 3,522.25 | 184.86 |

Latest selected row: last line (STATUS A, balance $3,707.11).

---

## 10. quikmstr Cross-Reference

Crosswalk: `QLA_Migration/Mapping/Master_Crosswalk.csv`  
Target: `QLA_Migration/Output/quikmstr.csv`

| Check | Result |
|-------|--------|
| Latest PLOAN policies mapped to MPOLICY | 913 / 913 |
| Mapped MPOLICY exists in quikmstr | 913 / 913 |
| Active-balance policies in quikmstr | 385 / 385 |
| Orphan loan policies (not in quikmstr) | **0** |

---

## 11. Phase L1 Emit Summary (Default Rules)

Config: `plan_governance/config/quikloan_derivation_rules.json`

| Rule | Value |
|------|-------|
| `emit_zero_balance_loans` | false |
| `active_balance_rule` | LOAN_BALANCE_NE_ZERO |
| Latest-row sort | ACCRUAL_DATE, LAST_CHG_DATE, LAST_CHG_TIME |

| Outcome | Count |
|---------|------:|
| Emit candidates (`quikloan_emit_candidates.csv`) | 384 |
| Zero-balance held | 528 |
| Missing MLOANDATE blocked | 1 |
| Duplicate MPOLICY in emit | 0 |

### Emit financial totals

| Field | Total |
|-------|------:|
| Σ MLOANBAL | $1,553,578.89 |
| Σ MLOANACCR | $0.00 |

Δ vs profile total ($1,554,200.67 − $1,553,578.89 = **$621.78**) = blocked policy `9011190668`.

---

## 12. Special Class Fields

| Field | Non-zero rows (all valid) |
|-------|--------------------------:|
| SPEC_CLS_LOAN_BAL | 0 |
| SPEC_CLS_INT_RATE | (all zero in sample) |
| SPEC_CLS_CAPD_AMT | (all zero in sample) |
| SPEC_CLS_LOAN_CHNG | (all zero in sample) |

**Recommendation:** Ignore special-class fields for QuikLoan unless SME identifies a product subset requiring them. No QuikLoan target fields exist for special-class data.

---

## 13. Data Quality Flags

1. **Future ACCRUAL_DATE** — max 2218-01-11 requires SME/data-team review  
2. **STATUS H with non-zero balance** — 57 active-candidate policies  
3. **Blank TYPE_CODE** — 351 latest rows (mostly zero balance)  
4. **Blank ACCRUAL_DATE** — 1 policy blocks emit  
5. **All INTEREST_TYPE = F** — no A/R mapping path without business rule  

---

## 14. Refresh Command

```powershell
$env:QLA_PLOAN_PATH = "QLA_Migration\Source\PLOAN_LoanInformation_Extract_20260530.csv"
python plan_analysis/phase_l1_quikloan/quikloan_runner.py
```

Reports written to `plan_analysis/phase_l1_quikloan/`.
