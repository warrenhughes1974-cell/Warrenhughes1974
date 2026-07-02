# Issue #32 — Field Mapping Revision (Post-Screenshot)

**Issue:** #32 — Policy Loan Conversion  
**Evidence:** LifePRO screenshots — policy `9010331768`  
**Prior baseline:** Phase L1 staging v1.0 / `Issue_32_QuikLoan_Field_Mapping_Proposal.md`  
**Generated:** 2026-06-29  
**Status:** Revised proposal — **pending SME sign-off on interest calculation**

---

## 1. Revision Summary

Screenshot evidence **overturns** three Phase L1 staging assumptions and **confirms** three others.

| Field | Phase L1 (v1.0) | Revised proposal (v1.1) | Change |
|-------|-----------------|---------------------------|--------|
| MLOANINT | 0.05 (UNRESOLVED_REVIEW) | **5.00** (`AS_PERCENT`) | **CHANGED** |
| MLOANPRIN | LOAN_BALANCE | **LOAN_BALANCE** (confirmed = screen Principal) | Confirmed |
| MLOANBAL | LOAN_BALANCE | **LOAN_BALANCE − MLOANACCR** | **CHANGED** |
| MLOANACCR | ACCRUED_INT_AMT (0.00) | **Calculated** — not in PLOAN | **CHANGED** |
| MLOANINTX | blank | **A** (Advance) — SME/plan default, **not** PLOAN.INT_METHOD | **CHANGED** |
| MLOANDATE | ACCRUAL_DATE | **ACCRUAL_DATE** | Confirmed |
| MLOANIDT | LAST_REPAY → CAPITALIZED | **ACCRUAL_DATE** primary; fallback LAST_REPAY → CAPITALIZED | **REFINED** |
| MLOANBILL | 0.00 | **0.00** | Unchanged |

---

## 2. Revised Field Mapping Table

| QuikLoan | Revised LifePRO source | Rule | Confidence |
|----------|------------------------|------|------------|
| **MPOLICY** | `POLICY_NUMBER` + crosswalk | Unchanged | High |
| **MLOANPRIN** | `LOAN_BALANCE` (latest row) | Gross loan principal per LifePRO Loan Values screen | **High** (screenshot) |
| **MLOANBAL** | `LOAN_BALANCE − MLOANACCR` | Net balance after accrued interest | **Medium** — depends on accrual calc |
| **MLOANINT** | `INTEREST_RATE × 100` | `.0500` → `5.00`; `.0740` → `7.40` | **High** (screenshot) |
| **MLOANINTX** | **Not PLOAN column** — default **`A`** | Advance per Loan Quotes screen; reject INT_METHOD=D mapping | **Medium** — SME fleet confirm |
| **MLOANIDT** | **`ACCRUAL_DATE`** | Matches "Last Accrued Date"; fallback chain if blank | **Medium-High** |
| **MLOANDATE** | **`ACCRUAL_DATE`** | Matches "Last Accrued Date" | **High** |
| **MLOANACCR** | **Calculated** | See §3 — not `ACCRUED_INT_AMT` | **Low** — formula TBD |
| **MLOANBILL** | Config default | `0.00` | Low |

---

## 3. MLOANACCR Calculation Gap (Critical)

### What screenshot proves

LifePRO displays **Interest = 18.19** while PLOAN **`ACCRUED_INT_AMT = 0.00`** on all 93,857 rows.

### Trace policy arithmetic

```
Principal (LOAN_BALANCE)     = 3,707.11
UI Interest                  =    18.19
Net Balance                  = 3,688.92  (= Principal − Interest)

18.19 / (3707.11 × 0.05)     ≈ 0.0981 of annual rate
0.0981 × 365                 ≈ 35.8 days
```

Consistent with **advance interest accrual** for ~36 days at 5% on gross principal.

### Candidate formulas (NOT implemented — SME must select)

| ID | Formula (conceptual) | Notes |
|----|----------------------|-------|
| F1 | `LOAN_BALANCE × INTEREST_RATE × (days_since_last_event / 365)` | Requires event date + as-of date |
| F2 | QLAdmin recalculates on load from MLOANPRIN + MLOANINT + MLOANINTX + MLOANIDT | **Preferred if QLAdmin owns calc** — emit MLOANACCR=0 |
| F3 | Pull from PACTG 0412 / loan transaction subsystem | Snapshot vs transaction mismatch risk |
| F4 | LifePRO API / secondary extract not in current ZIP | Out of scope unless client supplies |

### Recommended interim positions

| Option | MLOANACCR at conversion | MLOANBAL at conversion | Risk |
|--------|-------------------------|------------------------|------|
| **A — QLAdmin calc** | 0.00 | LOAN_BALANCE or let QLAdmin derive | Low if QLAdmin recalculates on open |
| **B — Implement F1** | calculated | LOAN_BALANCE − calculated | **High** — formula/as-of date unverified fleet-wide |
| **C — Hold** | block emit until source found | — | Safest |

**Planning recommendation:** Ask SME whether QLAdmin **recalculates** loan interest from principal/rate/dates on policy open. If yes, Option A may match production behavior despite PLOAN ACCRUED=0.

---

## 4. MLOANINTX — Revised Source Analysis

| Source tested | Fleet value | Maps to Advance? | Verdict |
|---------------|-------------|-------------------|---------|
| `PLOAN.INTEREST_TYPE` | 100% F | No — means Fixed rate | **Reject for MLOANINTX** |
| `PLOAN.INT_METHOD` | 100% D | No — not A/R | **Reject for MLOANINTX** |
| Screenshot Loan Quotes | Advance | Yes | **Evidence only** |
| QuikPlan `LOANINTX` (1960PO) | `22` | No — not A/R | **Reject until codebook** |

**Revised rule:** Set `MLOANINTX = A` via config default **`mloanintx_default: A`** after SME confirms fleet-wide advance method. Do **not** read from PLOAN `INT_METHOD` or `INTEREST_TYPE`.

---

## 5. MLOANINT — Config Change (When Authorized)

```json
"mloanint_scale": "AS_PERCENT"
```

| PLOAN raw | Revised MLOANINT |
|-----------|-----------------:|
| .0500 | 5.00 |
| .0740 | 7.40 |

---

## 6. Row Selection — Unchanged

Latest row per policy by `ACCRUAL_DATE`, `LAST_CHG_DATE`, `LAST_CHG_TIME`.

Policy 9010331768: 88 rows → latest row 224 (20250725, STATUS A) — **correct** per screenshot Principal match.

---

## 7. Phase L1 vs Revised — Trace Policy Delta

| Field | Phase L1 | Revised | Screen |
|-------|----------|---------|-------:|
| MLOANPRIN | 3,707.11 | 3,707.11 | 3,707.11 |
| MLOANBAL | 3,707.11 | 3,688.92 | 3,688.92 |
| MLOANINT | 0.05 | 5.00 | 5.00% |
| MLOANINTX | blank | A | Advance |
| MLOANACCR | 0.00 | 18.19 or 0* | 18.19 |
| MLOANDATE | 20250725 | 20250725 | 07/25/2025 |
| MLOANIDT | 20250725 | 20250725 | 07/25/2025 |

\*0 if QLAdmin calc option selected

---

## 8. Fleet Generalization

| Mapping | Generalizes? |
|---------|:------------:|
| MLOANINT AS_PERCENT | **Yes** — all rates are decimal < 1 |
| MLOANPRIN = LOAN_BALANCE | **Likely yes** — gross principal pattern |
| MLOANDATE = ACCRUAL_DATE | **Yes** — 354/354 active have accrual date |
| MLOANIDT = ACCRUAL_DATE | **Mostly** — 109 active lack LAST_REPAY; accrual populated |
| MLOANACCR from PLOAN | **No** — zero fleet-wide |
| MLOANBAL = LOAN_BALANCE | **No** — must subtract accrued interest |
| MLOANINTX = A | **Likely** — screenshot + QLAdmin Help; not provable from PLOAN column |

---

## 9. Config Diff Preview (Documentation Only — Do Not Apply)

When Development authorized, expected `quikloan_derivation_rules.json` changes:

| Key | v1.0 | v1.1 (proposed) |
|-----|------|-----------------|
| `mloanint_scale` | UNRESOLVED_REVIEW | AS_PERCENT |
| `mloanprin_source` | LOAN_BALANCE | LOAN_BALANCE *(confirmed)* |
| `mloanbal_source` | LOAN_BALANCE | **DERIVED_NET** *(new — LOAN_BALANCE − accrual)* |
| `mloanaccr_source` | ACCRUED_INT_AMT | **CALCULATED_OR_ZERO** *(TBD)* |
| `mloanintx_source` | UNRESOLVED | **CONFIG_DEFAULT** |
| `mloanintx_default` | "" | **A** |
| `mloanidt_precedence` | LAST_REPAY, CAPITALIZED | **ACCRUAL_DATE**, LAST_REPAY, CAPITALIZED |

---

## 10. Sign-Off Required Before Implementation

- [ ] MLOANACCR: QLAdmin calc vs converter calc (Option A vs B)  
- [ ] MLOANINTX = A fleet-wide  
- [ ] MLOANBAL net formula confirmed against 2+ screenshot policies  
- [ ] MLOANIDT precedence with ACCRUAL_DATE first  

---

**Status:** Mapping revision documented. **Not applied to code or config.**
