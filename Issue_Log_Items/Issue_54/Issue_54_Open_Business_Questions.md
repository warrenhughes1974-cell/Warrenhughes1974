# Issue #54 — Open Business Questions

**Status:** OBQ-1 **CLOSED** (2026-07-14) — coding still gated on Risk re-affirm + Development approval  
**Policy example:** `010822238C` / LifePRO `9010822238`

---

## OBQ-1 — Opening loan balance (CLOSED)

**Question:** When Loan History starts mid-stream (e.g. 2018) but the loan existed earlier (PLOAN back to 2003), where does QLAdmin get the **opening loan balance**?

**Why it matters:** We load Type / Date / Amount only. QLAdmin calculates Balance. Without an opening balance, early Balance shows large negatives (e.g. -$76,891). Current QuikLoan balance ($9,731.08) is correct.

**Decision (Warren / conversion lead, 2026-07-14):** **Option 1**

> Seed opening balance from **PLOAN** — last `LOAN_BALANCE` with `ACCRUAL_DATE` **strictly before** the first QuikBenh loan-history row date.

**Also decided:** Balance column **is required** for correct Loan History display — seed must make the UI running balance start correctly.

### How Option 1 is realized in QuikBenh

QuikBenh has **no Balance field** (Help §7.47). UI Balance is calculated from loaded Type / Date / Amount. Therefore Option 1 requires emitting a **synthetic opening seed row** into `quikbenh` so QLAdmin has a starting principal:

| Field | Rule |
|-------|------|
| `MPOLICY` | Crosswalk + #25 pad |
| `MBENTYP` | **10** (Policy loans granted) — proposed; Risk to confirm |
| `MDATE` | PLOAN seed row `ACCRUAL_DATE` (YYYYMMDD) |
| `MBEN` | PLOAN `LOAN_BALANCE` on that row |

**Do not emit seed when:** no PLOAN prior to first history date, or prior balance is 0 / blank (history already starts at inception or zero).

### Trace proof — `010822238C`

| Item | Value |
|------|-------|
| First research Benh row | 2018-01-15 · MBENTYP 11 · $669.20 |
| PLOAN seed (last before 20180115) | **2017-12-20** · **LOAN_BALANCE $8,373.99** |
| Current QuikLoan footer | $9,731.08 (unchanged #32/#44) |
| PLOAN span | 2003-10-31 → 2026-06-22 (874 rows) |

Evidence: `evidence/issue54_opening_balance_seed_scan.csv`

### Options not chosen

| # | Option | Status |
|---|--------|--------|
| 2 | Emit opening-balance row without specifying PLOAN source | Superseded — seed **is** a Benh row, but amount comes from PLOAN (Option 1) |
| 3 | Balance not required | Rejected — Balance required |
| 4 | Other LifePRO source | Not needed |

---

## Remaining open (non-blocking for Planning)

| ID | Question | Owner | Default for Risk |
|----|----------|-------|------------------|
| OBQ-2 | Confirm synthetic seed uses **MBENTYP=10** (vs other type / memo) | Eric / New Era | Use **10** |
| OBQ-3 | If first PACTG row is already 0411→10 on same day as seed, dedupe rule? | Conversion | Prefer PACTG 0411; skip seed if same-date type-10 already emitted |

Coding remains **not** in `app.py` until Risk re-affirm (G3) + explicit Development approval.
