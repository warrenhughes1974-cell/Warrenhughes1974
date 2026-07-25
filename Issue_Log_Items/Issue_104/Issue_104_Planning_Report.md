# Issue #104 — Planning Report

**Issue:** #104 — Loan Handling (claim/surrender loan payoff interest)  
**Framework stage:** Planning Agent  
**Status:** Planning complete — Dependency Gate next  
**Generated:** 2026-07-24  
**Agent:** Planning Agent (Cursor Grok 4.5) — research only, no code

---

## 1. Executive Finding

Client No-Go: at claim/surrender payoff, QLAdmin **adds** accrued loan interest ($194.01 → total $3,901.12) while LifePRO **removes** advance/unearned interest ($18.19 → total $3,688.92) on the same principal ($3,707.11). Trace policy is the Issue #32 / #54 anchor (`010331768C` / Output `9010331768C`).

Current conversion emit is **exactly the #32 approved mapping** (gross balance, `MLOANACCR=0`, `MLOANINTX=A`). #32 deferred interest math to QLAdmin and required UAT ≈ $18.19 unearned. That UAT expectation is **not** what the client sees at payout.

**Recommended direction:** Treat #104 as a **failed post-load loan interest settlement UAT** on the #32 design. Do **not** change QuikLoan emit until SME chooses among: (A) reopen #32 and load signed/net interest, (B) correct QuikPlan / QuikLoan timing fields so QLAdmin advance math yields ~$18.19, or (C) classify as QLAdmin runtime/config (no conversion change). Claims CSV emit is not the primary surface for this policy.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|--------------|--------------|---------------------|----------:|
| PLOAN | `PLOAN_LoanInformation_Extract_*.csv` | Yes | ~93k (latest-row grain for QuikLoan) |
| PACTG (history only) | accounting extract | Yes (#54) | N/A for payoff interest |
| QuikPlan (loan setup) | Output / plan emit | Yes | Plan `1960PO`: LOANINT=5.00, LOANINTX=A |

### Available source fields (loan)

| Field | Column / source | Populated % | Notes |
|-------|-----------------|------------:|-------|
| Policy number | `POLICY_NUMBER` | 100% | → MPOLICY via #2 |
| Carried balance | `LOAN_BALANCE` | 100% on active | **3707.11** on trace |
| Stored accrued | `ACCRUED_INT_AMT` | Always 0.00 | UI interest not in extract |
| Rate | `INTEREST_RATE` | Populated | `.0500` → 5.00% |
| Method code | `INT_METHOD` | `D` fleet-wide | **Not** Advance; rejected as MLOANINTX source in #32 |
| Accrual / paid-to dates | `ACCRUAL_DATE` | On latest | `20250725` → MLOANDATE / MLOANIDT |
| UI Interest / net | LifePRO screen only | N/A | 18.19 / 3688.92 — calculated |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source (Help / schema) |
|-------|-------|------|--------|------------------------|
| QuikLoan | MLOANPRIN | N | 10,2 | Help §7.150 |
| QuikLoan | MLOANBAL | N | 10,2 | Help §7.150 |
| QuikLoan | MLOANINT | N | | Rate % |
| QuikLoan | MLOANINTX | C | 1 | A=Advance / R=Arrears |
| QuikLoan | MLOANIDT / MLOANDATE | D | | Interest paid-to / balance date |
| QuikLoan | MLOANACCR | N | 10,2 | Accrued (advance may be negative) |
| QuikPlan | LOANINT / LOANINTX | | | Plan loan rate / timing (#70) |

**Repo references** (population paths only):

| Location | Role |
|----------|------|
| `qla_core/quikloan_converter.py` | Emit QuikLoan from PLOAN |
| `plan_governance/config/quikloan_derivation_rules.json` | #32 field rules v1.3 |
| `tools/validators/validate_quikloan_issue32.py` | Locks gross emit + MLOANACCR=0 |
| `qla_core/quikbenh_loan_history_converter.py` | #54 history (untouched unless coupled) |
| Issue #70 QuikPlan LOANINTX fleet `A` | Plan timing authority |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PLOAN | LOAN_BALANCE | MLOANPRIN | Direct money | **No** (unless SME reopens #32) |
| PLOAN | LOAN_BALANCE | MLOANBAL | Gross (not UI net) | **Pending SME** |
| PLOAN | INTEREST_RATE | MLOANINT | ×100 AS_PERCENT | **No** |
| QuikPlan | LOANINTX | MLOANINTX | A/R; fallback A | **Pending** if timing wrong |
| — | constant | MLOANACCR | 0.00 (#32) | **Pending SME reopen** |
| PLOAN | ACCRUAL_DATE | MLOANDATE / MLOANIDT | YYYYMMDD | **Pending** if date basis wrong |
| UI calc | Interest 18.19 | *(none today)* | Not extracted | Only if Option A |

### Fields that must remain unchanged (unless SME expands scope)

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| quikmstr.MMODPREM | PPOLC.MODE_PREMIUM | **No** |
| quikridr.MPREM | ANN_PREM_PER_UNIT + fallback (#26) | **No** |
| MPOLICY formatting | Issue #2 source+`C` width 11 | **No** |
| QuikBenh loan types 10/11/12 | #54 | **No** (default) |
| Held 0412 loan-accounting claims | Item 14 | **No** |

---

## 5. Open Client Questions

1. **Acceptance target:** Is LifePRO payoff total **$3,688.92** (principal − $18.19) the required QLAdmin claim/surrender loan total for this policy?
2. **Reproduce:** On the QLAdmin load under test, what screen/date produced **+$194.01**? Confirm payout as-of date and whether Loan Values shows Advance unearned before claim processing.
3. **#32 rule:** May conversion reopen `MLOANACCR=0` / gross `MLOANBAL`, or must QLAdmin continue to calculate interest?
4. **Sign:** Should Advance (`MLOANINTX=A`) produce **negative/unearned** interest at settlement (LifePRO), and is +$194.01 evidence QLAdmin is accruing as **arrears** despite `A`?
5. **#70 CSO:** Are any plans truly Arrears (`R`)? Is `1960PO` confirmed Advance for claim/surrender as well as display?
6. **Scope:** Claim only, surrender only, or both; one policy or fleet-wide loan settlements?

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Issue #2: source POLICY_NUMBER + `C`, width 11 (`9010331768C`) |
| Money | 2-decimal QLA money; do not invent UI interest without SME |
| MLOANACCR | Keep 0.00 until SME reopens #32 |
| Blanks / zeros | Zero-balance hold rules unchanged (#32/#44) |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

1. LifePRO `9010331768` → Output `9010331768C` (#2)  
2. Client may still cite `010331768C` — map both in validators/traces  
3. Orphans: existing QuikLoan hold rules — do not change

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| QuikLoan emit rows (current Output) | 356 | `quikloan.csv` |
| Trace policies with client dollar proof | 1 | 010331768C |
| Rows that would change under Option A (load signed interest) | Up to all active loans | Needs UI/calc source — **blocked** |
| Rows that would change under Option B (date/INTX fix only) | TBD after root-cause | Diagnostic first |

---

## 10. Sample Trace (1 client + controls)

| Policy (QLA) | LifePRO | QuikLoan before | LifePRO payoff | QLAdmin reported | Status |
|--------------|---------|-----------------|----------------|------------------|--------|
| 9010331768C | 9010331768 | PRIN=BAL=3707.11; INT=5; INTX=A; ACCR=0; dates=20250725 | 3688.92 (−18.19) | 3901.12 (+194.01) | **FAIL UAT** |
| *(control)* | — | Other Advance loans | TBD | TBD | Need second SME sample |

**Interest identity check:** 194.01 + 18.19 = **212.20** = 3901.12 − 3688.92 → pure opposite treatment of interest around the same principal.

**LifePRO ~18.19 check (from #32):** ~36 days advance at 5% on 3707.11 ≈ 18.28 — consistent with unearned-to-anniversary. **+$194.01** is consistent with a long **positive** accrual window, not advance unearned.

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Reopening #32 without SME | High | Gate Development until answers |
| Loading MLOANACCR from non-extract UI | High | No durable source in PLOAN |
| Changing MLOANBAL to net 3688.92 | High | Breaks #32/#54 balance-close assumptions |
| Touching QuikBenh / claims | Medium | Keep out of scope unless proven |
| #70 fleet LOANINTX=A wrong for some plans | Medium | CSO list; do not flip fleet blindly |
| Defect is QLAdmin-only runtime | Medium | Option C — no conversion Dev |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | Yes |
| Field definitions confirmed | Yes (#32 Help) |
| Client scope clear | **Partial** — payoff alignment clear; fix path not |
| Example policies available | Yes |
| #32 reopen authorized | **No** |

---

## 13. Recommended Risk Agent Prompt

```
Risk Agent — Issue #104: Loan Handling at claim/surrender.

Read Issue_104_Planning_Report.md and Issue_32 approved mapping.
Quantify options A/B/C (reopen #32 load interest; fix INTX/dates only; QLAdmin runtime).
Do not code. Recommend Go / Conditional Go / No-Go for Development.
Preserve #2 MPOLICY, #26 MPREM, #54 QuikBenh unless SME expands scope.
```

---

## 14. Recommended Development Task (Do Not Implement)

**Blocked pending SME.** If later approved:

1. Implement **only** the SME-chosen option (A, B, or C-documentation).  
2. Do **not** change QuikBenh, claims Item 14 holds, or #26/#2.  
3. Version bump both `app.py` copies if converter/rulebook touched.  
4. Validator: assert trace payoff interest sign/magnitude vs SME target; keep #32 emit checks updated if mapping changes.  
5. Publish affected `quikloan.csv` / `quikplan.csv` to `Output/Test_Validation/` on PASS.

---

## Appendix

- Related: `Issue_Log_Items/Issue_32/`, `Issue_54/`, `Issue_70/`  
- Help: QLAdmin Help §7.150 QuikLoan; advance accrued may be negative (~p.46)  
- Intake: `Issue_104_Intake_Summary.md`
