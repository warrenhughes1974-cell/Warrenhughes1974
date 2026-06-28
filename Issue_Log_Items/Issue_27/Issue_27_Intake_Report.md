# Issue #27 — Intake Report

**Issue:** SL Phase of Insurance — Apparent Duplicate Face Amount  
**Date:** 2026-06-28  
**Project version:** v57.38  
**Status:** Active / No-Go  
**Owner:** Warren  
**Client contact:** Eric  
**Stage:** Intake + Planning ✅ (no code changes)

---

## 1. Issue summary

Client reports that LifePRO benefit type **`SL` (Substandard Life)** does not represent an additional death benefit. In QLAdmin, converted policies appear to **duplicate face amount** by showing both base life coverage and an **`SL` coverage phase** with the same (or similar) amount insured.

**Example policy:** `010448806C`  
**QLAdmin screenshot (client):** Three coverage phases — `170858` (base), `1708PA` (PUA), and a second `170858` row with the same face amount as phase 1.

---

## 2. Business concern

| Concern | Detail |
|---------|--------|
| Death benefit duplication | QLAdmin may sum or display multiple phases as separate coverage |
| SL semantics | Client: SL = substandard **rating** information, not independent benefit |
| Regulatory / claims risk | Inflated amount insured on policy display |
| UAT blocker | Issue flagged **No-Go** until root cause and fix path confirmed |

---

## 3. Intake classification

| Dimension | Initial classification |
|-----------|------------------------|
| **Symptom** | Duplicate `170858` row / duplicated amount insured on Coverage tab |
| **Suspected layer** | Converter treating SL as normal `quikridr` coverage phase |
| **Not initially suspected** | quikplan product setup, quikmstr modal premium, DBF packaging |
| **Evidence type** | Client QLAdmin screenshot + LifePRO source trace |

---

## 4. Scope boundaries (this stage)

**In scope:**
- Source trace for `010448806C`
- Fleet impact for `BENEFIT_TYPE = SL`
- Converter behavior analysis
- Proposed surgical fix (planning only)

**Out of scope:**
- Code, rulebook, crosswalk, or DBF changes
- QLAdmin runtime rating engine changes
- Premium recalculation

---

## 5. Key source systems

| Extract | Table | Relevance |
|---------|-------|-----------|
| `PPBEN_PolicyBenefit_Extract_20260530.csv` | PPBEN | Benefit rows, units, VPU, premium, `BENEFIT_TYPE`, `BENEFIT_SEQ` |
| `PPBENTYP_BenefitType_Extract_20260530.csv` | PPBENTYP | `SL_TABLE_CODE`, `SL_2ND_TABLE_CODE`, substandard metadata |
| `QLA_Migration/Output/quikridr.csv` | QUIKRIDR | Converted coverage phases (`MPHASE` = `BENEFIT_SEQ`) |
| `Sync_Rulebook_quikridr.csv` | Rulebook | `BENEFIT_SEQ` → `MPHASE`; units → `MUNIT`/`MVPU` |

---

## 6. Terminology note

Internal status-analysis catalog lists `SL` as **"Supplemental Life"**. Client and PPBENTYP evidence (`SL_TABLE_CODE`) support **Substandard Life / table rating**. Planning treats **client definition as authoritative** for Issue #27.

---

## 7. Trace policy assigned

**Primary:** `010448806C` (LifePRO `9010448806`)  
**Secondary samples:** Policies in `Issue_27_SL_Impact_Population.csv`

---

## 8. Deliverables index

| # | File |
|---|------|
| 1 | `Issue_27_Intake_Report.md` (this document) |
| 2 | `Issue_27_Root_Cause_Analysis.md` |
| 3 | `Issue_27_Impact_Analysis.md` |
| 4 | `Issue_27_Proposed_Fix.md` |
| 5 | `Issue_27_Risk_Assessment.md` |
| 6 | `Issue_27_Next_Stage_Prompt.md` |

---

**Intake status:** ✅ COMPLETE — proceed to Ownership Decision / Dependency Gate per findings.
