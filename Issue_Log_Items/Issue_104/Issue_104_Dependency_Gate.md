# Issue #104 — Dependency Gate

**Issue:** #104 — Loan Handling (claim/surrender loan payoff interest)  
**Framework stage:** Dependency Gate (G2)  
**Date:** 2026-07-24  
**Result:** **CONDITIONAL PASS** — Risk may quantify options; **Development blocked** until SME answers fix-path questions

---

## Source data

| Check | Status | Notes |
|-------|--------|-------|
| PLOAN extract in `QLA_Migration/Source/` | **Met** | Same package as #32 QuikLoan |
| Extract row count > 0 | **Met** | Fleet PLOAN present; trace latest row known |
| Column headers documented | **Met** | `Issue_32_PLOAN_Source_Profile.md` |
| Extract matches batch under test | **Met** | Current `quikloan.csv` row matches approved mapping |
| Re-extract required? | **No** for diagnosis | UI interest still not in PLOAN (`ACCRUED_INT_AMT=0`) |

---

## Field definitions

| Check | Status | Notes |
|-------|--------|-------|
| QLAdmin QuikLoan target confirmed | **Met** | Help §7.150; #32 schema |
| Advance vs arrears semantics | **Met (Help)** | Advance accrued may be **negative** (unearned) |
| LifePRO UI interest semantics | **Met** | #32 screenshot: −18.19 unearned → net 3688.92 |
| Transformation for payoff total | **Missing for Dev** | No approved conversion change yet — SME must choose Option A/B/C |

---

## Client / business answers

| Check | Status | Notes |
|-------|--------|-------|
| Symptom + dollar proof | **Met** | Eric No-Go 7/23; policy 010331768C |
| Acceptance target = LifePRO $3,688.92 | **Missing** | Must confirm for claim/surrender |
| Authorize reopen of #32 `MLOANACCR=0` / gross BAL | **Missing** | Blocks Option A |
| QLAdmin as-of date / screen for +$194.01 | **Missing** | Needed to prove arrears-style calc |
| Scope claim vs surrender vs fleet | **Partial** | Wording says both; only one policy proven |
| Example policies | **Met** | 010331768C / 9010331768C |

---

## Evidence

| Check | Status | Notes |
|-------|--------|-------|
| Before-state in Output | **Met** | `9010331768C,3707.11,3707.11,5.00,A,20250725,20250725,0.00,0.00` |
| LifePRO side evidenced | **Met** | #32 screenshot / manual guidance |
| QLAdmin payout screenshot | **Missing** | Strongly preferred; not required to quantify Risk options |

---

## Regression guards

| Check | Status |
|-------|--------|
| #25 / #2 MPOLICY handling preserved | **Met** (plan does not touch unless expanded) |
| #26 MPREM mapping preserved | **Met** |
| #54 QuikBenh unchanged by default | **Met** |
| #32 validator expectations | **At risk** if Option A chosen — must revise intentionally |

---

## Blockers (Development — not Risk quantification)

| Blocker | Owner | Requested action |
|---------|-------|------------------|
| Confirm acceptance payoff total | Eric / SME | Yes/No: match LifePRO **$3,688.92** on this policy |
| Choose fix authority | Eric / SME | **A** reopen #32 load interest/net · **B** keep calc, fix INTX/dates · **C** QLAdmin-only / not conversion |
| Provide QLAdmin evidence of +$194.01 | Client UAT | Screen + as-of date (or confirm runtime version/load) |

---

## Gate G2 decision

**CONDITIONAL PASS** — Enough source, field, and Output evidence to run Risk option analysis.  
**Not** cleared for Development. Missing SME answers are **Development blockers**, not research blockers.

**Recommended tracking status:** Risk Complete — **No-Go for Development** pending SME (after Risk report).

**Hard stop for Dev:** Do not modify `quikloan_converter.py`, `quikloan_derivation_rules.json`, or #32 validator until SME selects an option and Risk is upgraded from No-Go.
