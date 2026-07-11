# Issue 21F — Dependency Gate

**Issue:** #21F — Truncated Premium History (conversion premium adjustment)  
**Framework stage:** Dependency Gate (G2)  
**Date:** 2026-07-11  
**Agent / model:** Dependency Gate · **Cursor Grok 4.5** (locked)  
**Planning reference:** `Issue_21F_Planning_Report.md`  
**Business decisions:** `Issue_21F_Business_Decisions.md` (Eric confirmed)

---

## 1. Checklist

### Source data

| Check | Status | Notes |
|-------|--------|-------|
| Required LifePRO extract(s) present | **Met** | `PPBENTYP_BenefitType_Extract_20260630.csv` in `QLA_Migration/Source/` |
| Premium component fields present | **Met** | `PREMIUMS_PAID`, `PU_PREMIUMS_PAID`, `SU_PREMIUMS_PAID`, `SL_PREMIUMS_PAID` |
| ISWL exclusion source identifiable | **Met** | `TYPE_CODE=BF` ≡ FV book (2,348 policies); aligns with PPBEN FV set |
| Converted history available for impact | **Met** | `QLA_Migration/Output/quikprmh.csv` (206,861 rows; DATEPAID 20170101–20270417) |
| Crosswalk present | **Met** | `Master_Crosswalk.csv` (e.g. 9010310404 → 010310404C) |
| Re-extract required? | **N/A** | Business chose adjustment over full PACTG re-extract |

### Field definitions

| Check | Status | Notes |
|-------|--------|-------|
| QLAdmin target table confirmed | **Met** | `quikprmh` |
| Schema / field order confirmed | **Met** | Existing schema; no new columns |
| Adjustment date confirmed | **Met** | **2017-12-31** (Eric) |
| Conversion Adjustment marker | **Met** (Dev to pick codes) | Use `MSOURCE` / `MBATCH` / `USER_ID` within schema — exact literals at Development |
| Report location confirmed | **Met** | `QLA_Migration/Reports/` (not Output) |

### Client clarification

| Check | Status | Notes |
|-------|--------|-------|
| Adjustment approach | **Met** | Single positive reconciling row |
| Four-component total | **Met** | Base + PUA + SU + SL |
| Negative handling | **Met** | Exceptions only — no load |
| ISWL scope | **Met** | Excluded phase 1 |
| Validation report | **Met** | Required |
| Open business questions | **None** | Eric agreed to all seven items |

### Evidence

| Check | Status | Notes |
|-------|--------|-------|
| Workbook example | **Met** | `docs/Copy of Premium Paid Fields.xlsx` — 010310404C Tot $17,040.05 |
| Simulation golden match | **Met** | Risk sim: HIST $1,846.20 → ADJ **$15,193.85** exact |

### Regression guards

| Check | Status | Notes |
|-------|--------|-------|
| Issue #25 MPOLICY padding | **Met** | Crosswalk + existing formatter path; no pad redesign |
| Issue #26 MPREM | **Met** | Out of scope (`quikridr`) |
| Existing `quikprmh` payment rows | **Met** | Additive only — no rewrite of history |
| ISWL history rows | **Met** | Must not receive adjustment |

---

## 2. Binding assumptions for Risk / Development

| ID | Assumption |
|----|------------|
| A1 | LifePRO total = max-per-policy of the four PPBENTYP component columns (populated on BA/PU/SU/SL rows respectively). |
| A2 | ISWL = policies with PPBENTYP `TYPE_CODE=BF` (equivalent to PPBEN FV set in current extract). |
| A3 | Idempotency via Conversion Adjustment marker — never emit a second adjustment for the same policy. |
| A4 | Policies with LP total but no current `quikprmh` rows may still receive an opening adjustment (history total = 0). |
| A5 | Exact `MSOURCE`/`USER_ID`/`MBATCH` literals chosen at Development must be documented and regression-tested. |

---

## 3. Gate decision

| Gate | Result |
|------|--------|
| **G2 — Dependencies satisfied** | **PASS** |

No client blockers. Soft Dev detail (marker field literals) does not block Risk.

**Next:** Risk Agent (Cursor Grok 4.5).
