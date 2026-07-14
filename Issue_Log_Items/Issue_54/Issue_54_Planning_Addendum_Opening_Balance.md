# Issue #54 — Planning Addendum (Opening Balance Seed)

**Date:** 2026-07-14  
**Framework stage:** Planning (re-entry after OBQ-1 close)  
**Model:** Cursor Grok 4.5 (locked)  
**Status:** **Ready for Dependency Gate / Risk re-affirm**  
**Supplements:** `Issue_54_Planning_Addendum_QuikBenh.md` · closes `Issue_54_Open_Business_Questions.md` OBQ-1  

**Code changes:** Prohibited this stage

---

## 1. Executive finding

UAT proved PACTG → QuikBenh Type / Date / Amount load works, but QLAdmin **Balance** goes largely negative when history starts **mid-stream** (loan existed earlier). Business decision **Option 1:** seed opening balance from **PLOAN** (last `LOAN_BALANCE` before first history date).

Because QuikBenh has no Balance column, Development must emit a **synthetic opening seed row** (`MBENTYP=10` proposed) carrying that PLOAN amount so the UI running balance starts correctly. QuikLoan footer (#32/#44) stays the current-balance authority and is **unchanged**.

---

## 2. Confirmed sources (unchanged + seed)

| Role | Source | Notes |
|------|--------|-------|
| History transactions | PACTG 0411/0412/0413 | → MBENTYP 10/11/12; exclude 0451 + reversals |
| **Opening seed amount + date** | **PLOAN** | Last row with `ACCRUAL_DATE` **&lt;** first Benh loan history `MDATE` |
| Current footer | PLOAN latest → QuikLoan | #32/#44 — do not change |

---

## 3. Proposed seed mapping (Development blueprint — do not implement yet)

| Condition | Action |
|-----------|--------|
| Policy has ≥1 loan Benh row from PACTG | Compute `first_mdate` = min loan `MDATE` |
| Exists PLOAN row with `ACCRUAL_DATE` &lt; `first_mdate` and `LOAN_BALANCE` &gt; 0 | Emit **one** seed row |
| Else | No seed (history starts at inception or no prior balance) |

| QuikBenh field | Seed value |
|----------------|------------|
| `MPOLICY` | Crosswalk + `#25` `format_qladmin_mpolicy` |
| `MBENTYP` | **10** (Policy loans granted) — pending OBQ-2 confirm |
| `MDATE` | Seed PLOAN `ACCRUAL_DATE` (YYYYMMDD) |
| `MBEN` | Seed PLOAN `LOAN_BALANCE` (N10.2 abs) |

**Merge rules:**

1. Append seed + PACTG loan rows to existing `quikbenh` (preserve MBENTYP=8).  
2. On re-run, replace loan types **10/11/12** for policies in scope (include synthetic seeds in replace set).  
3. If PACTG already emits type **10** on seed date with same amount, skip duplicate seed (OBQ-3 default).  
4. Sort presentation is QLAdmin’s (`MPOLICY+MDATE`); seed date must be **before** first PACTG history date.

**Out of scope:** Changing QuikLoan; emitting Balance field; MBENTYP 20; routing 04xx to QUIKCLMS.

---

## 4. Trace — `010822238C` / `9010822238`

| Step | Value |
|------|-------|
| First PACTG→Benh row | 2018-01-15 · type 11 · $669.20 |
| Opening seed | **2017-12-20 · type 10 · $8,373.99** (PLOAN) |
| QuikLoan current | $9,731.08 |
| Expected UI effect | Balance starts ~$8,373.99 then applies 2018+ activity (not −$76k) |

---

## 5. Fleet impact (research emit population)

Source scan: `evidence/issue54_opening_balance_seed_scan.csv` (1,287 research-emit policies)

| Rule | Policies | Meaning |
|------|---------:|---------|
| **SEED_PRIOR** | **628** | Mid-stream — emit PLOAN opening seed |
| … of which balance &gt; 0 | **593** | Non-zero seeds |
| NO_PRIOR_USE_EARLIEST | 96 | No PLOAN before first Benh — **no seed** under Option 1 |
| NO_PLOAN | 563 | No PLOAN match — **no seed** |

**Estimated added rows:** ~593–628 synthetic type-10 seeds (one per mid-stream policy), on top of prior ~36.8k–40.5k PACTG loan Benh rows.

---

## 6. Formatting / fallbacks

| Topic | Rule |
|-------|------|
| Amount | Absolute value, 2 decimals (same as PACTG emit) |
| Date | YYYYMMDD from PLOAN `ACCRUAL_DATE` |
| Missing prior PLOAN | Skip seed; log exception |
| Zero / blank balance | Skip seed |
| Multiple PLOAN rows same prior date | Use last row in file order after date sort (stable) |

---

## 7. Unrelated fields (must not change)

`quikloan` mapping · `quikmstr` / `quikridr` / `quikprmh` · existing Benh MBENTYP=8 · #25 pad helper · #26 MPREM · QUIKCLMS 04xx hold

---

## 8. Open questions for Risk

1. **OBQ-2:** Confirm seed `MBENTYP=10`.  
2. **OBQ-3:** Dedupe when PACTG 0411 already on seed date.  
3. Quantify Risk: +~600 seed rows; negative-balance UAT fix for mid-stream policies.  
4. Validator must assert: mid-stream sample (`010822238C`) has seed row; type-8 count stable; QuikLoan unchanged.

---

## 9. Recommended next stages

**Dependency Gate Rev3** → **Risk Agent re-affirm (G3)** for opening-seed delta → then explicit **Development approval** on **Composer 2.5**.

### Suggested Risk prompt

```
Proceed to Risk Agent for Issue 54 — Opening Balance Seed addendum.

Read Issue_54_Planning_Addendum_Opening_Balance.md and Issue_54_Open_Business_Questions.md (OBQ-1 CLOSED Option 1).
Model: Cursor Grok 4.5. Do not code.
Re-affirm G3 for PLOAN opening seed rows (MBENTYP 10) + prior PACTG→Benh plan.
```

### Suggested Development task (do not implement yet)

Extend `qla_core/quikbenh_loan_history_converter.py` + rules JSON: after building PACTG loan rows, for each policy with prior PLOAN balance, prepend/emit one seed row; wire only after G3 + approval; bump both `app.py` versions; extend `validate_issue54_quikbenh_loan_history.py` for seed presence on `010822238C`.
