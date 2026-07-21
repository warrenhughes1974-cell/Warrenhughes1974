# CFIC Issue #01 — Dependency Gate

**Issue:** CFIC #01 — Green-Sheet Non-Forfeiture / Reserve Rate Extraction  
**Framework stage:** Dependency Gate (G2)  
**Date:** 2026-07-11  
**Planning reference:** `CFIC_Issue_01_Planning_Report.md`  
**Intake reference:** `CFIC_Issue_01_Intake_Summary.md`

---

## 1. Checklist

### Source data

| Check | Status | Notes |
|-------|--------|-------|
| Green-sheet PDFs present | **Met** | 1,105 PDFs in 16 zips; 1,104 extractable |
| Inventory documented | **Met** | `evidence/cfic_issue01_pdf_inventory.csv` |
| Column layout documented | **Met** | P7MN sample + `docs/cash_value_extraction_plan.md` |
| Access checkpoint CSVs present | **Met** | `extracted/PermaLife*.csv`, `Quest.csv` |
| Plan crosswalk present | **Met** | `Citizens_Plan_Crosswak.xlsx` — 35/37 exact match |
| Re-extract required? | **N/A** | Source is PDF archive, not LifePRO |

### Field definitions

| Check | Status | Notes |
|-------|--------|-------|
| QLAdmin factor table targets confirmed | **Met** | `QuikCvs`, `QuikTvs`, `QuikNps` per `rate_dbf_schema.py` |
| QLAdmin key table targets confirmed | **Met** | `QuikPlCv`, `QuikPlTv` |
| Green-sheet column semantics | **Met** | 9 body columns + 3 header fields documented |
| Segmentation rules (suffix → GENDER/UWCLASS) | **Partial** | Proposed; juvenile suffixes need walkthrough |
| Transformation (duration paging, factor format) | **Met** | `duration_to_cntl_col()`, `format_factor()` |
| Rate-key assumption values | **Missing** | OBQ-2 — blocks emit |

### Client clarification

| Check | Status | Notes |
|-------|--------|-------|
| Scope boundary agreed | **Met** | Green sheets only; Warren conversion out of scope |
| Factor basis (per $1,000) | **Missing** | OBQ-1 |
| ETI mapping | **Missing** | OBQ-3 |
| Mean reserve handling | **Missing** | OBQ-4 |
| Expiry-age / consolidated PDF rules | **Missing** | OBQ-5, OBQ-6 |
| Access walkthrough §4–§5 | **Missing** | `docs/access_app_walkthrough.md` checklist open |
| UAT acceptance criteria | **Met** (coverage-level) | OCR accuracy ≥99.5%; CV parity at checkpoints; Warren tables unchanged |

### Evidence

| Check | Status | Notes |
|-------|--------|-------|
| Example policies | **N/A** | Plan/age traces substitute |
| Screenshots / sample renders | **Met** | `CFIC_Cash_Values/_sample_pdfs/P7MN_18.pdf` |
| Before-state measurable | **Met** | No QLAdmin CFIC rates loaded today |
| Inventory script | **Met** | `scripts/research_cfic_issue01_inventory.py` |

### Regression guards

| Check | Status | Notes |
|-------|--------|-------|
| Warren `QLA_Migration/Output/` untouched | **Met** | Hard scope rule |
| Warren `app.py` untouched | **Met** | CFIC work under `CFIC_Rates/` only |
| Issue #25 MPOLICY padding | **Met** | N/A — no policy tables |
| Issue #26 MPREM mapping | **Met** | N/A — no premium tables |

---

## 2. Gate decision

| Gate | Result |
|------|--------|
| **G2 — Dependencies satisfied (full program)** | **NOT MET** — OBQ-1, OBQ-2, OBQ-3, OBQ-4, OBQ-5, OBQ-6, walkthrough |
| **G2 — Wave 1 extract pilot** | **CONDITIONAL MET** — pending Risk Agent Conditional Go |

**Status recommendation:** **Blocked — Awaiting Client Clarification** (for QLAdmin emit)  
**Parallel path:** **Ready for Risk Review** (for Wave 1 extract pilot)

---

## 3. Blockers summary

| ID | Blocker | Blocks |
|----|---------|--------|
| OBQ-1 | Factor basis | QLAdmin emit |
| OBQ-2 | Rate-key assumptions | QLAdmin key tables |
| OBQ-3 | ETI mapping | NFO emit |
| OBQ-4 | Mean reserve | Mean reserve emit |
| OBQ-5 | 802M expiry-age rule | 802M emit |
| OBQ-6 | Consolidated sheet split | ALP/GDB/P8/P9 emit |
| OBQ-7 | R69G crosswalk | R69G emit |
| — | Access walkthrough incomplete | Assumption sign-off |

**Not blocked:** PDF inventory, P7MN OCR extract pilot, staging CSV creation, Access parity checks.

---

## 4. Recommended next agent

**Risk Agent** on Cursor Grok 4.5:

```
Proceed to Risk Agent for CFIC Issue #01.

Read AI_Agents/Risk_Agent.md. Scope CFIC_Rates/ only. No code.
Deliver CFIC_Issue_01_Risk_Review_Report.md.
Recommend Conditional Go for Wave 1 (P7MN extract pilot only).
Hold Wave 3 QLAdmin emit until OBQ-1 and OBQ-2 resolved.
```

**Do not proceed to Development** until Risk approves Wave 1.

---

## 5. Client actions needed (parallel)

1. Complete Access walkthrough §4–§5 (`docs/access_app_walkthrough.md`)
2. Answer OBQ-1 and OBQ-2 (minimum for any QLAdmin load)
3. Confirm green sheets are authoritative over Access illustrations (OBQ-8)
4. Add `R69G` to crosswalk or confirm obsolete (OBQ-7)
