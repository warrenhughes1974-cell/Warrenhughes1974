# Issue #33 — ISWL QUIKISSC Research Summary

**Issue:** #33 — ISWL Phase 6 QUIKISSC (Surrender Charges)  
**Date:** 2026-06-28  
**Mode:** Research and planning only — no code changes  
**Prerequisites:** Issue #31 (PR-1–PR-4 rate tables) **CLOSED**; Issue #32 PR-5 QUIKUINT **APPROVED**

---

## Executive summary

QUIKISSC maps LifePRO **Full Surrender / Surrender Load** segment data to QLAdmin **`QuikIssc`** (ISWL Surrender Charges, Help **§7.144**).

**Hierarchy proof status:** **STRONG EVIDENCE** — all 8 ISWL coverages wire **SR** and **SL** on hub segment **`659 CEN II`** via PCOVRSGT → PSEGT (8/8 each). **U7/U8 absent** (0/8). **TP/TX withdrawn** as surrender candidates (tax valuation/reserve only).

**Rate source status:** **CORRELATION ONLY** — **26 rows** correlate on hub (`659 CEN II`): Rate_Table **TYPE_CODE=SL** (14 rows, duration 1–14) + PDAGE SL (12 rows, all zero floats). PSEGT **SL `SEGT_DATA`** payload embeds `SLD000` and **`OSLNS00XT`** (likely rate-table pointer). **Segment-to-rate linkage not yet proven** — do not emit from TYPE_CODE alone.

**QLAdmin schema:** **CONFIRMED** from `QLAdmin_Help.pdf` §7.144 — wide duration columns **SCHG01–SCHG20**, index **PLAN + GENDER + UWCLASS + BAND + ISSCNTRY + ISSUEST**.

**Recommendation:** **CLOSED — APPROVED (PR-6, 2026-07-01).** See [`Issue_33_PR6_Closure_Report.md`](Issue_33_PR6_Closure_Report.md).

---

## 1. LifePRO storage model

### Mandatory hierarchy (Product Book + segment trace)

```text
PPRDF (not in repo — optional)
  ↓
PCOMP (PRODUCT_ID = ISWL coverage)
  ↓
PCOVR (COVERAGE_ID, POLICY_FORM_NUM)
  ↓
PCOVRSGT (SEGT_FLAG=Y → SEGT_ID)
  ↓
PSEGT (SEGMENT_ID + SEGT_TYPE)
  ↓
Rate tables (Rate_Table / PDAGE / segment constants in SEGT_DATA)
  ↓
Policy Form Crosswalk → MPLAN
  ↓
QuikIssc
```

**Non-negotiable rule:** Never map surrender charges from **TYPE_CODE alone**. Prove **PCOVRSGT → PSEGT(SR/SL) → rate rows** before emit.

### Product Book segment semantics

| Code | Meaning | QUIKISSC role |
|------|---------|---------------|
| **SR** | Full Surrender Segment (parent; may access lower segments) | **Primary** — hierarchy parent |
| **SL** | Full Surrender Load Segment (child) | **Primary** — schedule holder |
| **U7** | Legacy surrender load / fees | **Fallback** — absent for ISWL |
| **U8** | Legacy surrender load / percentages | **Fallback** — absent for ISWL |
| **TP** | Tax Valuation Premiums | **Excluded** — not surrender |
| **TX** | Tax Reserve Factors | **Excluded** — not surrender |

Product Book documents **SR → SL** as the preferred modern path; U7/U8 replaced by SL via SR in newer setups.

---

## 2. PSEGT findings (20260629 extract)

**File:** `QLA_Migration/Source/PSEGT_Segment_Extract_20260629.csv` (696 rows)

| SEGT_TYPE | Global segment IDs | ISWL 8/8 | Classification |
|-----------|-------------------|:--------:|----------------|
| **SR** | `659 CEN II`, `668 SPWL` | **8/8** | **CONFIRMED** |
| **SL** | `659 CEN II`, `668 SPWL` | **8/8** | **CONFIRMED** |
| **U7** | — | **0/8** | Not found |
| **U8** | — | **0/8** | Not found |
| **TP** | 11 segments | 8/8 | Confirmed — **NOT QUIKISSC** |
| **TX** | 11 segments | 8/8 | Confirmed — **NOT QUIKISSC** |

**Hub segment:** `659 CEN II` — shared UL dictionary (U5, U6, BP, CV, A1, G1, LN, SR, SL, UF, …) inherited by all eight ISWL coverages through PCOVRSGT slots.

### PSEGT payload decode (planning pass — not authoritative)

**SL row (`659 CEN II`, SL):**

```text
SEGT_DATA (ASCII): 659 CEN IISLD000 ... OSLNS00XT ... PN.I ... F ...
SEGT_KEY0:         659 CEN IISL
```

**SR row (`659 CEN II`, SR):**

```text
SEGT_DATA (ASCII): 659 CEN IISRY659 CEN II  N  Y659 CEN II  N  N  N  N ...
SEGT_KEY0:         659 CEN IISR
```

**Interpretation (CORRELATION ONLY):** SR payload references `659 CEN II` with Y/N child flags; SL payload references **`OSLNS00XT`** — candidate rate-table identifier. **SME must confirm** pointer semantics before loader uses Rate_Table SL rows.

---

## 3. Rate table evidence

### PAAGERAT

**No SR, SL, SC, SUR, or ISSC** TYPE_CODE exists in PAAGERAT. QUIKISSC will **not** use the PAAGERAT attained-age scalar loader pattern (unlike QUIKCOI/QUIKGCOI).

### Rate_Table TYPE_CODE=SL (hub `659 CEN II`)

**File:** `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv`

| Dimension | Value |
|-----------|-------|
| Rows | **14** |
| COVERAGE_ID | `659 CEN II` |
| TYPE_CODE | `SL` |
| GENDER | M only |
| AGE | 0 (issue age placeholder) |
| UWCLASS | S (Smoker) |
| BAND | 1 |
| DURATION | 1–14 |
| VALUE | Percent schedule (see below) |

**Duration schedule (Male / Band 1 / UW S):**

| Duration | VALUE |
|----------|------:|
| 1 | 100.0000 |
| 2 | 100.0000 |
| 3 | 70.0000 |
| 4 | 60.0000 |
| 5 | 50.0000 |
| 6 | 40.0000 |
| 7 | 30.0000 |
| 8 | 20.0000 |
| 9 | 15.0000 |
| 10 | 10.0000 |
| 11 | 8.0000 |
| 12 | 6.0000 |
| 13 | 4.0000 |
| 14 | 2.0000 |

**Note:** Rate_Table `SL` is in `EXCLUDED_TYPE_CODES` for the WL CV pipeline — inventory only until segment proof completes.

### PDAGE TYPE_CODE=SL (hub)

**File:** `QLA_Migration/Source/PDAGE_AgeDuration_Rates_Extract_20260530.csv`

- **12 rows** for `659 CEN II` / SL — durations 1–12
- **VALUE1_FLOAT = 0.0** for all — **not authoritative** for surrender emit

### TP/TX (withdrawn)

| Source | Hub rows | Status |
|--------|----------:|--------|
| PDAGE TP/TX | 2,128 each | **Do not use** for QUIKISSC |
| Rate_Table TP/TX | 19,780 each | **Do not use** for QUIKISSC |

---

## 4. QLAdmin QuikIssc (Help §7.144)

**Source:** `docs/claims_conversion_reference/QLAdmin_Help.pdf` — QuikIssc, PDF page index 832, Help **§7.144**

| Field | Type | Len | Description |
|-------|------|-----|-------------|
| PLAN | C | 6 | Plan code |
| AGE | N | 3 | Attained age |
| GENDER | C | 1 | M, F, J, U |
| UWCLASS | C | 2 | Underwriting class |
| BAND | C | 2 | Insurance band |
| ISSCNTRY | C | 4 | Issue country |
| ISSUEST | C | 2 | Issue state |
| SCHG01–SCHG20 | N | 8.4 | Surrender charge by **duration 1–20** |

**Index key:** `PLAN + GENDER + UWCLASS + BAND + ISSCNTRY + ISSUEST`  
(**AGE is not in the index** — confirm SME whether AGE=0 means “all ages” or age-rated expansion is required.)

---

## 5. Provisional transform (pending SME)

```text
For each ISWL MPLAN in allowlist:
  1. PCOVRSGT → PSEGT gate: SR and SL resolve (8/8)
  2. Decode SL SEGT_DATA rate pointer → authoritative rate table
  3. Load surrender schedule (duration-indexed percentages)
  4. Pivot DURATION 1..N → SCHG01..SCHGN
  5. Emit QuikIssc row(s) per PLAN + dimension tuple
```

**Provisional field mapping:**

| QuikIssc field | LifePRO source (provisional) |
|----------------|------------------------------|
| PLAN | Crosswalk MPLAN |
| AGE | Rate row AGE (0 in hub extract) |
| GENDER | Rate row SEX |
| UWCLASS | Rate row UNDERWRITING_CLASS → QLA UW code |
| BAND | Rate row BAND |
| ISSCNTRY | Default `0000` (no filing variation in extract) |
| ISSUEST | Default `00` |
| SCHG01..SCHG14 | Rate_Table SL VALUE at DURATION 1..14 |
| SCHG15..SCHG20 | Blank or zero unless source extends |

---

## 6. Scope estimate (provisional)

| Metric | Low estimate | High estimate | Basis |
|--------|-------------:|--------------:|-------|
| ISWL MPLANs | 8 | 8 | Fleet allowlist |
| Rows per MPLAN | 1 | 8+ | Shared hub schedule vs gender/UW expansion |
| **Total QuikIssc rows** | **8** | **64+** | 8 × (M/F × NS/SM × bands) if fully expanded |
| Duration columns populated | 14 | 14 | Rate_Table hub SL |
| Rate dimensions | **Policy year / duration** | Not attained-age PAAGERAT | Help SCHG01–20 labels |

**Working hypothesis (QUIKUINT pattern):** All 8 MPLANs share the **same** surrender schedule from hub `659 CEN II` → **8 rows** (one per MPLAN, M/S/Band1/0000/00) with 14 SCHG columns populated. **SME must confirm.**

---

## 7. Relationship to other QLAdmin tables

| Table | Relationship |
|-------|--------------|
| **QuikPlan** | Plan-level variation flags (surrender charge applicability) — not yet traced for ISWL |
| **QuikCvs** | Cash value floor — fund value less surrender charge should not fall below tabular CV where applicable (master ref §) |
| **QuikDvs** | Dividend variation — separate from surrender schedule |
| **QuikIswl** | UL/ISWL Values (Help §7.146) — related product family; not surrender schedule |
| **QuikIsrr** | Partial surrender (Help §7.143) — adjacent but separate target |

---

## 8. Policy-level validation fields (not yet traced)

For post-emit reconciliation:

- `PPBENTYP.BF_CURR_SURR_LOAD`
- `PPRBNUL.SURR_LOAD`, `PPRBNUL.LAPSE_SURR_LOAD`
- `PFNDD.SURRENDER_LOAD`

---

## 9. Research artifacts referenced

| Artifact | Path |
|----------|------|
| PSEGT extract | `QLA_Migration/Source/PSEGT_Segment_Extract_20260629.csv` |
| Segment trace matrix | `docs/research/ISWL_Segment_Trace/ISWL_Segment_Trace_Matrix.csv` |
| Row counts | `docs/research/ISWL_Segment_Trace/ISWL_Segment_Row_Counts.csv` |
| Issue #31 extract validation | `Issue_Log_Items/Issue_31/Issue_31_Extract_Validation_Report.md` |
| Product Book addendum | `docs/research/ISWL_Product_Book_Manual_Findings_Addendum.md` |
| Gap report §5 | `docs/research/ISWL_Implementation_Gap_Report.md` |
| Forensic absence proof | `Issue_Log_Items/Issue_ISWL_Research/ISWL_Forensic_Evidence_Matrix.csv` |

---

## 10. Final recommendation

**READY AFTER SME CONFIRMATION**

Hierarchy (SR/SL 8/8) and QuikIssc schema are documented. Rate pointer decode, percent literal format, dimensional scope, and SR→SL→Rate_Table proof remain open SME gates. Do **not** begin development until gates close (mirror Issue #32 QUIKUINT pattern).
