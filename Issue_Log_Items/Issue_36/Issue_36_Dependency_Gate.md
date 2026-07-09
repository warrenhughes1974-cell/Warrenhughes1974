# Issue #36 — Dependency Gate

**Issue:** #36 — Modal Premium factors at policy level (`quikmstr`)  
**Framework stage:** Dependency Gate (G2)  
**Date:** 2026-07-09  
**Planning reference:** `Issue_36_Planning_Report.md`

---

## 1. Checklist

### Source data

| Check | Status | Notes |
|-------|--------|-------|
| LifePRO policy-level modal factor extract | **N/A** | Confirmed absent (#21J); not required |
| `quikplan.csv` with SEMI/QTRL/MTHD/MTHB | **Met** | 141 plans; 0 blank SEMI |
| `Modal_Premium_Factors_By_Plan.csv` | **Met** | Upstream of #21J plan overlay |
| `quikridr` phase-1 MPLAN | **Met** | 5,083/5,083 policies resolve |
| Re-extract required? | **No** | Conversion-owned copy from plan setup |

### Field definitions

| Check | Status | Notes |
|-------|--------|-------|
| QLAdmin QuikMstr MSEMI/MQTRL/MMTHD/MMTHB | **Met** | Help p.836 screenshot in `evidence/` |
| Semantics = modal factors (not fees) | **Met** | Distinct from quikridr M*FEE |
| Factor scale (percent 51.xxxx) | **Met** | Same as closed #21J / quikplan |
| Target table = quikmstr (not quikridr) | **Met** | Client title corrected in Intake |

### Client clarification

| Check | Status | Notes |
|-------|--------|-------|
| Populate factors so Names-tab Modal Premiums work | **Met** | Issue log + screenshot |
| Fleet-wide copy from plan | **Met** | Accepted in Planning (Q2) |
| Do not invent LifePRO quote factors | **Met** | Explicit out of scope |
| UAT: Names tab on sample policies | **Met** | 010148856C + PAC sample |

### Evidence

| Check | Status | Notes |
|-------|--------|-------|
| Help schema screenshot | **Met** | `evidence/qladmin_help_quikmstr_modal_factors.png` |
| Names-tab screenshot | **Met** | `evidence/policy_010148856C_names_tab_modal_premiums.png` |
| Before-state blank fleet | **Met** | 5,083 blank on all four fields |
| Simulation populate count | **Met** | 5,083 would populate; PAC 4 Q + 8 S |

### Regression guards

| Check | Status |
|-------|--------|
| Issue #25 MPOLICY padding | Required |
| Issue #26 MPREM / MMODEPREM | Required — MMODEPREM untouched |
| Issue #21J quikplan factors + PAC overrides | Required — PAC after plan copy |

---

## 2. Gate decision

| Track | Scope | G2 result |
|-------|-------|-----------|
| **A — Fleet plan-factor copy to quikmstr** | MSEMI/MQTRL/MMTHD/MMTHB from phase-1 plan | **PASS** |
| **B — PAC GL85 override preserve** | Existing `apply_pac_gl85_modal_overrides` after copy | **PASS** |
| **C — LifePRO runtime quote factors** | 0.525 / 0.27 style extract | **Deferred / N/A** — not in source |

**Overall G2:** **PASS** — proceed to Risk Review. Development remains blocked until G3 Go and user acknowledgment.

---

## 3. Unblock actions

None. No client data wait.

---

## 4. Assumptions accepted at gate

1. Factor values use the same percent scale as `quikplan` / #21J mapping.  
2. All four factors are written for every policy.  
3. PAC GL85 overrides remain authoritative for the **two special modes**: quarterly `MQTRL=25.0000` and semiannual `MSEMI=50.0000` (per `docs/Policy Form Modal Premium Factors.xlsx`).
4. `MMTHD` and `MMTHB` are copied independently from plan `MTHD`/`MTHB` (often different).
5. `docs/Copy of Premium Paid Fields.xlsx` is **out of scope** for #36 (Premiums Paid / Tax Basis — Non-ISWL vs ISWL).
