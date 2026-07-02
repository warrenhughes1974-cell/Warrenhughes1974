# Issue #32 — LifePRO Screenshot Evidence Trace

**Policy:** `9010331768` → QLAdmin `010331768C`  
**Plan:** `960 PO` (QuikPlan `1960PO`)  
**Evidence:** LifePRO Policy Values / Loan Values / Loan Quotes screenshots  
**Extract:** `PLOAN_LoanInformation_Extract_20260530.csv`  
**PLOAN latest row:** ACCRUAL_DATE `20250725`, STATUS `A`, TYPE `R`  
**Generated:** 2026-06-29  
**Mode:** Dependency Gate / mapping evidence only — no code changes

---

## 1. Executive Summary

Screenshot evidence for policy `9010331768` **narrows** several mapping questions and **surfaces a critical gap** on accrued interest.

| Mapping topic | Screenshot verdict |
|---------------|-------------------|
| Interest rate scale (`MLOANINT`) | **Resolved** — load as **5.00** (percent), not 0.05 |
| Principal (`MLOANPRIN`) | **Resolved** — equals **`LOAN_BALANCE`**, not `ORIG_LOAN_AMOUNT` |
| Loan balance date (`MLOANDATE`) | **Resolved** — equals **`ACCRUAL_DATE`** (Last Accrued Date) |
| Interest paid-to (`MLOANIDT`) | **Narrowed** — on this policy equals `ACCRUAL_DATE` / `LAST_REPAY_DATE` (same date) |
| Net balance (`MLOANBAL`) | **Revised** — equals **`LOAN_BALANCE − UI Interest`**, not raw `LOAN_BALANCE` |
| Accrued interest (`MLOANACCR`) | **Not in PLOAN** — `ACCRUED_INT_AMT = 0.00`; UI value **18.19 is calculated** |
| Interest type Fixed | **Not mapped to QuikLoan** — display label only |
| Interest method Advance (`MLOANINTX`) | **NOT from `INT_METHOD`** — PLOAN has `D` fleet-wide; Advance is product/UI semantics |
| MLOANBILL | **No screenshot evidence** — default 0.00 |
| Bankers Year / Delay Days | **No QuikLoan fields** — PLOAN values match (`N`, `0`) |

---

## 2. End-to-End Comparison Table

| LifePRO Screen Label | LifePRO Screen Value | PLOAN Field | PLOAN Value (latest row) | Proposed QuikLoan Field | Proposed Output Value | Match? | Notes |
| -------------------- | -------------------: | ----------- | -----------------------: | ----------------------- | --------------------: | ------ | ----- |
| Principal | 3,707.11 | `LOAN_BALANCE` | 3,707.11 | `MLOANPRIN` | 3,707.11 | **YES** | Screen Principal = `LOAN_BALANCE`. **Not** `ORIG_LOAN_AMOUNT` (3,522.25). |
| Interest | 18.19 | `ACCRUED_INT_AMT` | 0.00 | `MLOANACCR` | 18.19 (calculated) | **NO** | PLOAN stores 0.00; UI computes ~36 days advance interest at 5% on principal. |
| Balance | 3,688.92 | derived | 3,688.92 | `MLOANBAL` | 3,688.92 | **PARTIAL** | 3,688.92 = 3,707.11 − 18.19. Not equal to raw `LOAN_BALANCE`. |
| Interest Rate | 5.00000% | `INTEREST_RATE` | .0500 (0.05 decimal) | `MLOANINT` | **5.00** | **YES** | PLOAN decimal × 100 = screen percent. Recommend `mloanint_scale: AS_PERCENT`. |
| Interest Type | Fixed | `INTEREST_TYPE` | F | *(none)* | N/A | N/A | Fixed vs variable — not QLAdmin A/R field. |
| Interest Method | Advance | `INT_METHOD` | D | `MLOANINTX` | A (inferred) | **NO** | **INT_METHOD=D fleet-wide (93,857 rows).** Advance label is **not** encoded in PLOAN `INT_METHOD`. |
| Last Accrued Date | 07/25/2025 | `ACCRUAL_DATE` | 20250725 | `MLOANDATE` | 20250725 | **YES** | Also equals `LAST_REPAY_DATE`, `CAPITALIZED_DATE`, `INT_START_DATE` on latest row. |
| Last Accrued Date | 07/25/2025 | `ACCRUAL_DATE` | 20250725 | `MLOANIDT` | 20250725 | **YES** | Staging used `LAST_REPAY_DATE` → same value on this policy. |
| Loan Interest Delay Days | 00 | `INT_DELAY_DAYS` | 0 | *(none)* | N/A | YES | No QuikLoan target field. |
| Bankers Year | No | `BANKERS_YEAR_IND` | N | *(none)* | N/A | YES | No QuikLoan target field. |
| Billing loan payment | *(not shown)* | *(none)* | — | `MLOANBILL` | 0.00 | N/A | No screenshot field; config default. |

**Machine-readable trace:** `Issue_32_Policy_9010331768_Trace.csv`

---

## 3. PLOAN History Context (Policy 9010331768)

88 PLOAN rows; latest selected row (Phase L1 sort):

| Field | Value |
|-------|------:|
| ACCRUAL_DATE | 20250725 |
| STATUS_CODE | A |
| TYPE_CODE | R |
| ORIG_LOAN_AMOUNT | 3,522.25 |
| LOAN_AMT_ADDED | 184.86 |
| LOAN_BALANCE | **3,707.11** |
| ACCRUED_INT_AMT | 0.00 |
| INTEREST_RATE | .0500 |
| INTEREST_TYPE | F |
| INT_METHOD | D |
| LAST_REPAY_DATE | 20250725 |
| CAPITALIZED_DATE | 20250725 |
| INT_START_DATE | 20250725 |
| INT_DELAY_DAYS | 0 |
| BANKERS_YEAR_IND | N |

Prior same-day rows on 20250725 show balance adjustments (history chain ending at active row 224).

---

## 4. Question-by-Question Resolution

### Q1 — Interest Rate Scale

**Answer:** `MLOANINT = 5.00` (whole percent).

| Evidence | Detail |
|----------|--------|
| Screenshot | `5.00000%` |
| PLOAN | `.0500` |
| Phase L1 staging | Emits `0.05` (incorrect per screenshot) |

**Recommendation:** Set `mloanint_scale: AS_PERCENT` in derivation rules when Development authorized.

---

### Q2 — MLOANINTX Mapping (`INT_METHOD` vs `INTEREST_TYPE`)

**Answer:** **Neither PLOAN column directly maps** to QLAdmin A/R on this fleet.

| Column | Policy 9010331768 | Fleet (93,857 rows) |
|--------|-------------------|---------------------|
| `INTEREST_TYPE` | F (Fixed) | **100% F** |
| `INT_METHOD` | D | **100% D** |

Screenshot shows **Interest Type = Fixed** and **Interest Method = Advance** as **separate** UI labels. PLOAN encodes Fixed in `INTEREST_TYPE` only; **Advance is not present as `A` or `R` in `INT_METHOD`**.

**Hypothesis tested:** Map `INT_METHOD` → `MLOANINTX` — **REJECTED** (no A/R codes in extract).

**Working inference:** Product uses **interest-in-advance** timing (screenshot + QLAdmin Help p.180). Proposed **`MLOANINTX = A`** as **business default**, sourced from **plan/product configuration or SME rule**, not from raw PLOAN `INT_METHOD`.

QuikPlan staged `1960PO` shows `LOANINTX = 22` (not A/R) — plan table **cannot** be used without codebook/SME normalization.

---

### Q3 — Principal Mapping

**Answer:** LifePRO screen **Principal = `LOAN_BALANCE`** on latest snapshot.

| Candidate | Value | Matches screen? |
|-----------|------:|:---------------:|
| `LOAN_BALANCE` | 3,707.11 | **YES** |
| `ORIG_LOAN_AMOUNT` | 3,522.25 | NO |
| `LOAN_AMT_ADDED` | 184.86 | NO |
| `LOAN_BALANCE + ACCRUED_INT_AMT` | 3,707.11 | YES (accrual zero) |

**Prior staging error:** `MLOANPRIN = MLOANBAL = LOAN_BALANCE` conflates principal with gross balance; screenshot shows principal is gross **before** accrued interest deduction.

---

### Q4 — Balance Mapping

**Answer:** LifePRO screen **Balance = `LOAN_BALANCE − accrued UI interest`**.

| Candidate | Value | Matches 3,688.92? |
|-----------|------:|:-----------------:|
| `LOAN_BALANCE` | 3,707.11 | NO |
| `LOAN_BALANCE − 18.19` | 3,688.92 | **YES** |
| `LOAN_BALANCE − ACCRUED_INT_AMT` | 3,707.11 | NO (ACCRUED=0) |

**Implication:** `MLOANBAL` cannot be mapped to raw `LOAN_BALANCE` alone when LifePRO shows net balance.

---

### Q5 — Accrued Interest Reconciliation

**Answer:** **`ACCRUED_INT_AMT` does not hold UI interest.** Interest is **LifePRO-calculated at display time**.

| Test | Result |
|------|--------|
| Policy in May extract? | **YES** — 88 rows |
| Latest row ACCRUED_INT_AMT | 0.00 |
| Fleet ACCRUED_INT_AMT > 0 | **0 rows** |
| UI interest formula check | 18.19 ≈ 3,707.11 × 0.05 × (35.8/365) — ~36 days advance accrual |

**Explanations ruled out:**

- Policy missing from extract — **ruled out**
- Wrong snapshot selected — **ruled out** (Principal matches latest `LOAN_BALANCE`)
- ACCRUED_INT_AMT populated elsewhere in PLOAN — **ruled out** (zero fleet-wide)

**Explanations supported:**

- Interest calculated dynamically in LifePRO UI from principal, rate, method, and period
- PLOAN stores **capitalized** movement in `LOAN_AMT_ADDED`, not running accrued interest in `ACCRUED_INT_AMT`

**PACTG note:** Phase 22C shows 0412 capitalization amounts for this policy (e.g. $602–$635 annual) — transaction history, not snapshot accrued interest.

---

### Q6 — Date Mapping

**Last Accrued Date 07/25/2025:**

| PLOAN field | Value | Match? |
|-------------|-------|--------|
| `ACCRUAL_DATE` | 20250725 | **YES** |
| `LAST_REPAY_DATE` | 20250725 | YES |
| `CAPITALIZED_DATE` | 20250725 | YES |
| `INT_START_DATE` | 20250725 | YES |

**Recommendations:**

| QuikLoan field | Revised source | Confidence |
|----------------|----------------|------------|
| `MLOANDATE` | `ACCRUAL_DATE` | **High** |
| `MLOANIDT` | `ACCRUAL_DATE` (preferred over repay/capitalized when equal) or keep LAST_REPAY → CAPITALIZED precedence | **Medium-High** on this policy; 109 active policies missing LAST_REPAY |

---

### Q7 — MLOANBILL

**Answer:** No screenshot evidence. **Default 0.00** unless SME identifies `PPOLC` loan repayment fields or billing source.

---

## 5. Phase L1 Staging vs Screenshot (Policy 9010331768)

| Field | Phase L1 emit | Screenshot-aligned target | Delta |
|-------|--------------|---------------------------|-------|
| MLOANPRIN | 3,707.11 | 3,707.11 | OK |
| MLOANBAL | 3,707.11 | 3,688.92 | **−18.19** |
| MLOANINT | 0.05 | 5.00 | **scale wrong** |
| MLOANINTX | blank | A (inferred) | **missing** |
| MLOANIDT | 20250725 | 20250725 | OK |
| MLOANDATE | 20250725 | 20250725 | OK |
| MLOANACCR | 0.00 | 18.19 | **wrong source** |
| MLOANBILL | 0.00 | 0.00 | OK (assumed) |

---

## 6. Fleet-Level Follow-Up

| Profile | Result |
|---------|--------|
| `INT_METHOD` values | **D only** — 93,857 rows |
| `INTEREST_TYPE` values | **F only** — 93,857 rows |
| Active loans (`LOAN_BALANCE > 0`, latest) | 354 policies (385 in full latest set; 354 after re-profile with valid balance parse) |
| Rate `.0500` active | 58 policies |
| Rate `.0740` active | 296 policies |
| `ACCRUED_INT_AMT > 0` | **0** fleet-wide |
| Principal = `LOAN_BALANCE` pattern | **Supported** for 9010331768; fleet active rows all have `ORIG ≠ LOAN_BALANCE` |
| Net balance derivable without UI formula | **No** — interest not in PLOAN |
| Active missing `LAST_REPAY_DATE` | 109 policies |
| Active missing `ACCRUAL_DATE` | 0 (9011190668 blocked at planning stage on full 385 set) |

**Generalization:** Principal/rate/date relationships from screenshot **generalize** for rate and principal. **Balance and accrued interest do not generalize from PLOAN columns alone** — same gap for entire fleet.

---

## 7. Conclusion

### Answered by screenshot evidence

1. **MLOANINT scale** — use **5.00** (percent), not 0.05  
2. **MLOANPRIN** — **`LOAN_BALANCE`** (gross principal)  
3. **MLOANDATE** — **`ACCRUAL_DATE`**  
4. **MLOANIDT** — **`ACCRUAL_DATE`** acceptable on trace policy (aligns with Last Accrued Date)  
5. **`INTEREST_TYPE`** — Fixed label only; **not** `MLOANINTX`  
6. **`INT_METHOD`** — **not** Advance/R in extract; **reject** as `MLOANINTX` source  
7. **Delay days / Bankers Year** — no QuikLoan mapping required  

### Partially answered / revised

1. **MLOANBAL** — net of accrued interest, **not** raw `LOAN_BALANCE`  
2. **MLOANINTX** — likely **`A` (Advance)** by product rule, but **source is not PLOAN column**  

### Still unresolved

1. **MLOANACCR** — no PLOAN source; requires **calculation formula** or alternate extract  
2. **MLOANBAL derivation** — depends on MLOANACCR calculation  
3. **MLOANINTX authoritative source** — plan table, PPOLC, or fleet-wide SME default  
4. **Zero-balance emit scope** — not addressed by screenshot  
5. **STATUS gating** — not addressed by screenshot  
6. **Conversion as-of date** for interest calculation when extract date ≠ UI quote date  

### Development status

| Gate | Status |
|------|--------|
| Development authorized? | **NO** |
| SME confirmation required? | **YES** — especially MLOANACCR formula and MLOANINTX ownership |
| Can Development proceed? | **Only under assumptions** documented in `Issue_32_Field_Mapping_Revision.md` |

---

**Stop point:** Evidence trace complete. Route to Ownership Decision after SME confirms interest calculation approach.
