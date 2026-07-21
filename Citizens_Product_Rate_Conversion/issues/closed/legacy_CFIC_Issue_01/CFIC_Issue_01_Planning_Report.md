# CFIC Issue #01 — Planning Report

**Issue:** CFIC #01 — Green-Sheet Non-Forfeiture / Reserve Rate Extraction  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning complete — proceed to Dependency Gate  
**Generated:** 2026-07-11  
**Agent:** Planning Agent (read-only research)  
**Intake reference:** `CFIC_Issue_01_Intake_Summary.md`

---

## 1. Executive finding

**Confirmed need:** Citizens requires full-duration non-forfeiture and reserve factors in QLAdmin. The authoritative source is **1,104 extractable scanned PDFs** in `CFIC_Cash_Values/` — not the Access Proposal Maker CSVs, which only carry sparse illustration checkpoints.

**Confirmed approach:** One OCR pass per PDF → wide **staging CSV** (all green-sheet columns) → validated emit to `QuikCvs`, `QuikTvs`, `QuikNps` (+ companion key tables) using `qla_core/rate_dbf_schema.py` paging and factor formatting. Work stays under `CFIC_Rates/`; Warren `QLA_Migration/` is untouched.

**Architecture (locked SD-1):** **One-time standalone extract** — standalone scripts only; **no `app.py` integration**, no batch pipeline wiring, no `APP_VERSION` bump.

**Recommended direction:** Pilot on **P7MN** (3–5 issue ages) to prove OCR + staging + Access parity before scaling to all 37 product folders. Development proceeds in **three gated waves** (extract pilot → P7* family → QLAdmin emit).

**Go/no-go for Development:** **No-Go until G2 + G3** for QLAdmin emit. **Conditional Go** expected for Wave 1 extract-only pilot after Risk review.

---

## 2. Confirmed source table/file(s)

| Source | File / pattern | In repo? | Grain | Rows / files |
|--------|----------------|----------|-------|-------------|
| Green sheets (primary) | `CFIC_Cash_Values/*_CV.zip` | Yes | Plan + issue age + duration | 1,104 PDFs |
| Green sheets (additional) | `MultipleCashValueFiles.zip` | Yes | Mixed (consolidated + all-ages) | 21 PDFs |
| Illustration checkpoints | `extracted/PermaLife7AdultBefore.csv` | Yes | Age × Sex × Smoker | 212 |
| Illustration checkpoints | `extracted/PermaLife8Adult.csv` | Yes | Age × Sex × Smoker | 212 |
| Illustration checkpoints | `extracted/Quest.csv` | Yes | Age × plan variant | 76 |
| Plan crosswalk | `Citizens_Plan_Crosswak.xlsx` | Yes | CFIC plan → QLPlan | 111 rows |
| QLAdmin schema reference | `qla_core/rate_dbf_schema.py` | Yes (Warren repo) | Table layouts | N/A |

### Green-sheet columns (confirmed from P7MN/18.pdf sample)

| Column | Staging field | Notes |
|--------|---------------|-------|
| PLAN CODE (header) | `source_plan` | e.g. `P7MN` |
| ISSUE AGE (header) | `issue_age` | e.g. `18` |
| FIRST YEAR NET (header) | `first_year_net` | Stage only |
| DUR | `duration` | 1-based policy year |
| RENEWAL NET | `renewal_net` | Often constant per age |
| TERMINAL RESERVE | `terminal_reserve` | Decimal |
| MEAN RESERVE | `mean_reserve` | Decimal |
| CASH VALUE | `cash_value` | Decimal |
| PAID UP | `paid_up` | Integer |
| EXT INS - YRS | `eti_years` | Integer |
| EXT INS - DAYS | `eti_days` | Integer |
| PURE END | `pure_end` | Decimal |
| CURRENT INFORCE | `inforce_unit` | Usually `1000` |

### PDF naming patterns (inventory)

| Pattern | Count | Examples |
|---------|------:|----------|
| `age_pdf` | 972 | `P7MN/18.pdf`, `PLP/0.pdf` |
| `other` | 86 | `802W/Table of Days.pdf` |
| `consolidated` | 29 | `ALP2/Cash Value Sheets.pdf` |
| `expiry_age` | 14 | `802M/Exiry Age 90.pdf` |
| `all_ages` | 3 | `1015/0-99.pdf` |
| `directions` | 1 | `802M/Directions.pdf` (skip) |

Evidence: `evidence/cfic_issue01_pdf_inventory.csv`, `evidence/cfic_issue01_product_summary.csv`

---

## 3. Confirmed QLAdmin target structure

Per `qla_core/rate_dbf_schema.py` (physical DBF layouts confirmed in Warren repo):

### Factor tables (19-field grid)

`PLAN(C6) AGE(C2) CNTL(C2) <PFX0..PFX9>(C7) GENDER(C1) UWCLASS(C2) BAND(C2) ISSCNTRY(C4) ISSUEST(C2) EFFDATE(D8)`

| Green-sheet column | QLAdmin factor table | Prefix | Key table |
|--------------------|---------------------|--------|-----------|
| CASH VALUE | `QuikCvs` | `CV0`–`CV9` | `QuikPlCv` |
| TERMINAL RESERVE | `QuikTvs` | `TV0`–`TV9` | `QuikPlTv` |
| PAID UP | `QuikNps` | `NP0`–`NP9` | `QuikPlTv` (shared) |
| EXT INS (TBD) | Stage → `QuikNff` or plan NFO | `NFF0`–`NFF9` (CHAR 10) | None |
| MEAN RESERVE | Staging only (initially) | — | — |
| RENEWAL / FIRST YEAR NET | Staging only (initially) | — | — |

### Rate-key assumption fields (business-supplied)

| Key table | Fields |
|-----------|--------|
| `QuikPlCv` | `MORT`, `ETIMORT`, `NFOINT`, `INTMETHCV` |
| `QuikPlTv` | `MORT`, `RSVINT`, `RSVMETH`, `INTMETHTV`, `STOREMEANS`, `CALCMIDS` |

### Duration paging

- Sheet duration (1-based) → QL duration (0-based): `ql_duration = duration - 1`
- `CNTL = ql_duration // 10`; column = `ql_duration % 10`
- Factor text: `format_factor()` — CHAR(7), no magnitude scaling

---

## 4. Required source-to-target field mapping

| Green-sheet source | Staging field | QLAdmin target | Transformation | Emit wave |
|--------------------|---------------|----------------|----------------|-----------|
| PLAN CODE | `source_plan` | `PLAN` | Crosswalk → `QLPlan` (e.g. `P7MN` → `10P7MN`) | All |
| ISSUE AGE | `issue_age` | `AGE` | Zero-pad to C2 | All |
| Suffix in plan code | — | `GENDER`, `UWCLASS` | `MN`→M/NS, `MS`→M/SM, etc. | All |
| DUR | `duration` | `CNTL` + factor col | Page/col split | All |
| CASH VALUE | `cash_value` | `QuikCvs.CVn` | `format_factor()` | Wave 3 |
| TERMINAL RESERVE | `terminal_reserve` | `QuikTvs.TVn` | `format_factor()` | Wave 3 |
| PAID UP | `paid_up` | `QuikNps.NPn` | `format_factor()` | Wave 3 |
| MEAN RESERVE | `mean_reserve` | Staging CSV | None until business decides | — |
| ETI YRS/DAYS | `eti_years`, `eti_days` | Staging CSV | NFO mapping TBD | — |
| PURE END | `pure_end` | Staging CSV | Optional future table | — |
| CURRENT INFORCE | `inforce_unit` | Metadata | Confirms per-$1,000 basis | Audit |

### Segmentation rules (proposed — confirm in walkthrough)

| Plan suffix | GENDER | UWCLASS |
|-------------|--------|---------|
| `FN`, `MN` | F / M | `NS` |
| `FS`, `MS` | F / M | `SM` |
| `FJ`, `MJ` | F / M | TBD (juvenile) |

Defaults: `BAND=01`, `ISSCNTRY=0000`, `ISSUEST=00`, `EFFDATE=19000101`

### Crosswalk gaps

| CV product | Status | Action |
|------------|--------|--------|
| R69G | Missing from crosswalk | Add row or confirm alias before emit |
| Table of Days | Not a plan — metadata PDF in 802W zip | Skip extraction |

35 of 37 products have exact crosswalk matches. Evidence: `evidence/cfic_issue01_crosswalk_match.csv`

### Fields / systems that must remain unchanged

| Target | Touch this issue? |
|--------|-------------------|
| Warren `QLA_Migration/Output/quik*.csv` | **No** |
| Warren `app.py` / rulebooks | **No** |
| Issue #25 MPOLICY padding | **No** (N/A — no policy tables) |
| Issue #26 MPREM mapping | **No** (N/A — no premium tables) |

---

## 5. Open client questions

See `CFIC_Issue_01_Open_Business_Questions.md` for the formal blocker list.

Summary:

1. **OBQ-1** — Confirm all factors are per $1,000 face (sheet shows `CURRENT INFORCE = 1,000`)
2. **OBQ-2** — Provide `QuikPlCv` / `QuikPlTv` assumption values per Citizens plan
3. **OBQ-3** — ETI years + days: `QuikNff`, plan NFO setup, or other?
4. **OBQ-4** — Mean reserve: load vs QLAdmin derive via `STOREMEANS`/`CALCMIDS`
5. **OBQ-5** — Expiry-age PDFs (`802M/Exiry Age {n}.pdf`): mapping rule to issue age
6. **OBQ-6** — Consolidated mega-sheets (`ALP2`, `GDB`): acceptable split strategy
7. **OBQ-7** — Add `R69G` to plan crosswalk or confirm obsolete
8. **OBQ-8** — Green sheets vs Access illustrations: which is authoritative when they differ?

---

## 6. Recommended formatting rules

| Rule | Recommendation |
|------|----------------|
| Plan code | Crosswalk `CFIC Plan` → `QLPlan`; 6-char PLAN field |
| Age | C2 zero-padded (`18` → `18`, `8` → `08`) |
| Duration paging | 0-based QL duration; 10 factors per CNTL page |
| Money / factors | CHAR(7) text via `format_factor()`; no scaling |
| Paid-up integers | Stage as-is; confirm per-$1,000 vs absolute before emit |
| Blanks / zeros | Preserve sheet zeros (CV often 0 for early durations) |
| OCR confidence | Flag rows below threshold; do not silently emit |

---

## 7. Memo / text / special handling

**N/A** — rate factors only. No MEMOKEY, long text, or policy-level fields.

---

## 8. Policy number key handling

**N/A for CFIC #01** — this is a plan-rate load, not a policy conversion. Validation uses **plan + age + gender + UWCLASS + duration** traces, not policy numbers.

---

## 9. Estimated record counts

| Metric | Estimate | Basis |
|--------|----------:|-------|
| Source PDFs (extractable) | 1,104 | Inventory |
| Product folders | 37 | Inventory |
| Avg durations per PDF | ~50–65 | P7MN sample (2 pages, ~49 rows) |
| Staging rows (total) | ~55,000–72,000 | 1,104 × ~50–65 |
| QuikCvs rows (emit) | ~5,500–7,200 | Staging ÷ 10 (CNTL paging) per family |
| QuikTvs rows | ~5,500–7,200 | Same paging |
| QuikNps rows | ~5,500–7,200 | Same paging |
| Distinct QL plans (after crosswalk) | ~35+ | Crosswalk match |

---

## 10. Sample trace (plan/age checkpoints — no policies)

Access illustration checkpoints for **P7MN** (Male, Non-smoker, age 18) vs green-sheet pilot target:

| Trace key | Access PL7 `CashValueIn10` | Access PL7 `CashValueIn20` | Access PL7 `CashValueAt65` | Green-sheet (pilot) | Status |
|-----------|---------------------------:|---------------------------:|---------------------------:|---------------------|--------|
| P7MN / age 18 / M / NS / DUR 10 | 21 | — | — | OCR `cash_value` @ DUR=10 | **Pending pilot** |
| P7MN / age 18 / M / NS / DUR 20 | — | 84 | — | OCR `cash_value` @ DUR=20 | **Pending pilot** |
| P7MN / age 18 / M / NS / DUR 47* | — | — | 433 | OCR `cash_value` @ DUR=(65−18) | **Pending pilot** |

\*Duration at age 65 = `65 − issue_age` for issue-age-based grids (confirm per product).

Paid-up parity (same key):

| Checkpoint | Access PL7 `PaidUpIn10` | Access PL7 `PaidUpIn20` | Access PL7 `PaidUpAt65` |
|------------|------------------------:|------------------------:|------------------------:|
| P7MN age 18 M NS | 197 | 514 | 898 |

Pilot must confirm whether Access checkpoints align to PL7 or PL8 tables (premiums identical; illustrations differ per `product_catalog.md`).

---

## 11. Risks and unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| OCR numeric errors on green-bar scans | **High** | P7MN pilot + 99.5% spot-check gate; confidence flags |
| Wrong age key on expiry-age / consolidated PDFs | **High** | Per-family templates; manual review of pattern `expiry_age` / `consolidated` |
| Missing rate-key assumptions | **High** | Dependency Gate block on QLAdmin emit; staging still proceeds |
| Access vs green-sheet authority conflict | **Medium** | OBQ-8; green sheets treated as authoritative for full grid |
| Crosswalk gap (`R69G`) | **Low** | Resolve before emit |
| Accidental Warren merge | **High** | Hard rule: output only under `CFIC_Rates/output/rates/` |
| Scope creep into premium rates | **Medium** | Defer to CFIC #02 |

---

## 12. Development waves (do not implement yet)

### Wave 1 — Extract pilot (Conditional Go after Risk)

- Products: `P7MN` only
- Ages: 18, 30, 50 (3 PDFs)
- Output: `CFIC_Rates/extracted_green_sheets/staging/P7MN/{age}.csv`
- Script home: `CFIC_Rates/Issue_Log/CFIC_Issue_01/scripts/`
- **No** QLAdmin emit; **no** Warren changes

### Wave 2 — P7* family normalize

- Products: `P7FN`, `P7FS`, `P7MN`, `P7MS` (252 PDFs)
- Output: full P7 staging + `evidence/cfic_issue01_ocr_audit.csv`

### Wave 3 — QLAdmin emit (requires G2 clearance on OBQ-1, OBQ-2)

- Emit: `CFIC_Rates/output/rates/QuikCvs.csv`, `QuikTvs.csv`, `QuikNps.csv`, `QuikPlCv.csv`, `QuikPlTv.csv`
- Reuse `qla_core/rate_dbf_schema.py` paging/format helpers (import or copy — surgical)

### Product rollout after P7 (Planning order)

1. `P8*`, `P9*` — consolidated sheets in `MultipleCashValueFiles.zip`
2. `PLP`, `PLP6`
3. `R28G`, `R68G`, `RW8`, `R29G`, `RW9G`
4. `ABF*`, `802M`, `802W`
5. `ALP2`, `ALP6`, `GDB`, `101*`

---

## 13. Dependency Gate preview

| Check | Met? |
|-------|------|
| Source PDFs present | **Met** |
| Column headers / layout documented | **Met** (sample + plan doc) |
| QLAdmin target tables confirmed | **Met** (schema reference) |
| Plan crosswalk present | **Met** (2 gaps documented) |
| Rate-key assumptions | **Missing** |
| ETI / mean reserve mapping | **Missing** |
| Access walkthrough complete | **Missing** |
| Example policies | **N/A** (plan/age traces) |

**Expected G2 outcome:** **Partial pass** — Wave 1 extract approved; Wave 3 emit blocked.

---

## 14. Recommended Risk Agent prompt

```
Proceed to Risk Agent for CFIC Issue #01 — Green-Sheet NF/Reserve Rate Extraction.

Read AI_Agents/Risk_Agent.md and AI_Agents/Templates/Risk_Report_Template.md.
Scope: CFIC_Rates/ only. Do NOT touch QLA_Migration or Warren conversion.

Deliver CFIC_Rates/Issue_Log/CFIC_Issue_01/CFIC_Issue_01_Risk_Review_Report.md.

Quantify:
- OCR error risk and false-load impact
- Warren blast radius (must be zero)
- Wave 1 Conditional Go for P7MN extract pilot
- Wave 3 hold until OBQ-1 and OBQ-2 resolved
```

---

## 15. Recommended Development task (do not implement)

1. Build OCR/extract script for P7MN ages 18, 30, 50 (layout-aware, all columns)
2. Write staging CSV per `docs/cash_value_extraction_plan.md` schema
3. Produce `evidence/cfic_issue01_ocr_audit.csv` with 20-cell spot-check per column
4. Compare CV/paid-up at durations 10, 20, 65-age vs Access `PermaLife7AdultBefore.csv`
5. **Do not** emit QLAdmin tables until OBQ-2 cleared
6. **Do not** modify `QLA_Migration/app.py` or Warren Output

Validation script (future): `CFIC_Rates/Issue_Log/CFIC_Issue_01/scripts/validate_cfic_issue01_p7mn_pilot.py`

---

## Appendix

| Artifact | Path |
|----------|------|
| Inventory script | `scripts/research_cfic_issue01_inventory.py` |
| PDF inventory | `evidence/cfic_issue01_pdf_inventory.csv` |
| Product summary | `evidence/cfic_issue01_product_summary.csv` |
| Crosswalk match | `evidence/cfic_issue01_crosswalk_match.csv` |
| Extraction plan | `../../docs/cash_value_extraction_plan.md` |
| Schema reference | `../../../qla_core/rate_dbf_schema.py` |

**Future CFIC issues (out of scope):** CFIC #02 Access premium rates; CFIC #03 QLAdmin integration / load package.
