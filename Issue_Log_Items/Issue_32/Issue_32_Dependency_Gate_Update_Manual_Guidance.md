# Issue #32 — Dependency Gate Update (Manual Guidance)

**Issue:** #32 — Policy Loan Conversion  
**Gate stage:** Dependency Gate — **CONDITIONAL PASS**  
**Engine:** v57.39 (unchanged)  
**Generated:** 2026-06-29  
**Inputs:** Manual/business guidance + screenshot trace (9010331768) + repo investigation

---

## 1. Manual Guidance Received

| # | Guidance | Gate impact |
|---|----------|-------------|
| 1 | **Loan balance** = balance as of last anniversary or last loan transaction, including capitalized interest (arrears) or capitalized to next anniversary (advance) | Confirms PLOAN snapshot authority; both QuikLoan principal and balance load **gross** `LOAN_BALANCE` |
| 2 | **Interest rate/type** from **Plan Information File** (phase 1); timing may be **Advance (Adv)** or **Arrears (Arr)** | `MLOANINTX` from QuikPlan with documented fallback |
| 3 | **Accrued interest** — arrears: since last anniversary/transaction; advance: **negative** (unearned) | QLAdmin calculates; converter **does not** derive UI interest |
| 4 | **Business decision:** **QLAdmin will calculate interest** | **`MLOANACCR = 0.00`** approved at conversion |

---

## 2. Gate Verdict

## **CONDITIONAL PASS — Development Authorized**

Development may proceed under the **approved field mapping** in `Issue_32_Approved_Field_Mapping.md` and the **documented assumptions** below.

| Criterion | Status |
|-----------|--------|
| MLOANINT scale confirmed | **PASS** — `INTEREST_RATE × 100` (5.00, 7.40) |
| MLOANPRIN / MLOANBAL rule confirmed | **PASS** — both `LOAN_BALANCE` |
| MLOANACCR rule confirmed | **PASS** — `0.00`; QLAdmin calculates |
| MLOANINTX source or default | **CONDITIONAL PASS** — QuikPlan lookup + fallback **`A`** |
| MLOANIDT date rule documented | **PASS** — `ACCRUAL_DATE` |
| MLOANDATE | **PASS** — `ACCRUAL_DATE` |
| MLOANBILL | **PASS** — `0.00` |

---

## 3. Resolved vs Remaining

### Resolved by manual + prior screenshot evidence

| Topic | Decision |
|-------|----------|
| MLOANINT scale | **AS_PERCENT** — `.0500` → `5.00` |
| MLOANPRIN | **`LOAN_BALANCE`** |
| MLOANBAL | **`LOAN_BALANCE`** (gross; QLAdmin derives net/display interest) |
| MLOANACCR | **`0.00`** — do not map LifePRO UI calculated interest |
| MLOANDATE | **`ACCRUAL_DATE`** |
| MLOANIDT | **`ACCRUAL_DATE`** (see §5) |
| MLOANBILL | **`0.00`** |
| LifePRO UI net balance vs PLOAN | **Explained** — UI subtracts calculated interest; conversion loads gross balance for QLAdmin |

### Conditional / deferred (not blocking Development)

| Topic | Status | Assumption |
|-------|--------|------------|
| MLOANINTX plan lookup | QuikPlan `LOANINTX` in staged CSV not valid A/R | Fallback **`A`** per rulebook + screenshot Advance |
| Zero-balance emit (528 policies) | Not addressed in manual | Keep Phase L1 rule: **exclude** until OD-32D |
| STATUS_CODE filter | Not addressed | Keep date-driven latest-row selection |
| Policy 9011190668 | Phase L1 exception `MISSING_MLOANDATE` | Hold single policy; investigate accrual parse |

---

## 4. Loan Balance Rule (Manual Alignment)

### Why both MLOANPRIN and MLOANBAL = LOAN_BALANCE

Manual defines loan balance as the **authoritative carried balance** as of the last anniversary or loan transaction, including capitalization rules that differ for advance vs arrears.

PLOAN `LOAN_BALANCE` on the latest snapshot is that **carried balance** in the extract.

| LifePRO UI (9010331768) | PLOAN | QuikLoan load |
|-------------------------|-------|---------------|
| Principal 3,707.11 | LOAN_BALANCE 3,707.11 | MLOANPRIN = 3,707.11 |
| Balance 3,688.92 | *(not stored)* | MLOANBAL = 3,707.11 |
| Interest 18.19 | ACCRUED_INT_AMT 0.00 | MLOANACCR = 0.00 |

**Rationale:** LifePRO UI **Balance** reflects principal minus **QLAdmin/LifePRO-calculated** accrued/unearned interest. Manual states QLAdmin will calculate interest. Loading **gross** `LOAN_BALANCE` into both principal and balance fields gives QLAdmin the correct basis to apply advance/arrears math post-load.

**UAT requirement:** After load, QLAdmin must display interest and net balance consistent with LifePRO for policy `9010331768` (or document acceptable variance).

---

## 5. Accrued Interest Rule

| Fact | Detail |
|------|--------|
| PLOAN `ACCRUED_INT_AMT` | **0.00** on all 93,857 valid rows |
| LifePRO UI | May show non-zero interest (e.g. 18.19) |
| Manual | QLAdmin calculates; advance accrual may be **negative** (unearned) |
| QLAdmin Help (p.46) | Confirms advance vs arrears accrued semantics |

**Approved conversion rule:**

```
MLOANACCR = 0.00
```

Converter **must not** implement LifePRO UI interest derivation.

---

## 6. MLOANIDT Rule

**Approved precedence:**

1. **`ACCRUAL_DATE`** — matches LifePRO "Last Accrued Date" on screenshot; aligns with manual anniversary/transaction framing  
2. `LAST_REPAY_DATE` — fallback only if accrual blank  
3. `CAPITALIZED_DATE` — tertiary fallback  

**Fleet coverage (913 latest rows, ACCRUAL_DATE first):**

| Metric | Count |
|--------|------:|
| Populated via ACCRUAL_DATE | 913 / 913 |
| Blank MLOANIDT | **0** |
| ACCRUAL_DATE = INT_START_DATE | 912 / 913 |

**Blocked rows:** 0 under ACCRUAL_DATE-first rule. (Phase L1 still holds policy `9011190668` for invalid accrual parse — see Development readiness.)

---

## 7. MLOANINTX Summary (see full review)

| Source investigated | Usable for A/R? |
|--------------------|:---------------:|
| PLOAN `INTEREST_TYPE` (100% F) | No |
| PLOAN `INT_METHOD` (100% D) | No |
| QuikPlan `LOANINTX` (Plan Information File) | **Intended** — staged CSV values invalid (`22`) |
| `Sync_Rulebook_quikplan.csv` default | **Yes — `A`** |
| Screenshot (Advance) | Supports **`A`** |
| QuikPlSt `MLOANINTX` | State override table — optional phase 2 |

**Approved rule:** Plan lookup → if `LOANINTX ∈ {A,R}` use it; else **`A`**.

Full analysis: `Issue_32_MLOANINTX_Source_Review.md`

---

## 8. Authorization Conditions

Development is authorized **only if**:

1. Implements **approved mapping** — no UI interest derivation  
2. Sets **`mloanint_scale: AS_PERCENT`**  
3. Sets **`MLOANACCR = 0.00`**  
4. Implements **MLOANINTX** plan lookup with **`A` fallback**  
5. Sets **`MLOANIDT` / `MLOANDATE` from `ACCRUAL_DATE`**  
6. Preserves **emit gates** (`QLA_ENABLE_QUIKLOAN_EMIT`, `QLA_QUIKLOAN_WRITE_OUTPUT`) until UAT PASS  
7. Does **not** modify protected issues #21D–#28, #31  
8. Completes **UAT trace** on `9010331768` post-load  

---

## 9. Gate Outcome Matrix

| Outcome | When |
|---------|------|
| **FULL PASS** | After UAT confirms QLAdmin calculates interest correctly on ≥1 trace policy |
| **CONDITIONAL PASS (now)** | Mapping + manual alignment complete; plan LOANINTX CSV quality deferred |
| **FAIL** | Would have applied if MLOANACCR derivation were required — **avoided** by manual |

---

## 10. Document Index

| File | Purpose |
|------|---------|
| `Issue_32_Approved_Field_Mapping.md` | Signed mapping sheet v1.2 |
| `Issue_32_MLOANINTX_Source_Review.md` | Plan-file investigation |
| `Issue_32_Development_Readiness_Update.md` | Readiness checklist |
| `Issue_32_Next_Stage_Prompt.md` | Development Agent prompt |

---

**Verdict: CONDITIONAL PASS — Development Authorized** under assumptions in §8.

**Stop point:** No code changes in this task.
