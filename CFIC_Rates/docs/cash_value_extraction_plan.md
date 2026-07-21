# CFIC Green-Sheet Extraction Plan — Full Non-Forfeiture / Reserve Values

**Status:** PLANNING (no production code yet)  
**Date:** 2026-07-11  
**Source:** `CFIC_Cash_Values/*.zip` (scanned PDF green sheets)  
**Target platform:** QLAdmin rate tables (see `docs/target_platform.md`)  
**Related:** `Citizens_Plan_Crosswak.xlsx`, `extracted/*.csv` (Access proposal tool), `qla_core/rate_dbf_schema.py`

---

## Purpose

Citizens / CFIC **Non-Forfeiture and Reserve Values** green sheets are the authoritative full-duration rate source for whole-life and related products. Unlike the Access `CFIProposalMakerRev2.mdb` tables (which carry only sparse illustration columns such as `CashValueIn10`, `CashValueIn20`, `CashValueAt65`), these PDFs contain **complete duration grids** for:

- Terminal reserve
- Mean reserve
- Cash value
- Paid-up (reduced paid-up)
- Extended term insurance (years + days)
- Pure endowment
- Renewal net (and first-year net in the header)

This plan defines how to **extract all columns once**, land them in a staging layer, validate them, and emit QLAdmin-compatible rate files.

**Do not** merge into Warren `QLA_Migration/Output/` until Citizens plan/rate crosswalk and business sign-off are complete (per `README.md`).

---

## Source inventory

### Location

| Path | Contents |
|------|----------|
| `CFIC_Cash_Values/*_CV.zip` | 15 product packs (~1,079 PDFs) |
| `CFIC_Cash_Values/MultipleCashValueFiles.zip` | 21 additional product PDFs (often one mega-sheet per product) |

### Naming patterns (by product family)

| Pattern | Example | Interpretation |
|---------|---------|----------------|
| `{PLAN}/{age}.pdf` | `P7MN/18.pdf` | One issue age per file |
| `{PLAN}/Exiry Age {n}.pdf` | `802M/Exiry Age 90.pdf` | Expiry-age variant (confirm mapping to issue age) |
| `{PLAN}/0.pdf`, `01.pdf` … | `PLP/0.pdf` | Age or index encoded in filename (confirm per product) |
| `{PLAN}/0-99.pdf` | `1015/0-99.pdf` | All ages on one sheet |
| `{PLAN}/Cash Value Sheets.pdf` | `ALP2/Cash Value Sheets.pdf` | Multi-age consolidated sheet |
| `Directions.pdf` | `802M/Directions.pdf` | Metadata only — skip for factor extraction |

### Document characteristics

- **Image-only PDFs** — no text layer; OCR or layout-aware extraction required.
- **Fixed green-bar layout** — monospaced columns, consistent headers.
- **Header metadata:** `PLAN CODE`, `ISSUE AGE`, `FIRST YEAR NET`, print date.
- **Body columns:** DUR + numeric factors (see below).
- **Unit basis:** `CURRENT INFORCE` is typically `1,000.00` → factors are almost certainly **per $1,000 face**.

### Plan code → QLPlan crosswalk

Use `Citizens_Plan_Crosswak.xlsx` (`CFIC Plan` → `QLPlan`). Some crosswalk rows group multiple CFIC codes (e.g. `P7FN, P7FS, P7MN, P7MS`). Suffix letters on plan codes likely encode **gender and smoker** (see Segmentation).

---

## Green-sheet column inventory

Each page is a **full non-forfeiture / reserve pack** for one plan key + issue age (or expiry-age variant).

| # | Green-sheet column | Typical content | Staging field | QLAdmin target (proposed) |
|---|-------------------|-----------------|---------------|---------------------------|
| H1 | PLAN CODE | e.g. `P7MN` | `source_plan` | → `PLAN` via crosswalk |
| H2 | ISSUE AGE | e.g. `18` | `issue_age` | → `AGE` |
| H3 | FIRST YEAR NET | e.g. `1.531100` | `first_year_net` | Stage; premium support — **not** a duration grid |
| 1 | DUR | Policy year 1…n | `duration` | Index for all factor tables |
| 2 | RENEWAL NET | Often flat per age | `renewal_net` | Stage; confirm vs premium tables |
| 3 | TERMINAL RESERVE | Decimal factors | `terminal_reserve` | **`QuikTvs`** (+ `QuikPlTv`) |
| 4 | MEAN RESERVE | Decimal factors | `mean_reserve` | Stage always; QLAdmin may derive mean — see Open Decisions |
| 5 | CASH VALUE | Decimal factors | `cash_value` | **`QuikCvs`** (+ `QuikPlCv`) |
| 6 | PAID UP | Integer face amount | `paid_up` | **`QuikNps`** (RPU amount table) |
| 7 | EXT INS - YRS | Integer years | `eti_years` | Stage → NFO / ETI mapping — see Open Decisions |
| 8 | EXT INS - DAYS | Integer days | `eti_days` | Stage → NFO / ETI mapping — see Open Decisions |
| 9 | PURE END | Often zero | `pure_end` | Stage; load only if product uses pure endowment |
| 10 | CURRENT INFORCE | Usually `1,000.00` | `inforce_unit` | Metadata — confirms per-$1,000 basis |

**Principle:** Extract **all columns in one OCR pass**. Do not run separate CV-only, reserve-only, or NFO-only extraction jobs.

---

## Segmentation (plan suffix → QLAdmin keys)

Plan suffix letters on CFIC codes (e.g. `P7MN`, `P7MS`, `ABFN`, `ABFS`) likely map to QLAdmin segmentation:

| Suffix pattern | Proposed GENDER | Proposed UWCLASS |
|----------------|-----------------|------------------|
| `FN`, `MN` | `F` / `M` | `NS` (non-smoker) |
| `FS`, `MS` | `F` / `M` | `SM` (smoker) |
| `FJ`, `MJ` | `F` / `M` | Juvenile — confirm UWCLASS |
| Unsuffixed / numeric | Confirm per product | Confirm per product |

Defaults unless business overrides:

- `BAND` = `01`
- `ISSCNTRY` = `0000`
- `ISSUEST` = `00`
- `EFFDATE` = `19000101` (matches existing rate pipeline convention)

---

## Staging layer (canonical intermediate)

All extracted data lands here **before** QLAdmin emit. Re-OCR should never be required to change mapping rules.

### Proposed folder layout

```
CFIC_Rates/
  CFIC_Cash_Values/          # source zips (read-only archive)
  extracted_green_sheets/
    inventory.csv            # every PDF: product, path, pages, naming pattern
    staging/
      {source_plan}/
        {issue_age}.csv      # one wide file per plan+age after OCR
    audit/
      ocr_confidence.csv     # low-confidence cells flagged for review
      manual_spot_checks.csv # human-verified sample cells
  validation/
    parity_access.csv        # vs Access CashValueIn10/20/At65 where available
    parity_green_sheet.csv   # OCR vs manually keyed cells
  mapping/
    plan_crosswalk.csv       # from Citizens_Plan_Crosswak.xlsx
    suffix_segmentation.csv  # FN/FS/MN/MS → GENDER/UWCLASS
  output/
    rates/                   # emitted QuikCvs, QuikTvs, QuikNps, QuikPl* (draft)
```

### Staging row schema (wide format)

One row per `(source_plan, issue_age, duration)`:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `source_plan` | text | Yes | From header or folder name |
| `ql_plan` | text | Yes | From crosswalk |
| `issue_age` | int | Yes | From header or filename |
| `duration` | int | Yes | DUR column (1-based on sheet) |
| `renewal_net` | decimal | No | |
| `terminal_reserve` | decimal | No | |
| `mean_reserve` | decimal | No | |
| `cash_value` | decimal | No | |
| `paid_up` | int | No | |
| `eti_years` | int | No | |
| `eti_days` | int | No | |
| `pure_end` | decimal | No | |
| `inforce_unit` | decimal | No | Expected 1000 |
| `gender` | text | Yes | From suffix rules |
| `uwclass` | text | Yes | From suffix rules |
| `band` | text | Yes | Default `01` |
| `source_file` | text | Yes | Original PDF path |
| `source_page` | int | Yes | Page within PDF |
| `extract_method` | text | Yes | e.g. `azure_di`, `tesseract_v1` |
| `extract_confidence` | decimal | No | Per-row or per-cell score |

### QLAdmin duration paging

QLAdmin factor tables hold **10 durations per row** (`CV0`–`CV9`, `TV0`–`TV9`, `NP0`–`NP9`, etc.) with `CNTL` as the page number.

Use the same paging rules as `qla_core/rate_dbf_schema.py`:

- Source duration (1-based on sheet) → QL duration (0-based): `ql_duration = duration - 1`
- Page + column: `CNTL = ql_duration // 10`, column index = `ql_duration % 10`
- Factor formatting: `format_factor()` — CHAR(7) text, no magnitude scaling

---

## QLAdmin emit targets

### Confirmed factor table families (from `rate_dbf_schema.py`)

| Family | Factor table | Key table | Prefix | Factor width |
|--------|-------------|-----------|--------|--------------|
| Cash value | `QuikCvs` | `QuikPlCv` | `CV` | CHAR(7) |
| Terminal reserve | `QuikTvs` | `QuikPlTv` | `TV` | CHAR(7) |
| Net premium / paid-up | `QuikNps` | `QuikPlTv` (shared key) | `NP` | CHAR(7) |
| Non-forfeiture factor | `QuikNff` | *(no QuikPl companion)* | `NFF` | CHAR(10) |

### Emit priority (recommended)

| Phase | Tables | Source columns | Rationale |
|-------|--------|----------------|-----------|
| 1 | `QuikCvs` + `QuikPlCv` | CASH VALUE | Highest business value; Access has sparse checkpoints |
| 2 | `QuikTvs` + `QuikPlTv` | TERMINAL RESERVE | Core reserve basis |
| 3 | `QuikNps` | PAID UP | RPU non-forfeiture option |
| 4 | ETI / pure end | EXT INS YRS/DAYS, PURE END | Requires NFO table / plan setup confirmation |
| — | Staging only | MEAN RESERVE, RENEWAL NET, FIRST YEAR NET | Audit / parity; mapping TBD |

### Rate-key assumptions (business-supplied per plan)

Factor tables require companion **key** rows with actuarial assumptions that **do not exist on the green sheets**:

| Key table | Required assumption fields |
|-----------|---------------------------|
| `QuikPlCv` | `MORT`, `ETIMORT`, `NFOINT`, `INTMETHCV` |
| `QuikPlTv` | `MORT`, `RSVINT`, `RSVMETH`, `INTMETHTV`, `STOREMEANS`, `CALCMIDS` |

These must be collected during the Access walkthrough or from Citizens actuarial records before QLAdmin load.

---

## Pipeline phases

### Phase 0 — Inventory (½ day)

- [ ] Unzip all packs into a read-only catalog (do not duplicate 2+ GB in git)
- [ ] Build `inventory.csv`: product folder, file name, page count, naming pattern, skip flags (`Directions.pdf`)
- [ ] Join inventory to `Citizens_Plan_Crosswak.xlsx`
- [ ] Flag products with non-standard layouts (ALP, GDB, 802 expiry-age, consolidated `0-99` sheets)

### Phase 1 — OCR pilot on P7MN (2–3 days)

**Why P7MN first:** one PDF per issue age, consistent layout, crosswalk hit confirmed.

- [ ] Extract 3–5 ages (e.g. 18, 30, 50) via layout-aware OCR
- [ ] Capture **all columns** per row
- [ ] Manual spot-check: 20 cells per column vs rendered PDF
- [ ] Compare CV at durations 10, 20, and at age 65 vs Access `PermaLife7AdultBefore.csv` / `PermaLife8Adult.csv` where keys align

**Pilot acceptance criteria:**

| Check | Pass threshold |
|-------|----------------|
| Header plan/age matches folder | 100% |
| Duration sequence complete (no gaps) | 100% |
| OCR numeric accuracy (spot-check) | ≥ 99.5% per column |
| CV parity vs Access illustration columns | Exact match at checkpoint durations |
| Low-confidence rows flagged | 100% of rows below threshold |

### Phase 2 — Normalize all P7* packs (1 week)

- [ ] Roll proven template to `P7FN`, `P7FS`, `P7MN`, `P7MS`
- [ ] Apply suffix → GENDER/UWCLASS rules
- [ ] Emit draft `QuikCvs.csv` + `QuikPlCv.csv` (and `QuikTvs` / `QuikNps` if assumptions available)

### Phase 3 — Remaining product families (2–4 weeks)

Process in complexity order:

1. `P8*`, `P9*` — same layout family as P7
2. `PLP`, `PLP6` — filename index encoding
3. `R28G`, `R68G`, `RW8`, `R29G`, `RW9G`
4. `ABF*`, `802M`, `802W` — expiry-age naming
5. `ALP2`, `ALP6`, `GDB`, `101*` — consolidated mega-sheets (hardest)

### Phase 4 — QLAdmin emit + validation (ongoing)

- [ ] Pack staging rows into factor tables using `duration_to_cntl_col()` + `format_factor()`
- [ ] Schema validation against `qla_core/rate_dbf_schema.py`
- [ ] Row-count and monotonicity audits per plan/age
- [ ] Sandbox import test (when Citizens QLAdmin environment is available)

---

## OCR / extraction approach

### Recommended strategy

Green-bar sheets are **highly structured** but **image-only**. Best approach:

1. **Preprocess:** deskew, contrast boost, green-bar neutralization
2. **Layout-aware OCR** with column geometry (not free-form LLM vision on the full corpus)
3. **Template per layout family** — P7-style, expiry-age style, consolidated style

### Tool options (pilot → scale)

| Tool | Role | Notes |
|------|------|-------|
| Azure Document Intelligence | Pilot + production | Strong on tables; pay-per-page |
| Google Document AI | Alternative pilot | Similar table extraction |
| Tesseract + OpenCV | Local fallback | Cheaper at scale once column crops are fixed |
| Manual re-key | Last resort | Only for failed/low-confidence pages |

### Do not

- Hand-type 1,100 PDFs
- Run separate extraction jobs per QLAdmin family
- Merge draft output into Warren `QLA_Migration/Output/`
- Emit QLAdmin files without rate-key assumptions

---

## Validation matrix

| Validation | Source A | Source B | When |
|------------|----------|----------|------|
| Header identity | OCR header | Folder/filename | Every PDF |
| Duration completeness | Staging | Expected max duration per product | Every plan+age |
| Numeric spot-check | Staging | Human reads PDF | Pilot + 5% sample |
| CV checkpoint parity | Staging | Access `CashValueIn10/20/At65` | Where Access keys exist |
| Monotonicity | Staging | Prior duration row | CV, terminal reserve |
| Factor width | Emitted CSV | CHAR(7) / CHAR(10) fit test | Pre-load |
| Segmentation | Suffix rules | Walkthrough confirmation | Per product family |
| Non-candidate isolation | N/A | Warren QLA tables unchanged | Always |

---

## Open business decisions

Resolve before Development / QLAdmin load:

| # | Question | Options | Impact |
|---|----------|---------|--------|
| 1 | **Factor basis** | Per $1,000 (likely) vs per unit | All emitted factors |
| 2 | **Mean reserve** | Load to staging only vs derive in QLAdmin via `STOREMEANS`/`CALCMIDS` | Whether mean_reserve becomes a table |
| 3 | **ETI years + days** | `QuikNff` vs plan NFO setup vs combined factor | Extended term option accuracy |
| 4 | **Pure endowment** | Load vs ignore for initial release | Scope |
| 5 | **Renewal net / first-year net** | Premium table vs illustration-only | Whether `QuikGps` gets a separate pass |
| 6 | **Expiry-age PDFs (802*)** | Map expiry age → issue age rule | Age key correctness |
| 7 | **Consolidated sheets (ALP, GDB)** | Split by age during OCR vs manual segmentation | Hardest products |
| 8 | **Rate-key assumptions** | Source for MORT, RSVINT, NFOINT, etc. | Blocks `QuikPlCv` / `QuikPlTv` load |
| 9 | **PL7 vs PL8** | Both in scope (confirmed active) | Duplicate CV sets |
| 10 | **Paid-up integer basis** | Per $1,000 face vs absolute dollars | `QuikNps` scaling |

---

## Relationship to existing CFIC work

| Existing asset | Role in this plan |
|----------------|-------------------|
| `extracted/*.csv` | Sparse illustration checkpoints for CV validation |
| `docs/product_catalog.md` | Product scope (all active) |
| `docs/access_app_walkthrough.md` | Rate meaning, assumption collection |
| `Citizens_Plan_Crosswak.xlsx` | CFIC plan → QLPlan |
| `qla_core/rate_dbf_schema.py` | QLAdmin physical layout + paging + factor format |
| `qla_core/rate_emit.py` | Reference emit pattern (Warren LifePRO — adapt for CFIC staging) |

---

## Next actions

1. **Business:** Schedule Access walkthrough items §4–§5 (rate meaning, green-sheet authority, assumptions).
2. **Planning:** Run Phase 0 inventory script (read-only) and publish `inventory.csv`.
3. **Pilot:** OCR 3 P7MN ages; publish first `staging/P7MN/*.csv` + spot-check audit.
4. **Decision:** Resolve open items 1, 2, 3, and 8 before first QLAdmin emit.

---

## Revision history

| Date | Change |
|------|--------|
| 2026-07-11 | Initial plan — full-sheet extraction (CV + reserves + NFO columns) |
