# Issue #32 — Sample Policy Validation

**Engine:** v57.40  
**Date:** 2026-06-29  
**Result:** **PASS**

Evidence JSON: `Issue_32_Sample_Policy_Evidence.json`

---

## 1. Primary trace policy — 9010331768 → 010331768C

**Expected:**

```text
010331768C,3707.11,3707.11,5.00,A,20250725,20250725,0.00,0.00
```

**Actual (quikloan.csv line 2):**

```text
010331768C,3707.11,3707.11,5.00,A,20250725,20250725,0.00,0.00
```

| Field | Expected | Actual | Status |
|-------|--------:|-------:|:------:|
| MLOANPRIN | 3707.11 | 3707.11 | ✅ |
| MLOANBAL | 3707.11 | 3707.11 | ✅ |
| MLOANINT | 5.00 | 5.00 | ✅ |
| MLOANINTX | A | A | ✅ |
| MLOANIDT | 20250725 | 20250725 | ✅ |
| MLOANDATE | 20250725 | 20250725 | ✅ |
| MLOANACCR | 0.00 | 0.00 | ✅ |
| MLOANBILL | 0.00 | 0.00 | ✅ |

**PLOAN context:** LOAN_BALANCE=3707.11; INTEREST_RATE=.0500; LifePRO UI interest ~18.19 **not** converted.

---

## 2. Representative samples

### 2.1 — 5.00% loan (9010331768)

See §1 — **PASS**

---

### 2.2 — 7.40% loan (9010719815 → 010719815C)

| Field | PLOAN source | Emit | Status |
|-------|-------------|------|:------:|
| LOAN_BALANCE / MLOANPRIN | 513.22 | 513.22 | ✅ |
| MLOANBAL | 513.22 | 513.22 | ✅ |
| INTEREST_RATE .0740 → MLOANINT | — | 7.40 | ✅ |
| ACCRUAL_DATE → MLOANIDT/MLOANDATE | 20120803 | 20120803 | ✅ |
| MLOANINTX | — | A (fallback) | ✅ |
| MLOANACCR / MLOANBILL | — | 0.00 / 0.00 | ✅ |

**Emit line:** `010719815C,513.22,513.22,7.40,A,20120803,20120803,0.00,0.00`

**Note:** LAST_REPAY_DATE=20101130 on PLOAN — MLOANIDT still uses ACCRUAL_DATE per v1.2 (not repay date).

---

### 2.3 — Largest non-zero balance (9010736035 → 010736035C)

| Field | Value | Status |
|-------|------:|:------:|
| MLOANPRIN / MLOANBAL | 67404.71 | ✅ |
| MLOANINT | 7.40 | ✅ |
| MLOANIDT / MLOANDATE | 20190613 | ✅ |
| MLOANACCR / MLOANBILL | 0.00 | ✅ |

---

### 2.4 — Smallest non-zero balance (9010363098 → 010363098C)

| Field | Value | Status |
|-------|------:|:------:|
| MLOANPRIN / MLOANBAL | 0.08 | ✅ |
| MLOANINT | 5.00 | ✅ |
| MLOANIDT / MLOANDATE | 20181005 | ✅ |

Confirms sub-dollar balances emit correctly when non-zero.

---

### 2.5 — Policy with prior repayments (9010719815)

Same as §2.2 — PLOAN shows LAST_REPAY_DATE=20101130; emit dates from ACCRUAL_DATE=20120803. **PASS** per v1.2 rule.

---

### 2.6 — Policy with capitalized amount (9010393181 → 010393181C)

| PLOAN field | Value |
|-------------|-------|
| LOAN_BALANCE | 1805.04 |
| LAST_REPAY_DATE | 20150708 |
| CAPITALIZED_DATE | 20190701 |
| ACCRUAL_DATE | 20190701 |

**Emit:** `010393181C,1805.04,1805.04,5.00,A,20190701,20190701,0.00,0.00` — **PASS**

Capitalization history reflected in balance; dates from ACCRUAL_DATE only.

---

### 2.7 — Zero-balance exclusion (9010300689 → 010300689C)

| Check | Result |
|-------|--------|
| Latest LOAN_BALANCE | 0.00 |
| In quikloan.csv | **No** |
| Exception reason | ZERO_BALANCE_HELD |
| Audit trace present | Yes (mapped values 0.00) |

**PASS** — correctly excluded from emit.

---

### 2.8 — Blocked policy (9011190668 → 011190668C)

| Check | Result |
|-------|--------|
| Latest LOAN_BALANCE | 621.78 (non-zero) |
| ACCRUAL_DATE | blank |
| In quikloan.csv | **No** |
| Exception reason | MISSING_MLOANDATE |
| Mapped trace values | MLOANPRIN/BAL=621.78, MLOANINT=7.40, dates blank |

**PASS** — correctly blocked per `hold_missing_mloandate=true`.

---

## 3. Sample validation summary

| Sample type | Policy | In emit | Status |
|-------------|--------|:-------:|:------:|
| Trace 5.00% | 9010331768 | Yes | ✅ |
| 7.40% | 9010719815 | Yes | ✅ |
| Largest balance | 9010736035 | Yes | ✅ |
| Smallest non-zero | 9010363098 | Yes | ✅ |
| Prior repayments | 9010719815 | Yes | ✅ |
| Capitalized | 9010393181 | Yes | ✅ |
| Zero balance | 9010300689 | No | ✅ |
| Blocked date | 9011190668 | No | ✅ |

---

**Sample policy validation: PASS**
