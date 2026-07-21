# Issue #21 Open Items — Official Decisions (Locked 2026-07-09)

**Status:** DECIDED · **Engine:** v57.63 · **Authority:** Conversion lead (Warren) adopting Opus best-guess analysis as working decisions

**Source analysis:** `Issue_Log_Items/Issue_21/reports/Issue_21_Open_Items_Opus_Best_Guess_Analysis.md`

These decisions replace the prior **AWAITING CLIENT** placeholders for 21D / 21E / 21F / 21G / 21I. Client confirmation is still welcome for governance, but conversion proceeds on these rules.

---

## Decision summary

| ID | Decision | Code impact (v57.63) | Status |
|---|---|---|---|
| **21D** | ISWL Dividend Accum Int Rate = **4.50%**; non-ISWL remains **4.00%** | Already in engine (v57.36 `MDEPINT` allowlist) | **DECIDED / IMPLEMENTED** |
| **21E** | Traditional CV = **compute** from QuikCvs rates; UL = **load** `PPBEN.FV_BALANCE2` → `quikridr.MCV0` (phase 1) | New UL fund-balance enrichment | **DECIDED / IMPLEMENTED (UL load)**; traditional depends on rate tables (#40/#41) |
| **21F** | **Superseded 2026-07-11:** keep extract floor for detail rows; add **one Conversion Adjustment** `quikprmh` row (non-ISWL) so lifetime premiums paid match LifePRO | **IMPLEMENTED v57.72** | **IMPLEMENTED** |
| **21G** | Source mapping locked (client workbook); stage totals to `Reports/` until QLAdmin target field named | Staged report on full batch | **DECIDED / STAGED** |
| **21I** | Type + split already correct; **`MRELATION=1000` is intentional** (RNA has no kinship field for B1/B2) | None (rulebook default retained) | **DECIDED** |

---

## 21D — Interest crediting rate

**Decision:** Authoritative Dividend Accum Int Rate is **4.50% for all ISWL plans** and **4.00% for non-ISWL** until separately governed.

**Rationale:** Corroborated by client annotation, `PPBEN.FV_GUAR_RATE=4.50` (2,159+ ISWL rows), and CSO Mortality Crosswalk. Current output already splits 2,268 @ 4.50 / 2,815 @ 4.00.

**Code:** No change in v57.63 (v57.36 Track A remains authoritative).

---

## 21E — Cash value

**Decision (split model):**

1. **Traditional / par whole life:** Do **not** populate `MCV0/1/2`. QLAdmin **computes** cash value from **QuikCvs** rate tables (Issues #40 / #41 rate load).
2. **Universal Life / fund-value policies:** **Load** current fund balance from `PPBEN.FV_BALANCE2` onto **`quikridr.MCV0`** for **phase-1 (base)** coverage rows only.

**Rationale:** UL fund values are account balances (e.g. 010713704C ≈ $45,551.94; 010818663C ≈ $12,475.03), not tabular CV. Traditional CV is rate-driven. Leaving traditional `MCV*` blank avoids fighting QLAdmin’s compute path.

**Code (v57.63):** `qla_core/issue21_open_item_decisions.py` + quikridr enrichment in `app.py` / `QLA_Migration/app.py`.

**Still open (non-blocking):** Traditional CV display quality depends on QuikCvs completeness/parity — tracked under Issues #40/#41, not as a `quikmstr` defect.

---

## 21F — Premium history depth / conversion adjustment

**Prior decision (2026-07-09):** Accept the extract floor (~2017-01-01) for detailed payment rows — still true; full transaction replay to issue is **not** required.

**Updated decision (2026-07-11 — Eric confirmed):** Reconcile **lifetime premiums paid** by emitting **one Conversion Adjustment** `quikprmh` row per eligible **non-ISWL** policy when LifePRO total > converted history sum.

| Rule | Value |
|---|---|
| LifePRO total | `PREMIUMS_PAID` + `PU_PREMIUMS_PAID` + `SU_PREMIUMS_PAID` + `SL_PREMIUMS_PAID` (PPBENTYP) |
| Adjustment date | **2017-12-31** |
| Classification | Conversion Adjustment (not a customer payment) |
| Negatives | Exception report only — do not load |
| ISWL | Excluded from phase 1 |
| Validation | Before / adjustment / after / variance (+ components) in `Reports/` |

**Canonical package:** `Issue_Log_Items/Issue_21/Issue_21F/`

**Code:** `qla_core/issue21f_premium_adjustment.py` + batch wire in `app.py` v57.72.

---

## 21G — Total premium / cost basis

**Decision (CLOSED 2026-07-11):**

1. **Source (locked)** from `docs/Copy of Premium Paid Fields.xlsx`:
   - Traditional: `PREMIUMS_PAID` + `PU_PREMIUMS_PAID` / `TAX_BASIS` + `PU_TAX_BASIS` (PPBENTYP)
   - ISWL/UL: `FV_GUAR_DEPOSITS` / `FV_BASIS2` (PPBEN FV rows)
2. **Target:** **Not required in QLAdmin.** New Era confirmed QL does not program cost basis / taxable gains on life policies, does not withhold on life surrenders, and expects any gain/tax work outside QL (accounting). Premium history may support a manual estimate but is often incomplete on converted business.
3. **Conversion:** Do **not** load Premiums Paid / Tax Basis into a QLAdmin master field. Optional informational staging to `Reports/issue21g_premium_basis_totals.csv` may remain for reference.

**Resolution:** QLAdmin has no programmed cost basis / taxable-gain field for life policies and does not compute or withhold taxable gains on life surrenders; conversion will not load LifePRO Premiums Paid or Tax Basis into a QLAdmin master field — use premium history and/or the staged report for any manual estimate outside QL.

**Code (v57.63):** Staged report only (not in Output load package). No further mapping change.

---

## 21I — Beneficiary information

**Decision:**

1. **Mandatory:** name (`MBENFID`), type (`MTYPE` P/C), split (`MSPLIT` summing to 100% per type) — already satisfied (v57.29).
2. **`MRELATION=1000` is the correct default.** LifePRO RNA beneficiary rows carry only `RELATE_CODE` B1/B2 (primary/contingent). There is **no spouse/child/estate kinship column** in the extract. Hardcoding a fake kinship code would invent data.
3. **"Unknown 100%" must not appear** as type/split — and does not in current output.

**Code:** No change. Rulebook `Sync_Rulebook_quikbenf.csv` retains `MRELATION` default `1000`.

---

## Regression risks

| Change | Risk | Mitigation |
|---|---|---|
| UL `MCV0` load | Traditional policies incorrectly get MCV0 | Only policies with FV_BALANCE2 cache entry; phase-1 only |
| 21G report | Output folder pollution | Writes to `Reports/` only |
| 21D/I | None | Documentation / existing behavior |
| 21F adjustment (pending) | Additive `quikprmh` rows; ISWL/negatives mishandled | See Issue_21F Planning / Risk |

---

## Files touched (v57.63)

| File | Role |
|---|---|
| `qla_core/issue21_open_item_decisions.py` | Helpers: UL cache, MCV0 apply, 21G staging |
| `app.py` / `QLA_Migration/app.py` | Wire enrichment + batch report; version bump |
| This document + tracking sheets | Decision lock |

---

*Decisions locked 2026-07-09. Supersedes AWAITING CLIENT for 21D/E/F/G/I on the Issue 21 tracking sheet.*  
*21F updated 2026-07-11: conversion adjustment approach (Eric confirmed) — see `Issue_21F/Issue_21F_Business_Decisions.md`.*
