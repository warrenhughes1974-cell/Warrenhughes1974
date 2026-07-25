# Issue #104 — Risk Review Report

**Issue:** #104 — Loan Handling (claim/surrender loan payoff interest)  
**Framework stage:** Risk Agent (G3)  
**Status:** **NO-GO** for Development  
**Generated:** 2026-07-24  
**Agent:** Risk Agent (Cursor Grok 4.5, read-only)

**Status note:** Risk analysis only — no production code changes.

---

## Go / No-Go Recommendation

**NO-GO** — Converter already emits the SME-approved Issue #32 QuikLoan snapshot for the exact client policy. The defect is that QLAdmin settlement interest (**+$194.01**) does not match LifePRO advance/unearned (**−$18.19**). Changing load rules without an SME-chosen authority would reopen #32/#54 balance assumptions. Quantify options below; do not code until SME picks a path.

---

## 1. Is this actually an issue?

**Yes (UAT / settlement).** Principal matches; payoff interest sign and magnitude do not.

| Side | Principal | Interest | Total |
|------|----------:|---------:|------:|
| LifePRO | 3,707.11 | −18.19 | 3,688.92 |
| QLAdmin (client) | 3,707.11 | +194.01 | 3,901.12 |
| Converter Output | 3,707.11 | ACCR=0 (calc deferred) | BAL=3,707.11 gross |

Identity: 194.01 + 18.19 = 212.20 = 3,901.12 − 3,688.92.

---

## 2. Current vs proposed mapping

| Field | Current (#32 approved) | Proposed | Change? |
|-------|------------------------|----------|---------|
| MLOANPRIN | LOAN_BALANCE | unchanged until SME | No |
| MLOANBAL | LOAN_BALANCE (gross) | Option A: maybe net 3688.92 | **SME** |
| MLOANACCR | 0.00 | Option A: signed interest | **SME** |
| MLOANINTX | A (plan/fallback) | Option B: verify A vs R / runtime | **SME** |
| MLOANDATE / MLOANIDT | ACCRUAL_DATE 20250725 | Option B: alternate date basis | **SME** |
| QuikBenh / claims | #54 / Item 14 | out of scope | No |

---

## 3. Premium / related fields untouched

| Target | Source | Touched? |
|--------|--------|----------|
| quikridr.MPREM / MMODPREM | #26 | **No** |
| MPOLICY width/form | #2 | **No** |
| QuikBenh loan history | #54 | **No** (default) |
| Held 0412 claim rows | Item 14 | **No** |

---

## 4. Repo references

| Location | Role |
|----------|------|
| `qla_core/quikloan_converter.py` | Emit path |
| `plan_governance/config/quikloan_derivation_rules.json` | #32 rules |
| `tools/validators/validate_quikloan_issue32.py` | Locks current emit |
| `Issue_Log_Items/Issue_32/*` | Approved mapping + UAT ~18.19 |
| `Issue_Log_Items/Issue_70/*` | Fleet LOANINTX=A; CSO arrears list still open |
| Output `quikloan.csv` line | `9010331768C,...,5.00,A,20250725,20250725,0.00,0.00` |
| Output `quikplan.csv` `1960PO` | LOANINT=5.00, LOANINTX=A |

---

## 5. Population analysis

| Metric | Count |
|--------|------:|
| QuikLoan rows in current Output | 356 |
| Client-proven payoff mismatch | 1 |
| Rows with MLOANACCR ≠ 0 today | 0 (by design) |
| Rows with MLOANINTX=A (expected majority) | Fleet per #32/#70 |

**Before/after simulation:** Not run for a production mapping change — no single approved “after” state. Option impacts:

| Option | Rows changed (est.) | Assessment |
|--------|--------------------:|------------|
| **A** — Load signed MLOANACCR and/or net MLOANBAL from LifePRO UI calc | Up to **356** active loans | **Reject until SME** — no extract field; breaks #32 “QLAdmin calculates”; #54 close-to-QuikLoan assumes gross footer |
| **B** — Keep MLOANACCR=0; fix date and/or INTX so QLAdmin advance math ≈ −18.19 | 1–N plans/policies | **Preferred conversion track if root cause is load dates/INTX** — needs QLAdmin reproduce first |
| **C** — QLAdmin runtime/config only (conversion correct per #32) | 0 conversion rows | **Possible** — document; no Dev on converter |

---

## 6. Fallback recommendation

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| A — reopen #32 load interest/net | ≤356 | Reject without SME + durable interest source |
| B — INTX/date diagnostic then surgical fix | TBD | **Recommended conversion path if SME keeps “QLAdmin calculates”** |
| C — no converter change | 0 | **Recommended if UAT proves load correct and engine mis-applies Advance** |
| Hybrid — load MLOANACCR only for claim-pending policies | unknown | Reject — no claim rows for this policy; grain unclear |

**Recommended fallback:** **Hold converter.** Reproduce QLAdmin +$194.01 with current CSV. If Loan Values already shows Advance unearned ≈ $18.19 but claim/surrender adds arrears-style interest, treat as **Option C** (product/runtime). If QuikLoan display already shows +$194 accrued under `INTX=A`, treat as **Option B** (timing/date/INTX) before any Option A.

---

## 7. Trace policies

| Policy | Converter before | LifePRO target | QLAdmin reported | Pass? |
|--------|-----------------:|---------------:|-----------------:|-------|
| 9010331768C (010331768C) | 3707.11 / ACCR 0 / A | 3688.92 | 3901.12 | **FAIL** |

---

## 8. Material calculation impact

| Item | Impact |
|------|--------|
| Claim/surrender net proceeds | Off by **$212.20** on this policy alone |
| Intentional #32 design | Gross load + zero accr — **working as coded** |
| Failed expectation | Post-load Advance unearned ≈ 18.19 (**#32 UAT not met at payout**) |

---

## 9. Prior fix preservation

| Check | Result |
|-------|--------|
| Issue #2 MPOLICY | Untouched under No-Go |
| Issue #26 MPREM / MMODPREM | Untouched |
| Issue #32 QuikLoan emit | **Do not alter** until SME |
| Issue #54 QuikBenh | Untouched |
| Issue #70 LOANINTX fleet A | Related; do not flip fleet without CSO |

---

## 10. Regression testing checklist (for Validation Agent — if later approved)

- [ ] Trace 9010331768C / 010331768C: payoff interest matches SME target
- [ ] QuikLoan row count stable unless Option A scoped
- [ ] MLOANACCR rule: either all-zero (#32) or documented signed load
- [ ] #54 Balance-close to QuikLoan still holds
- [ ] Non-loan tables unchanged
- [ ] #2 / #26 untouched
- [ ] Publish `Test_Validation/quikloan.csv` (+ `quikplan.csv` if INTX) on PASS
- [ ] Accountability IN_DATA before Closure

---

## 11. Recommended Development Agent Task

**Do not start Development.** After SME answers:

1. If **Option B:** surgical change only to proven wrong field(s) (date precedence and/or INTX source) with version bump + validator update.  
2. If **Option A:** rewrite #32 approved mapping + validator + #54 close assumptions; high-risk change control.  
3. If **Option C:** no converter PR — client/runtime note + close or park #104 as non-conversion.  
4. Do **not** emit held 0412 rows as surrenders; do not touch QuikBenh unless SME expands scope.

---

## Appendix — SME ask (paste-ready)

1. Confirm QLAdmin must match LifePRO loan payoff **$3,688.92** on `010331768C` at claim/surrender.  
2. Choose authority: **A** load interest/net in conversion · **B** keep QLAdmin calc, fix load timing/INTX · **C** QLAdmin-only (no conversion change).  
3. Send QLAdmin screenshot (Loan Values + claim/surrender loan line) showing **+$194.01** and the as-of date used.

---

## Gate G3

| Item | Result |
|------|--------|
| Risk report published | Yes |
| Impact quantified | Yes (options; 1 proven policy; ≤356 if Option A) |
| Go / No-Go | **NO-GO** |
| Ask for Development approval? | **No** — ask for SME answers first |
