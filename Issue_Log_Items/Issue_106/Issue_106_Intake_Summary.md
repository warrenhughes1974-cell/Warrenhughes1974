# Issue #106 — Intake Summary

**Issue:** #106 — RV Rates Off by One Duration (QuikTvs)  
**Date:** 2026-07-24  
**Framework stage:** Intake complete (G0)  
**Status:** Proceed to Planning  
**Owner:** Conversion (Warren)  
**Business status:** No-Go (Eric 7/24/2026) — client blocker

---

## Client / business symptom (verbatim)

> RV rates appear to be off by a duration. For example, policy form 170858 has rate factors for a 17 year male where the rate is 0 for Dur 1 in LifePRO and 8.76 for QLAdmin while QLAdmin has 0 for Dur 83 and LifePRO has 1000. Note this issue appears to be similar for the prior CV rate Dur issue. 1659C2 has same issue as for a 17 year male S the rate is 1 for Dur 0 in QLAdmin while LifePRO has this rate at Dur 1 (LifePRO 978.00 at Dur 83 and QL has 0). 221END and 1960OL have same issue. You may want to verify if 1L1095 are pulling the correct RV factors as I could not replicate where the values were pulling from.

Follow-up email (Eric 7/24/2026):

> The rates for the 670 GL 85-8, 670 GL85-M, and 670 GL858 appear to have their RV factors off by one duration. The 670 GL85 Rates document has screenshots from LifePRO and QLAdmin where you can see the rates are off by one year. It appears LifePRO starts with Dur 1 and QLAdmin starts with Dur 0. … RV Factor samples provide rates for 659 CEN II, 621 END85, and 960 OL which all have the same issue. Also included is L10 LP9595 RV factors; however, they look significantly different from what is in QLAdmin. If you can check where the QLAdmin RV rates for 1L1095 are pulling, I can try to research.

---

## Normalized finding

**Two defects in one report:**

### A. Duration shift (primary)

RV (Terminal Reserve) factors emit to **QuikTvs** with `ql_duration = source_duration − 1` via `source_duration_to_ql()`. LifePRO screens label the same extract duration as **Dur N**. Comparing like-named columns makes every value appear one year early.

| Source (Rate_Table RV) | Current QuikTvs |
|------------------------|-----------------|
| LifePRO Dur **N** | QLAdmin Dur **N−1** |

This is the same *symptom class* as CV Dur issues (#37/#41/#98), but **not** the CV first-duration/FNZ matrix. RV extract durations already match LifePRO year labels.

### B. `1L1095` source mismatch (trace)

Eric compared **L10 LP9595** samples to QLAdmin `1L1095`. Delivered Rate_Table has **0** rows with `LP9595`. `1L1095` QuikTvs aligns to **`L10 LP95`** (with the same −1 Dur shift). Inheritance parity evidence maps L10 issuing plans’ RV to segment `L10 LP95` → plan `1L1095`.

---

## Proof cells (current Output vs source)

Source: `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv`  
Output: `QLA_Migration/Output/rates/QuikTvs.csv`  
Diagnostic: `QLA_Migration/_research_issue106_rv_dur.py`

| Form / plan | Slice | LifePRO / source | Current QuikTvs |
|-------------|-------|------------------|-----------------|
| 670 GL85-8 → `170858` | M/17 UW 0 | Dur1=0, Dur2=**8.76**, Dur83=**1000** | Dur0=0, Dur1=**8.76**, Dur82=**1000**, Dur83 blank |
| 670 GL85-M → `17085M` | M/17 | (inherits from 170858) | Same as 170858 |
| 659 CEN II → `1659C2` | M/17 S→SM | Dur1=**1**, Dur83=**978** | Dur0=**1**, Dur82=**978**, Dur83 blank |
| 621 END85 → `221END` | M/17 | (same −1 pattern) | Dur0=0, Dur1=9.86, … |
| 960 OL → `1960OL` | M/17 | (same −1 pattern) | Dur0=4, Dur1=11, Dur82=1000 |
| L10 LP95 → `1L1095` | M/17 S | Dur1=0, Dur2=**4.45** | Dur0=0, Dur1=**4.45** |

---

## Example plans / forms

| LifePRO form / segment | QLAdmin PLAN | Role |
|------------------------|--------------|------|
| 670 GL85-8 | `170858` | Primary Dur-shift proof |
| 670 GL85-M | `17085M` | Inherited RV from 170858 |
| 670 GL858 | `170588` | Inherited RV from 170858 |
| 659 CEN II | `1659C2` | Dur-shift proof (SM) |
| 621 END85 | `221END` | Dur-shift sample |
| 960 OL | `1960OL` | Dur-shift sample |
| L10 LP95 (not LP9595) | `1L1095` | Source-trace for Eric |

---

## Suspected domain

**Rate factor duration indexing — RV → QuikTvs only.**

| Item | Value |
|------|-------|
| LifePRO TYPE_CODE | `RV` |
| QLAdmin factor table | `QuikTvs` (prefix TV) |
| Rate-key table | `QuikPlTv` (shared with NP) |
| Defect code | `qla_core/rate_dbf_schema.py` → `source_duration_to_ql` used for non-CV families |
| CV path (must not change) | `cv_remap_ql_duration` / #37/#41/#98 |

---

## Client evidence pack (repo)

| File | Content |
|------|---------|
| `docs/670 GL85 Rates.docx` | LifePRO vs QLAdmin screenshots — off by one year |
| `docs/RV Factor Samples.docx` | 659 CEN II, 621 END85, 960 OL + L10 LP9595 samples |
| `docs/QuikTvs_RsvReview_20260724.xlsx` | Client QuikTvs reserve review workbook |

---

## Related issues

| Issue | Relation |
|-------|----------|
| #37 / #41 / #98 | CV-only LifePRO duration grid; docs explicitly left QuikTvs on `source − 1` |
| #42 | PDAGE / L10 fleet completeness; LP9595 extract gap known |
| Rates Inheritance Validation | `1L1095` RV source segment = `L10 LP95` |

---

## Intake disposition

| Gate | Result |
|------|--------|
| Symptom clear | **Yes** |
| Target table clear | **Yes** — QuikTvs |
| Reproducible in Output | **Yes** |
| Blocker for Planning | **None** |

**Proceed to Planning.**
