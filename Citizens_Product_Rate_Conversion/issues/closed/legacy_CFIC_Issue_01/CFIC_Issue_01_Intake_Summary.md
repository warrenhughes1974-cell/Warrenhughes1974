# CFIC Issue #01 — Intake Summary

**Issue:** CFIC #01 — Green-Sheet Non-Forfeiture / Reserve Rate Extraction  
**Program:** Citizens / CFIC Rates (`CFIC_Rates/`)  
**Date:** 2026-07-11  
**Framework stage:** Intake complete (G0)  
**Status:** Approved → Planning  
**Owner:** Conversion (Warren) · **Assigned:** Warren  
**Business status:** No-Go for Development until G1 + G2 + G3  

---

## 1. Business symptom (verbatim + normalized)

**Business request (normalized):**

Citizens whole-life and related products require **full-duration** non-forfeiture and reserve rate tables in QLAdmin. The authoritative source is a library of scanned **green-sheet PDFs** (`CFIC_Cash_Values/`) containing terminal reserve, mean reserve, cash value, paid-up, extended term insurance, and related columns by plan code and issue age.

The Access **CFI Proposal Maker** database (`extracted/*.csv`) carries **premium rates** and only **sparse illustration checkpoints** (`CashValueIn10`, `CashValueIn20`, `CashValueAt65`, etc.) — not the full duration grids needed for QLAdmin rate tables.

**Example policies:** None provided (rate-table issue; plan/age traces substitute).

---

## 2. Suspected domain

| Layer | Path / artifact | Role |
|-------|-----------------|------|
| Primary source | `CFIC_Cash_Values/*_CV.zip`, `MultipleCashValueFiles.zip` | Scanned NF/reserve green sheets (~1,105 PDFs) |
| Checkpoint source | `extracted/PermaLife*.csv`, `Quest.csv` | Sparse CV/paid-up illustration columns for parity |
| Premium source (separate future issue) | `extracted/FiveYearTerm.csv`, etc. | Proposal premiums — **not CFIC #01 scope** |
| Plan crosswalk | `Citizens_Plan_Crosswak.xlsx` | CFIC plan code → QLPlan |
| QLAdmin targets | `QuikCvs`, `QuikTvs`, `QuikNps`, `QuikPlCv`, `QuikPlTv` | Factor + rate-key tables per `qla_core/rate_dbf_schema.py` |
| Warren conversion | `QLA_Migration/` | **Out of scope** for CFIC #01 |

**Domain:** Rates — Citizens CFIC track. **Not** Warren policy conversion, claims, or memo.

---

## 3. Intake evidence (measured)

| Check | Result |
|-------|--------|
| Green-sheet PDFs present | **Yes** — 1,105 PDFs across 16 zip archives |
| Extractable PDFs (excl. Directions) | **1,104** |
| Distinct CV product folders | **37** |
| Crosswalk match (exact) | **35 / 37** products |
| Crosswalk missing | **R69G**, **Table of Days** (802W metadata PDF) |
| PDF text layer | **None** — image-only; OCR required |
| Layout sample (P7MN/18.pdf) | Header: PLAN `P7MN`, ISSUE AGE `18`; body: DUR + 9 numeric columns |
| Unit basis on sheet | `CURRENT INFORCE = 1,000.00` (per-$1,000 likely) |
| Target platform decided | **QLAdmin** — `docs/target_platform.md` (2026-07-08) |
| All products active | **Yes** — `docs/product_catalog.md` |

Evidence:

- `evidence/cfic_issue01_pdf_inventory.csv`
- `evidence/cfic_issue01_product_summary.csv`
- `evidence/cfic_issue01_crosswalk_match.csv`
- `docs/cash_value_extraction_plan.md`

---

## 4. In scope / out of scope

### In scope

- Inventory all green-sheet PDFs and naming patterns
- OCR/extract **all columns** per duration row into staging CSV
- Map columns to QLAdmin rate families: CV, terminal reserve, paid-up (+ staged ETI/NFO)
- Validate via OCR spot-checks and Access illustration checkpoints
- Emit draft `QuikCvs` / `QuikTvs` / `QuikNps` + key tables under `CFIC_Rates/output/rates/` (after business gates)

### Out of scope (CFIC #01)

- Warren LifePRO → QLAdmin policy conversion (`QLA_Migration/app.py`, rulebooks, Output/)
- Access premium rate load (`extracted/*.csv` → `QuikGps`) — future **CFIC #02**
- Citizens QLAdmin sandbox import / production cutover — future integration issue
- Hand-keying 1,100 PDFs at scale
- Wholesale OCR without validation gates

---

## 5. Related work

| Reference | Relationship |
|-----------|--------------|
| `docs/cash_value_extraction_plan.md` | Technical extraction blueprint (feeds Planning) |
| `docs/access_app_walkthrough.md` | Rate meaning + assumption collection checklist |
| `docs/target_platform.md` | QLAdmin target decided |
| `qla_core/rate_dbf_schema.py` | QLAdmin physical schema reference (Warren repo; reuse for emit format) |
| Warren Issue #40 | CV rate load pattern for LifePRO — **reference only**, not same source |
| Warren Issue #48 | Rate source authority — **reference only** |

---

## 6. Immediate blockers visible at intake

| Blocker | Severity |
|---------|----------|
| Rate-key assumptions (`MORT`, `NFOINT`, `RSVINT`, etc.) not collected | **High** — blocks QLAdmin key-table load |
| ETI years/days → QLAdmin table mapping undefined | **Medium** — blocks NFO emit |
| Factor basis (per $1,000) not business-confirmed | **Medium** |
| Access walkthrough §4–§5 not completed | **Medium** |
| OCR pipeline not built | **Expected** — Development wave 1 |

**No blocker** on starting read-only inventory or P7MN extract pilot after Risk Conditional Go.

---

## 7. Gate G0 — Intake complete

- [x] Issue folder created: `CFIC_Rates/Issue_Log/CFIC_Issue_01/`
- [x] Intake summary written
- [x] Example policies: none (plan/age traces in Planning)
- [x] Owner assigned: Warren
- [x] No code or Warren conversion changes made

**Next:** Planning Agent (G1) — complete.
