# Issue #106 — Dependency Gate

**Issue:** #106 — RV Rates Off by One Duration (QuikTvs)  
**Framework stage:** Dependency Gate (G2)  
**Date:** 2026-07-24  
**Result:** **PASS** — cleared for Risk / Development approval

---

## Source data

| Check | Status | Notes |
|-------|--------|-------|
| Rate_Table extract present | **Met** | `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv` |
| RV rows for 670 GL85-8 | **Met** | 9,230 RV rows; M/17 Dur1=0, Dur2=8.76, Dur83=1000 |
| RV rows for 659 CEN II | **Met** | M/17 S Dur1=1, Dur83=978 |
| L10 LP95 RV rows | **Met** | Coverage present (~196k rows containing `L10 LP95`) |
| L10 LP9595 RV rows | **Absent (expected)** | **0** Rate_Table rows containing `LP9595` — explains Eric mismatch |
| Re-extract required? | **No** for Dur fix | LP9595 would need client extract if they want that ID loaded |

---

## Field definitions

| Check | Status | Notes |
|-------|--------|-------|
| RV → QuikTvs mapping confirmed | **Met** | `TYPE_TO_TABLE["RV"] = "QuikTvs"` |
| Duration helper documented | **Met** | `source_duration_to_ql` = source−1; CV separate |
| Proposed identity transform | **Met** | `ql = source` for RV only |
| CV matrix out of scope | **Met** | Do not call `cv_remap_ql_duration` for RV |

---

## Client / business answers

| Check | Status | Notes |
|-------|--------|-------|
| Symptom + screenshot pack | **Met** | `docs/670 GL85 Rates.docx`, `docs/RV Factor Samples.docx`, `docs/QuikTvs_RsvReview_20260724.xlsx` |
| Acceptance = match LifePRO Dur labels | **Met (implied)** | Eric: “LP starts Dur 1 / QL starts Dur 0” |
| Example plans | **Met** | 170858, 17085M, 170588, 1659C2, 221END, 1960OL, 1L1095 |
| Expand to NP/DV/DB this issue? | **Deferred** | Not required for Dev of RV-only |

---

## Evidence

| Check | Status | Notes |
|-------|--------|-------|
| Before-state QuikTvs Output | **Met** | 170858 M/17 Dur1=8.76, Dur82=1000; 1659C2 M/17 SM Dur0=1, Dur82=978 |
| Diagnostic script | **Met** | `QLA_Migration/_research_issue106_rv_dur.py` |
| 1L1095 lineage | **Met** | QuikTvs M/17 S Dur1=4.45 = L10 LP95 M/17 S Dur2 (under −1); inheritance JSON source_segments=`L10 LP95` |
| Output QuikTvs row counts | **Met** | 170858=986, 17085M=986, 170588=986, 1659C2=2128, 221END=476, 1960OL=1015, 1L1095=3096 |

---

## Regression guards

| Check | Status |
|-------|--------|
| #37/#41/#98 CV remap preserved | **Met** (plan does not touch CV branch) |
| #25 / #2 MPOLICY | **Met** (untouched) |
| #26 MPREM | **Met** (untouched) |
| Non-CV NP/DV/DB/PR duration | **Met** (explicitly out of scope) |

---

## Blockers

| Blocker | Owner | Status |
|---------|-------|--------|
| None for RV Dur identity Dev | — | Cleared |
| LP9595 extract (only if client insists that ID) | Client | Not a Dur-fix blocker; document gap |

---

## Gate G2 decision

**PASS** — Source, Output before-state, client screenshots, and fix authority are sufficient. Proceed to Risk; Development may start after user approval.
