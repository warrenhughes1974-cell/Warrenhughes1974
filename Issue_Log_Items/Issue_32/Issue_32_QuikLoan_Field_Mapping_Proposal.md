# Issue #32 — QuikLoan Field Mapping Proposal

**Status:** Proposed — **not finalized** (pending PLOAN profile + SME confirmation)  
**Baseline:** Phase L1 staging config v1.0  
**Generated:** 2026-06-29  
**Source:** `PLOAN_LoanInformation_Extract_20260530.csv`  
**Target:** QLAdmin `QuikLoan` (index `QuikLoan.ntx`, key `MPOLICY`)

---

## 1. Target Schema

| Field | Type | Length | QLAdmin description |
|-------|------|-------:|---------------------|
| MPOLICY | Character | 10 | Policy number |
| MLOANPRIN | Numeric | 10.2 | Loan principal |
| MLOANBAL | Numeric | 10.2 | Loan balance |
| MLOANINT | Numeric | 5.2 | Loan interest rate |
| MLOANINTX | Character | 1 | Interest type: A=advance, R=arrears |
| MLOANIDT | Date | 8 | Interest paid-to date |
| MLOANDATE | Date | 8 | Loan balance date |
| MLOANACCR | Numeric | 10.2 | Accrued interest |
| MLOANBILL | Numeric | 10.2 | Billing loan payment |

**Repo schema:** `qla_core/schema_constants.py` → `QUIKLOAN_SCHEMA` (field order above).

**Naming note:** Intake templates may label interest paid-to date as `MLOANDT`. The implemented and documented QLAdmin field is **`MLOANIDT`**.

---

## 2. Row Selection (Pre-Mapping)

Before field mapping, reduce PLOAN history to one row per policy:

| Step | Rule |
|------|------|
| 1 | Exclude invalid rows: blank/dash `POLICY_NUMBER`, non-numeric `LOAN_BALANCE` |
| 2 | Parse dates: `ACCRUAL_DATE`, `LAST_CHG_DATE`, `LAST_CHG_TIME`, `LAST_REPAY_DATE`, `CAPITALIZED_DATE`, `INT_START_DATE` |
| 3 | Sort per `POLICY_NUMBER` by `ACCRUAL_DATE`, `LAST_CHG_DATE`, `LAST_CHG_TIME` (descending intent via tail-1) |
| 4 | Take **latest row** per policy |
| 5 | Classify: `ACTIVE_CANDIDATE` if `LOAN_BALANCE ≠ 0`; else `ZERO_BALANCE_HOLD` |
| 6 | Emit filter (staging default): include `ACTIVE_CANDIDATE` only; require `MLOANDATE`; require `MLOANINT` |

Config reference: `plan_governance/config/quikloan_derivation_rules.json`

---

## 3. Field Mapping Table

| QuikLoan field | Proposed LifePRO source | Staging value (v1.0) | Confidence | SME decision needed |
|----------------|-------------------------|----------------------|------------|---------------------|
| **MPOLICY** | `POLICY_NUMBER` | Master_Crosswalk → QLAdmin format (e.g. `9010331768` → `010331768C`) | **High** | No |
| **MLOANPRIN** | `ORIG_LOAN_AMOUNT` **or** `LOAN_BALANCE` | Currently **`LOAN_BALANCE`** | **Low** | **Yes** — see §4 |
| **MLOANBAL** | `LOAN_BALANCE` | Latest snapshot balance | **High** | Confirm zero-balance emit policy |
| **MLOANINT** | `INTEREST_RATE` | Raw decimal string (`.0500` → `0.05`) | **Medium** | **Yes** — scale §5 |
| **MLOANINTX** | `INTEREST_TYPE` | **Blank** (default "") | **Low** | **Yes** — all source = `F` §6 |
| **MLOANIDT** | `LAST_REPAY_DATE` → `CAPITALIZED_DATE` | First non-blank in precedence order | **Medium** | **Yes** — 12 blanks in emit §7 |
| **MLOANDATE** | `ACCRUAL_DATE` | Accrual / valuation date of latest snapshot | **High** | Confirm vs `INT_START_DATE` |
| **MLOANACCR** | `ACCRUED_INT_AMT` | Always `0.00` in current extract | **High** (value) | Confirm if non-zero expected in production |
| **MLOANBILL** | *(none in PLOAN)* | Config default `0.00` | **Low** | **Yes** — source TBD §8 |

---

## 4. MLOANPRIN — Principal Definition

### Candidates

| Source field | Meaning in PLOAN | Latest-row observation |
|--------------|------------------|------------------------|
| `ORIG_LOAN_AMOUNT` | Opening principal for **this accrual row** | Changes each history row |
| `LOAN_BALANCE` | Current outstanding balance | Matches `ORIG + LOAN_AMT_ADDED` |
| `ORIG_LOAN_AMOUNT` (first loan row) | Original loan at inception | Requires history scan — not implemented |
| `LOAN_BALANCE − ACCRUED_INT_AMT` | Principal net of accrued int | Equivalent to balance when accrual = 0 |

### Staging decision (interim)

Phase L1 sets **`MLOANPRIN = MLOANBAL = LOAN_BALANCE`** for simplicity. All 913 latest rows flagged for BA review.

### Profile evidence

- `ORIG_LOAN_AMOUNT + LOAN_AMT_ADDED = LOAN_BALANCE` on **100%** of latest rows  
- On active loans, `ORIG_LOAN_AMOUNT` on latest row is the **row-open principal**, not original loan at policy inception  

**Recommendation:** SME must define QLAdmin "Loan principal" semantics before production. If QLAdmin expects **original loan at issue**, mapping requires first-history-row logic or a different LifePRO field.

---

## 5. MLOANINT — Interest Rate Scale

### Source distribution (latest row)

| Raw `INTEREST_RATE` | Policies |
|--------------------|--------:|
| .0740 | 715 |
| .0500 | 198 |

### Scale options

| Option | `.0500` loads as | QLAdmin N(5,2) fit |
|--------|-----------------|-------------------|
| A — Decimal | 0.05 | Valid if QLAdmin stores decimal rate |
| B — Percent | 5.00 | Valid if QLAdmin stores whole percent |
| C — Basis points | 500.00 | Unlikely — exceeds N(5,2) |

Staging uses **`mloanint_scale: UNRESOLVED_REVIEW`** — emits small decimal without ×100.

**Cross-check:** `QuikPlSt.MLOANINT` and plan `LOANINT` on QuikPlan may provide plan-default rate for validation (separate analysis).

---

## 6. MLOANINTX — Interest Type Mapping

### QLAdmin allowed values

| Code | Meaning |
|------|---------|
| A | Advance (interest due in advance) |
| R | Arrears (interest due in arrears) |

### LifePRO source

| `INTEREST_TYPE` | Policies (latest) |
|-----------------|------------------:|
| F | 913 |

`F` = **fixed rate** in LifePRO — **not** equivalent to QLAdmin A/R advance/arrears timing.

### Proposed mapping (pending SME)

| LifePRO | Proposed QLAdmin | Status |
|---------|------------------|--------|
| F | *(blank)* or plan-default `LOANINTX` | **Unresolved** |
| A | A | No source rows |
| R | R | No source rows |

**Do not** map `F → A` or `F → R` without written BA approval.

`INT_METHOD = D` (daily) has no QuikLoan target — document only.

---

## 7. MLOANIDT — Interest Paid-To Date

### Staging precedence

1. `LAST_REPAY_DATE` (if valid)  
2. `CAPITALIZED_DATE` (if valid)  
3. Blank

### Profile gaps (384 emit candidates)

| Condition | Count |
|-----------|------:|
| Valid `MLOANIDT` populated | 372 |
| Blank `MLOANIDT` | 12 |

Blank cases have active balance but no repay or capitalized date on latest row (e.g. `010381745C` balance $7,199.96).

### Alternative candidates (not implemented)

| Field | Use case |
|-------|----------|
| `INT_START_DATE` | Interest period start |
| `ACCRUAL_DATE` | Same as balance date — may duplicate `MLOANDATE` |
| `LAST_REPAY_DATE` from prior history row | Requires history logic |

**Recommendation:** SME defines paid-to semantics. If blank is acceptable for QLAdmin, relax validation; else add fallback rule.

---

## 8. MLOANDATE — Loan Balance Date

### Staging source

**`ACCRUAL_DATE`** of the selected latest snapshot.

### Validation

- Required for emit (`hold_missing_mloandate: true`)  
- 1 policy blocked: `9011190668` ($621.78 balance, blank accrual date)

### Alternatives

| Field | When to use |
|-------|-------------|
| `INT_START_DATE` | If accrual date unreliable |
| `LAST_CHG_DATE` | Last maintenance date |

---

## 9. MLOANACCR — Accrued Interest

### Mapping

**`ACCRUED_INT_AMT`** → `MLOANACCR`

### Profile

Zero on **all** 93,857 valid rows and all 913 latest rows. LifePRO appears to capitalize interest into `LOAN_BALANCE` via `LOAN_AMT_ADDED` rather than maintain separate accrued interest in PLOAN.

**Emit:** `0.00` for all candidates — structurally correct for this extract; confirm against QLAdmin loan screen expectations.

---

## 10. MLOANBILL — Billing Loan Payment

### Mapping

**No PLOAN source identified.**

Staging: **`0.00`** via `mloanbill_default`.

### Possible future sources (investigation only)

| Source | Notes |
|--------|-------|
| PACTG 0413 Loan Payment | Transaction amount — not snapshot |
| Billing system export | Not in current LifePRO ZIP |
| QLAdmin plan default | May be computed post-load |

**Recommendation:** Confirm with SME whether `MLOANBILL` is required at conversion or populated by QLAdmin billing cycle.

---

## 11. Fields Explicitly Not Mapped

| PLOAN field | Reason |
|-------------|--------|
| `LOAN_AMT_ADDED` | Movement delta — absorbed into balance selection |
| `CAPITALIZED_AMOUNT` | Event detail — no QuikLoan field |
| `LAST_REPAY_AMOUNT` | No QuikLoan field |
| `TAXABLE_AMOUNT` | No QuikLoan field |
| `SPEC_CLS_*` | All zero — no target |
| `STATUS_CODE`, `TYPE_CODE` | Selection/filter only — not stored in QuikLoan |
| `PLAN_CODE` | Policy context via quikmstr |
| `ACTG_*`, `LOAN_KEY0`, `ROW_COLUMN` | Operational / extract metadata |

---

## 12. PACTG Relationship

`PACTG` 04xx Borrowed Money transactions (0411 principal, 0412 interest capitalized, 0413 payment, etc.) are **not** used to derive QuikLoan balances in Phase L1.

| Role | Usage |
|------|-------|
| PLOAN | **Authoritative snapshot** for QuikLoan emit |
| PACTG | Optional reconciliation / loan history (future) |

Phase 22C held 3,851 loan accounting rows from QUIKCLMS — those policies overlap the loan fleet but are a **separate domain**.

---

## 13. Proposed Production Mapping (Conditional)

**If** SME confirms staging assumptions:

```
MPOLICY   ← crosswalk(POLICY_NUMBER)
MLOANPRIN ← LOAN_BALANCE          [pending: may change to ORIG at inception]
MLOANBAL  ← LOAN_BALANCE
MLOANINT  ← INTEREST_RATE         [pending: scale confirmation]
MLOANINTX ← ""                    [pending: plan default or A/R rule]
MLOANIDT  ← coalesce(LAST_REPAY_DATE, CAPITALIZED_DATE)  [pending: fallback rule]
MLOANDATE ← ACCRUAL_DATE
MLOANACCR ← ACCRUED_INT_AMT       [0.00 in current fleet]
MLOANBILL ← 0.00                  [pending: source identification]
```

**Emit scope:** Latest row, `LOAN_BALANCE ≠ 0`, valid `ACCRUAL_DATE`, valid `INTEREST_RATE`, unique `MPOLICY`.

---

## 14. Implementation Reference (Do Not Execute)

When authorized:

- Module: `qla_core/quikloan_converter.py`  
- Rules: `plan_governance/config/quikloan_derivation_rules.json`  
- Enable: `QLA_ENABLE_QUIKLOAN_EMIT=1`, optionally `QLA_QUIKLOAN_WRITE_OUTPUT=1`  
- Version bump: `app.py` when integrating default batch emit

---

**Status:** Mapping proposal complete. **Finalize only after SME gate PASS.**
