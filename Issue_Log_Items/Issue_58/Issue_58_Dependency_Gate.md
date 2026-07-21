# Issue #58 — Dependency Gate

**Issue:** #58 — Premium Mode Amounts Incorrect  
**Framework stage:** Dependency Gate (G2)  
**Date:** 2026-07-13  
**Planning reference:** `Issue_58_Planning_Report.md`  
**Model:** Cursor Grok 4.5 (locked stage assignment)

---

## 1. Checklist

### Source data

| Check | Status | Notes |
|-------|--------|-------|
| New LifePRO modal-fee extract | **N/A** | Confirmed absent; derive from `MANNLFEE` + factors |
| PPOLC `POLICY_FEE` / #21C `MANNLFEE` | **Met** | Live Output: 4,457 base rows with `MANNLFEE > 0` |
| Policy modal factors (`quikmstr` MSEMI…) | **Met** | Implemented in engine (#36); **re-batch required** — current `Output/quikmstr.csv` has **0** non-blank factors (stale vs Issue_45 baseline with 5,083) |
| `Modal_Premium_Factors_By_Plan.csv` / quikplan | **Met** | Fallback only; primary = post-PAC `quikmstr` |
| Re-extract required? | **No** | Conversion-owned derivation |

### Field definitions

| Check | Status | Notes |
|-------|--------|-------|
| QuikRidr MSEMIFEE / MQTRLFEE / MMTHDFEE / MMTHBFEE | **Met** | Help §7.203 — modal policy fee amounts, NUMERIC 8.4 |
| Distinct from quikmstr modal **factors** | **Met** | #36 targets factors; #58 targets fees |
| Annual fee semantics (`MANNLFEE`) | **Met** | #21C from `POLICY_FEE` |
| Transformation | **Met** | `MANNLFEE × factor/100`; base phase only; post-PAC |

### Client clarification

| Check | Status | Notes |
|-------|--------|-------|
| Eric symptom / expected amounts | **Met** | `$60 / $31.20 / $15.90 / $5.40` on `010367131C` |
| Fleet fee authority = premium factors for **all** products (OBQ-1) | **Accepted for Conditional Risk** | Soft; not a hard G2 FAIL — Risk Conditional Go |
| Out of scope: `MMODEPREM`, `MPREM`, plan fee defaults | **Met** | Planning §4 |
| UAT criteria | **Met** | Names-tab amounts on Eric + PAC + ISWL samples |

### Evidence

| Check | Status | Notes |
|-------|--------|-------|
| Example policy | **Met** | `010367131C` |
| Math / before-state | **Met** | Intake + Planning evidence CSVs |
| Names-tab screenshot | **Missing (soft)** | Not required — measurable from Output + Eric dollars |
| Plan-family variance evidence | **Met** | `issue58_plan_mode36_match_rollup.csv` |

### Regression guards

| Check | Status |
|-------|--------|
| Issue #25 MPOLICY padding | **Required** |
| Issue #26 MPREM / MMODEPREM | **Required — untouched** |
| Issue #21C MANNLFEE | **Required — untouched** |
| Issue #36 factors + PAC order | **Required — fees after PAC** |

---

## 2. Gate decision

| Track | Scope | G2 result |
|-------|-------|-----------|
| **A — Derive modal fees on quikridr** | Base `MANNLFEE > 0` → four M*FEE fields | **PASS** |
| **B — Factor precondition** | #36 factors present before fee derive | **PASS with re-batch note** |
| **C — Fleet product authority (OBQ-1)** | All plans vs Conditional | **Deferred to Risk** — not G2 FAIL |

**Overall G2:** **PASS** — proceed to Risk Review.  
Development remains blocked until G3 and explicit user Development approval.

---

## 3. Unblock actions

None for G2. Soft follow-ups for Risk / UAT:

1. Re-batch so `quikmstr` factors are non-blank before validating #58 amounts.  
2. OBQ-1 (client): confirm fee modalization uses same factors for ISWL / all products.

---

## 4. Assumptions accepted at gate

1. Modal fees are coverage amounts on `quikridr`, not `quikmstr` factors.  
2. Derivation `MANNLFEE × (factor/100)` is correct for Eric’s family (`17085M` / GL85).  
3. Fleet-wide application may be **Conditional** at Risk (GPT / Planning caveat).  
4. `quikplan` SEMIFEE… remain 0.0000 — not invented.  
5. Live Output factor blankness is a **batch freshness** issue, not a missing design dependency.

---

## 5. Recommended issue status

**Dependency Gate PASS → Risk Agent**

Tracking: `ACTIVE — G2 PASS — Risk`
