# ISWL Product Book Manual Findings Addendum

**Date:** 2026-06-28  
**Authority:** LifePRO Product Book manual reference (`Product.pdf` — Product Usage / segment definitions)  
**Baseline documents:**  
- `docs/research/ISWL_LifePRO_to_QLAdmin_Master_Reference.md`  
- `docs/research/ISWL_Implementation_Gap_Report.md`  
- May 20260530 ZIP research (`docs/research/ISWL_Zip_Research_Executive_Summary_20260530.md`)

**Purpose:** Add LifePRO Product Book manual findings to the ISWL conversion research baseline and revise prior source-data assumptions where the manual contradicts or clarifies extract-based inferences.

**Note on manual access:** Segment definitions below follow the LifePRO Product Book (`Product.pdf`) as supplied for this research pass. The PDF is not stored in the repo; PDDIC extracts did **not** provide an equivalent TYPE_CODE dictionary. Manual definitions supersede prior **inferred** TYPE_CODE meanings until SME confirms CSO’s ISWL setup matches the book.

**May ZIP segment-trace caveat:** The May 20260530 extract includes `PPRDF`, `PCOMP`, `PCOVR`, `PCOVRSGT`, rate files (`PAAGE`, `PAAGERAT`, `PDAGE`, `PRBEN*`), but **did not include** `PSEGT` or `PDINT`/`PDINTTBL` as separate files. **Update 2026-06-29:** Client supplied `PSEGT`, `PDINT`, and `PDINTTBL` in `QLA_Migration/Source/` — segment trace is now authoritative for PSEGT-mapped codes. See Issue #31 follow-up report.

---

## 1. Treat ISWL as UL / Interest Sensitive Whole Life setup

The Product Book supports treating ISWL as part of the **Universal Life / Interest Sensitive Whole Life** processing family, not as ordinary traditional whole life only.

For ISWL, inspect UL-style setup and processing, including:

- credited interest  
- guaranteed interest  
- fund value  
- current COI  
- guaranteed COI  
- NAR (net amount at risk)  
- corridor  
- surrender loads  
- billable premium  
- premium loads  
- monthly expense charges  
- monthaversary rules  

This supports the need for more than `QUIKCVS`. ISWL likely requires UL-style QLAdmin tables/rules such as:

```text
QUIKUINT
QUIKCOI
QUIKGCOI
QUIKISSC
QUIKGPS
expense/load handling
```

**Impact on prior research:** Confirms the gap report finding that WL-only rate pipeline (`CV`/`PR`/`NP`/`RV`/`DB`/`DV`) is **insufficient** for full ISWL product setup. Partial implementations (`quikplan.NFOINT`, `quikdvdp.MDEPINT`, `QuikCvs`) do not satisfy UL governance (`QUIKUINT` required per `Data_Goverence.txt`).

---

## 2. Product setup must be traced through LifePRO hierarchy

Do **not** directly map `PAAGERAT` or `PDAGE` rows to QLAdmin output based only on `TYPE_CODE`.

The Product Book confirms LifePRO product setup is built through:

```text
Product -> Component -> Coverage -> Segments -> Rates
```

For source data, trace:

```text
PPRDF -> PCOMP -> PCOVR -> PCOVRSGT -> PSEGT -> rate tables
```

Rate tables may be:

```text
PAAGE / PAAGERAT
PDAGE
PDINT / PDINTTBL
PRBEN / PRBENINT
```

A rate row is **not authoritative for ISWL** until the segment path proves what it represents.

**Impact on prior research:** Reverses the extract-first workflow used in ZIP/forensic analysis (TYPE_CODE grep → QLA target hypothesis). All prior TYPE_CODE→target mappings are **candidates only** pending segment trace.

---

## 3. Product Usage Cross Reference / lower-level segments matter

The Product Book describes Product Usage Cross Reference and higher/lower segment relationships. Product elements can include:

```text
Product
Component
Coverage
Segment
Attained Age Rate
Age/Duration Rate
Declared Interest Rate
```

Some segments are not standalone; they may access **lower-level** segments.

**Important example for ISWL surrender:**

```text
SR -> SL
```

- `SR` = Full Surrender Segment (can access lower-level segments)  
- `SL` = Full Surrender Load Segment  

For ISWL, do not search isolated segment/type codes in isolation. Trace higher/lower segment relationships where applicable.

---

## 4. Correct the prior TYPE_CODE / segment assumptions

### NC — **REVISED (contradicts prior COI assumption)**

| | |
|---|---|
| **Manual meaning** | `NC` = **Net Premium Credited Segment** |
| **Prior assumption** | PAAGERAT `TYPE_CODE=NC` ≈ current COI (690 ISWL rows) |
| **Revision** | **Do not treat NC as current COI.** NC relates to net premium credited / premium crediting behavior. Do not map to `QUIKCOI` unless segment linkage proves the extract uses `NC` differently from the manual. |

### U6 — **REVISED (strengthens current COI path)**

| | |
|---|---|
| **Manual meaning** | `U6` = **Current COI Rates Segment** |
| **Prior assumption** | Mixed: segment doc said U6=current COI, but extract analysis treated `TYPE_CODE=U6` as **guaranteed** COI candidate |
| **Revision** | **U6 is the stronger current COI candidate**, not guaranteed COI. Distinguish **LifePRO segment type U6** from **rate table `TYPE_CODE=U6`** — but manual strongly supports U6 as current COI. May extract: **800 ISWL rows** with `TYPE_CODE=U6` (658 CEN I, 659 CEN II only) — candidate for U6 segment resolution, not direct emit. |

### U5 — **REVISED (new primary GCOI path)**

| | |
|---|---|
| **Manual meaning** | `U5` = **Guaranteed COI Rates Segment** |
| **Prior assumption** | U5 mentioned in master ref but extract work focused on `TYPE_CODE=U6` for GCOI |
| **Revision** | **Search U5 first for guaranteed COI.** Do not assume `TYPE_CODE=U6` is guaranteed COI. May extract: **200 ISWL rows** with `TYPE_CODE=U5` in PAAGERAT (plus 417 global) — aligns better with manual than U6 for `QUIKGCOI`. |

### BP — **STRENGTHENED**

| | |
|---|---|
| **Manual meaning** | `BP` = **Billable Premium Segment** |
| **Prior assumption** | BP inferred as gross premium candidate (1,164 ISWL PAAGERAT rows) |
| **Revision** | **BP is a credible ISWL billable/premium candidate**, stronger than PR for this extract. Segment linkage must still prove whether BP feeds `QUIKGPS`. |

### PR — **CONFIRMED ABSENT IN EXTRACT**

| | |
|---|---|
| **Manual meaning** | `PR` = **Premium Segment** |
| **Prior finding** | Zero ISWL rows for `PR` in Rate_Table, PAAGERAT, PDAGE |
| **Revision** | PR remains the **standard** premium segment in LifePRO, but **not the ISWL source** in available extracts. Do not expect ISWL GP from current PR loader path. |

### TP — **REVISED (remove as surrender candidate)**

| | |
|---|---|
| **Manual meaning** | `TP` = **Tax Valuation Premiums** |
| **Prior assumption** | PDAGE `TYPE_CODE=TP` (2,128 ISWL rows) possible surrender candidate |
| **Revision** | **Do not treat TP as surrender charge.** Tax valuation premium data. Remove from primary `QUIKISSC` candidates unless SME proves client-specific reuse. |

### TX — **REVISED (remove as surrender candidate)**

| | |
|---|---|
| **Manual meaning** | `TX` = **Tax Reserve Factors** |
| **Prior assumption** | PDAGE `TYPE_CODE=TX` (2,128 ISWL rows) possible surrender candidate |
| **Revision** | **Do not treat TX as surrender charge.** Tax reserve factor data. Remove from primary `QUIKISSC` candidates. |

### SR / SL — **PREFERRED SURRENDER PATH**

| | |
|---|---|
| **Manual meaning** | `SR` = Full Surrender Segment; `SL` = Full Surrender Load Segment |
| **Revision** | **SR → SL is the preferred starting path for ISWL surrender setup.** Better than TP/TX. |

### U7 / U8 — **FALLBACK SURRENDER**

| | |
|---|---|
| **Manual meaning** | `U7` = Full Surrender Load / Fees; `U8` = Full Surrender Load / Percentages |
| **Revision** | Fallback/legacy paths if SR/SL absent. Manual notes U7/U8 were older monthaversary functionality, replaced by SL via SR in newer setup. |

---

## 5. Revised ISWL table/segment assumption baseline

Use this table for all future ISWL research (replaces prior inference list in master reference §6–7):

| Code | Manual meaning | QLA target hypothesis |
|------|----------------|----------------------|
| NC | Net Premium Credited — **NOT current COI** | Premium crediting — not QUIKCOI |
| U6 | Current COI Rates Segment | **QUIKCOI** (via segment trace) |
| U5 | Guaranteed COI Rates Segment | **QUIKGCOI** (via segment trace) |
| BP | Billable Premium Segment | **QUIKGPS** (via segment trace) |
| PR | Premium Segment — zero ISWL extract rows | Standard segment; not ISWL GP source here |
| TP | Tax Valuation Premiums — **NOT surrender** | Do not use for QUIKISSC |
| TX | Tax Reserve Factors — **NOT surrender** | Do not use for QUIKISSC |
| SR | Full Surrender Segment | **QUIKISSC** path (parent) |
| SL | Full Surrender Load Segment | **QUIKISSC** path (child) |
| U7 / U8 | Legacy surrender load fees/pct | QUIKISSC fallback |
| CV | Cash Values Segment | **QUIKCVS** |
| A1 | Current Interest Rate Segment | **QUIKUINT** (credited) |
| G1 | Guaranteed Interest Rate Segment | **QUIKUINT** (guaranteed) |
| LN | Loan Interest Rates Segment | **QUIKUINT** (loan) |
| UF | Per Policy Monthly Expense | Expenses |
| U1 | Premium Collection Expenses / Fees | Expenses |
| U2 | Premium Collection Expenses / Percent Premium Load | Expenses |
| U3 | Per Thousand Expense Load | Expenses |
| G2 | Guaranteed Percentage of Premium Load | Expenses / loads |
| G3 | Guaranteed Per 1000 of Face | Expenses / loads |
| GF | Guaranteed Monthly Policy Fee | Expenses |

---

## 6. COI setup is more complex than one table lookup

For current and guaranteed COI, inspect more than U5/U6 rate rows alone.

**Additional segments to check:**

```text
U6  = Current COI Rates Segment
U5  = Guaranteed COI Rates Segment
MR  = MPR COI Rate Rules Segment
NR  = NAR Calculation Method
FC  = Fund Contract Rules
UL  = Universal Life Corridor Segment
UI  = Monthaversary Control Segment
```

ISWL COI may depend on: death benefit, fund value, NAR, corridor, monthly COI rate, fund allocation, monthaversary timing, specified amount increases, parent benefit rules.

**Do not load `QUIKCOI` or `QUIKGCOI`** until segment setup points to COI rates and rate shape (attained age vs duration) is understood.

---

## 7. NAR and corridor logic may matter

Inspect for ISWL:

```text
NR = NAR Calculation Method
UL = Universal Life Corridor Segment
UI = Monthaversary Control Segment
DB = Death Benefits Segment
FC = Fund Contract Rules
```

COI charges generally apply to **Net Amount at Risk**, not face amount alone. Confirm whether QLAdmin expects rates only or full plan setup for NAR/corridor behavior.

---

## 8. Premium and expense logic may be connected

Expense/load segments may nest inside billable premium or UL premium calculations.

**Expense/load segments:** U1, U2, U3, UF, G2, G3, GF  

**Premium/billable premium segments:** BP, BI, PR, UG, UH, UX, UY, UZ, MP  

Do not search only for standalone expense tables. Inspect whether expenses are referenced from BP/BI/UG/UH/UX/UY/UZ premium logic.

**Impact on gap report:** `quikridr.MANNLFEE` (Issue #21C) may capture one policy fee dimension but likely **not** the full UF/U1/U2/U3/G2/G3/GF product expense structure.

---

## 9. Surrender should trace through SR/SL first

| Priority | Path |
|----------|------|
| **Preferred** | `SR -> SL` |
| **Fallback** | `U7` / `U8` |
| **Do not use** | `TP` / `TX` as surrender unless SME proves client-specific usage |

Prior ZIP research listing TP/TX as `QUIKISSC` candidates is **superseded** by this addendum.

---

## 10. Cash values remain strongest

Manual: `CV` = Cash Values Segment.

May ZIP evidence (unchanged): `PDAGE TYPE_CODE=CV` — **12,084 ISWL rows**.

Continue treating CV as strongest `QUIKCVS` candidate. Current implementation uses April `Rate_Table_Extract_20260427.csv`. **Before changing routing:**

1. Compare Rate_Table CV vs May PDAGE CV by coverage, duration, band, age, sex, UW class, value.  
2. Document whether May PDAGE can replace Rate_Table for production.  
3. Obtain business sign-off.

---

## 11. Rate type determines source table

Manual rate-type logic:

| Rate type | Meaning | Likely source file |
|-----------|---------|-------------------|
| A | Attained Age | Attained Age Rate File (`PAAGE` / `PAAGERAT`) |
| I | Issue Age | Attained Age Rate File |
| O | Duration Only | Age/Duration Rate File (`PDAGE`) |
| D | Age and Duration | Age/Duration Rate File (`PDAGE`) |

**Do not assume source table from TYPE_CODE alone.** Inspect segment rate setup for each ISWL table family.

---

## 12. Updated mapping guidance by QLAdmin target

### QUIKCVS

- **Likely source:** CV segment → `PDAGE TYPE_CODE=CV` or Rate_Table CV  
- **Status:** Implemented via Rate_Table; May PDAGE not wired  
- **Action:** Parity study before routing change  

### QUIKCOI

- **Revised likely source:** **U6** segment → PAAGE/PAAGERAT or PDAGE (per rate type)  
- **Do not use:** NC as COI  
- **Action:** Trace `PCOVRSGT` for U6; resolve to rate file; confirm dimensions  

### QUIKGCOI

- **Revised likely source:** **U5** segment → PAAGE/PAAGERAT or PDAGE  
- **Do not assume:** `TYPE_CODE=U6` = guaranteed COI  
- **Action:** Trace U5 on all 8 ISWL coverages; compare to PAAGERAT U5 rows (200 ISWL)  

### QUIKGPS

- **Revised likely source:** **BP** (Billable Premium); also BI, UG, UH, UX, UY, UZ, MP  
- **Not ISWL source:** PR (zero rows)  
- **Action:** Trace BP/BI/UG/UH from PCOVRSGT; validate vs PPBEN/PPRBNUL premium fields  

### QUIKISSC

- **Revised likely source:** **SR → SL**; fallback U7/U8  
- **Do not use:** TP/TX  
- **Action:** Trace SR on ISWL coverages; resolve SL; validate vs PPBENTYP/PPRBNUL surrender fields  

### QUIKUINT

- **Likely segments:** A1, G1, LN  
- **Possible files:** PDINT/PDINTTBL (not in May ZIP), PRBENINT, PSEGT constants, PPBEN.FV_GUAR_RATE (validation)  
- **Action:** Trace A1/G1/LN; confirm QUIKUINT schema; separate guaranteed vs credited vs loan  

### Expenses

- **Likely segments:** UF, U1, U2, U3, G2, G3, GF  
- **Also inspect:** nesting under BP/BI/UG/UH/UX/UY/UZ  
- **Action:** Segment trace; do not infer from policy values alone  

---

## 13. Required updates to existing research/gap report

The following revisions apply to `ISWL_Implementation_Gap_Report.md` and `ISWL_LifePRO_to_QLAdmin_Master_Reference.md` (conceptual — see revised summary §15):

1. **NC** — no longer primary current COI candidate.  
2. **U6** — current COI candidate (segment + possible TYPE_CODE alignment).  
3. **U5** — search first for guaranteed COI.  
4. **TP/TX** — removed as primary surrender candidates.  
5. **SR/SL** — primary surrender path.  
6. **U7/U8** — fallback surrender paths.  
7. **BP** — elevated as stronger billable/gross premium candidate.  
8. **PR** — standard segment; zero ISWL rows in extract.  
9. **Expenses** — may nest in BP/BI or UL premium logic.  
10. **Hierarchy trace** — mandatory before final mapping (`PPRDF` → rates).

---

## 14. Revised questions for Eric / SME

1. Confirm Product Book segment definitions apply to CSO ISWL setup: U6=Current COI, U5=Guaranteed COI, BP=Billable Premium, NC=Net Premium Credited, TP=Tax Valuation Premiums, TX=Tax Reserve Factors, SR/SL=Full Surrender/Load.  
2. For ISWL current COI, should authority trace through **U6**?  
3. For ISWL guaranteed COI, should authority trace through **U5**?  
4. For ISWL billable/gross premiums, should authority trace through **BP** or another premium segment (BI, UG, UH, etc.)?  
5. For ISWL surrender, **SR/SL** or legacy **U7/U8**?  
6. Are TP/TX tax-only, or used for surrender in CSO’s LifePRO setup?  
7. Where are ISWL expenses maintained — UF/U1/U2/U3, G2/G3/GF, or embedded in BP/BI/UG/UH/UX/UY/UZ?  
8. For ISWL interest, trace **A1/G1/LN**, PRBENINT, PDINT/PDINTTBL, or other?  
9. Should May **PDAGE CV** replace April **Rate_Table CV** for QUIKCVS after parity confirmation?  
10. Can client provide **PSEGT** and **PDINT/PDINTTBL** extracts (missing from May ZIP)?

---

## 15. Revised gap summary (post–Product Book)

See also: `docs/research/ISWL_Gap_Report_Manual_Revised_Summary.md` (structured per-area revision table).

---

## Related documents

| Document | Role |
|----------|------|
| `ISWL_LifePRO_to_QLAdmin_Master_Reference.md` | Pre-manual baseline (sections 5–7 contain assumptions superseded here) |
| `ISWL_Implementation_Gap_Report.md` | Repo implementation gap (pre-manual) |
| `ISWL_Gap_Report_Manual_Revised_Summary.md` | Per-target revised assumptions after manual |
| `ISWL_Zip_Research_Executive_Summary_20260530.md` | Extract evidence counts |
