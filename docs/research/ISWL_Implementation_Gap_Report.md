# ISWL Implementation Gap Report

**Date:** 2026-06-28 (revised with Product Book manual findings)  
**Baselines:**
- `docs/research/ISWL_LifePRO_to_QLAdmin_Master_Reference.md`
- `docs/research/ISWL_Product_Book_Manual_Findings_Addendum.md` (LifePRO Product Book / `Product.pdf`)

**Method:** Read-only comparison of repo implementation against master reference **and** Product Book segment definitions. Extract evidence from May 20260530 ZIP research and prior forensic audit. **No code changes.**

**ISWL fleet (proven):** MPLAN `1658C1`, `1658CS`, `1659C2`, `1659CR`, `1659CS`, `1659SR`, `1669SR`, `1679CS` ↔ LifePRO coverage IDs `658 CEN I` through `679 CEN SD` (2,268 policies per Issue #21D).

---

## Update — 2026-06-29 (Issue #31 follow-up)

**Primary source dependency removed.** Client supplied:

- `QLA_Migration/Source/PSEGT_Segment_Extract_20260629.csv` (696 rows; 221 segment IDs)
- `QLA_Migration/Source/PDINT_DeclaredInterestRates_Extract_20260629.csv` (10 rows)
- `QLA_Migration/Source/PDINTTBL_DeclaredInterestRates_Extract_20260629.csv` (37 rows)

**Authoritative hierarchy trace is now possible:** `PCOVRSGT.SEGT_ID → PSEGT (multi-type per segment) → PAAGERAT / PDAGE / PDINT`.

| QLA area | Status after PSEGT |
|----------|-------------------|
| QUIKCVS | **Fully resolved** (hierarchy + rates; parity TBD) |
| QUIKUINT | **Partially resolved** (A1/G1/LN on PSEGT; PDINT sparse) |
| QUIKCOI / QUIKGCOI / QUIKGPS | **Partially resolved** (PSEGT 8/8; PAAGERAT gaps on senior plans) |
| QUIKISSC | **Partially resolved** (SR/SL on PSEGT; rate pointer TBD) |
| Expenses | **Partially resolved** (UF only; U1–U3/G2/G3/GF absent) |

Full detail: `docs/research/ISWL_Segment_Trace/ISWL_Segment_Trace_Addendum_20260629.md` and `Issue_Log_Items/Issue_31/Issue_31_PSEGT_PDINT_Followup_Report.md`.

---

## Research methodology (post–Product Book)

1. **ISWL is UL-style setup** — requires QUIKUINT, QUIKCOI, QUIKGCOI, QUIKISSC, QUIKGPS, expense/load handling, not WL rate tables alone.
2. **Do not map rate rows by TYPE_CODE alone.** Authoritative path:

   ```text
   PPRDF -> PCOMP -> PCOVR -> PCOVRSGT -> PSEGT -> rate tables
   ```

3. **Segment definitions** come from the Product Book manual (see addendum §4–5). PDDIC extracts did not provide an equivalent dictionary.
4. **May ZIP gap (partially closed 2026-06-29):** `PCOVRSGT`, `PCOMP`, `PCOVR`, `PPRDF`, rate files present in May ZIP; **`PSEGT` and `PDINT`/`PDINTTBL` were not in May ZIP** — now supplied separately in `QLA_Migration/Source/` (20260629 extracts). Segment trace complete for PSEGT-mapped codes; see Issue #31 follow-up.

---

## 1. Interest values → QUIKUINT

**Area:** Interest values → QUIKUINT  

**Current state (repo):** **Partial — not QUIKUINT table.**
- `qla_core/cso_mortality_crosswalk.py`: ISWL MPLAN allowlist; 4.50%; `NFOINT` code `A`
- `QLA_Migration/app.py`: ISWL-scoped `quikdvdp.MDEPINT = 4.50` via `is_iswl_mplan()`
- CSO crosswalk enriches `quikplan.NFOINT` / `INTMETHCV` at emit
- `Data_Goverence.txt`: UL plans **must** have a `QUIKUINT` record — **no loader satisfies this**

**Prior assumption (extract-only):** PPBEN `FV_GUAR_RATE`, PRBENINT, or CSO/NFOINT path might suffice for interest.

**Manual finding:** ISWL is Interest Sensitive / UL-style. Interest via segments **A1** (current credited), **G1** (guaranteed), **LN** (loan); declared interest (`PDINT`/`PDINTTBL`); monthaversary control (**UI**). NFOINT alone does not represent full UL interest product setup.

**Revised assumption:** **NFOINT/MDEPINT are validation/display paths only.** Authoritative QUIKUINT mapping requires **A1/G1/LN segment trace** → rate source. PPBEN `FV_GUAR_RATE=4.50` (2,159 ISWL rows) supports **validation** of guaranteed rate, not final column mapping.

**QLAdmin target:** `QUIKUINT` (guaranteed, current credited, loan credited/charged)

**Implemented already?** **No** (QUIKUINT). **Partial** (NFOINT + MDEPINT).

**Current source table used:** `CSO_Mortiality_Crosswalk.csv`; no LifePRO interest loader.

**Expected source table (after segment trace):** `PRBENINT`; `PDINT`/`PDINTTBL` (request from client); PSEGT constants; `PPBEN.FV_GUAR_RATE`; `PLOAN.INTEREST_RATE` (loan validation).

**Segment path to trace:** `PCOVRSGT → A1 / G1 / LN → PDINT/PDINTTBL or PRBENINT or PSEGT constant`

**Dimensions preserved?** Plan-level NFOINT only; no QUIKUINT effective-date or rate-type dimensions.

**Validation gap:** No QUIKUINT schema in repo; A1/G1/LN not traced; PDINT missing from May ZIP; governance vs NFOINT unresolved.

**TYPE_CODE / segment confirmed?** Manual defines A1/G1/LN; **not traced in CSO extract**.

**SME confirmation needed?** **Yes**

**Recommended next action:** Trace A1/G1/LN on all 8 ISWL coverages in `PCOVRSGT`; profile `PRBENINT` for ISWL; request PSEGT/PDINT extracts; obtain QUIKUINT DBF/Help layout.

**Code change needed?** **Yes** (after segment proof + schema)  

**Business decision needed?** **Yes**

---

## 2. Expenses

**Area:** Expenses  

**Current state (repo):** **Partial — policy fee only.** Issue #21C: `POLICY_FEE` → `quikridr.MANNLFEE` on base rider (~4,459 policies fleet-wide). No product-level expense tables for monthly policy fee, % premium, or per-$1,000.

**Prior assumption:** Standalone expense TYPE_CODE tables or `PCOVR.POLICY_FEE` plan field.

**Manual finding:** Expense segments **UF, U1, U2, U3, G2, G3, GF**. Expenses may be **nested inside billable premium / UL premium logic** (BP, BI, UG, UH, UX, UY, UZ), not only standalone tables.

**Revised assumption:** Expenses are **multi-component and possibly embedded** in premium assembly. `MANNLFEE` captures at most one policy-fee dimension; it does **not** satisfy the full expense requirement from the master reference.

**QLAdmin target:** Monthly expense per policy; percent of premium; monthly expense per $1,000.

**Implemented already?** **Partial** (MANNLFEE only).

**Current source table used:** `POLICY_FEE` cache during `quikmstr` pass → `quikridr.MANNLFEE`.

**Expected source table (after segment trace):** UF/U1/U2/U3/G2/G3/GF via `PCOVRSGT`; nested refs from BP/BI/UG/UH/UX/UY/UZ; `PCOVR`/`PCOMP` for plan-level fees.

**Segment path to trace:** `UF/U1/U2/U3/G2/G3/GF` and nested references from premium segments.

**Dimensions preserved?** Policy-level annual fee on base rider only.

**Validation gap:** Three expense components required; segment trace not performed; nesting in BP not inspected.

**TYPE_CODE / segment confirmed?** Manual defines UF/U1/U2/U3/G2/G3/GF; **not traced in extract**.

**SME confirmation needed?** **Yes**

**Recommended next action:** Trace expense segments on all 8 ISWL coverages; inspect BP/BI for nested U1/U2/U3; compare MANNLFEE on ISWL policies vs LifePRO fee fields.

**Code change needed?** **Yes** (if full expense product setup required)  

**Business decision needed?** **Yes**

---

## 3. Current COI → QUIKCOI

**Area:** Current COI → QUIKCOI  

**Current state (repo):** **Not implemented.** No `QUIKCOI` in converter. NC, U6, BP excluded from `TYPE_TO_TABLE` (`qla_core/rate_dbf_schema.py`).

**Prior assumption (extract — superseded):** PAAGERAT `TYPE_CODE=NC` ≈ current COI (**690 ISWL rows**).

**Manual finding:** **NC = Net Premium Credited Segment — NOT current COI.** **U6 = Current COI Rates Segment.** COI also depends on **NR, UL, UI, FC, MR** (NAR, corridor, monthaversary, fund contract rules).

**Revised assumption:** **Primary QUIKCOI candidate is U6 segment** → resolved rate table (PAAGE/PAAGERAT or PDAGE per rate type **A/I/O/D**). Extract `TYPE_CODE=U6` (**800 ISWL rows**, 658 CEN I + 659 CEN II) may align **only if** U6 segment linkage proves it — not direct emit. **NC path withdrawn** for QUIKCOI. PPBEN `UV_CURR_COI_RATE` disproven (all zero).

**QLAdmin target:** `QUIKCOI`

**Implemented already?** **No**

**Current source table used:** None

**Expected source table (after segment trace):** Rate rows resolved from **U6** (not NC); supporting context from NR/UL/UI/FC/MR segments.

**Segment path to trace:** `PCOVRSGT → U6 → PAAGERAT / PAAGE / PDAGE`

**Dimensions preserved?** N/A until U6 resolved; likely attained-age or issue-age per rate type — VARGP alignment with other ISWL tables TBD.

**Validation gap:** U6 not traced on PCOVRSGT; NC misclassified in prior research; QUIKCOI schema absent; NAR/corridor setup not assessed.

**TYPE_CODE / segment confirmed?** **Manual: U6 = current COI.** Extract TYPE_CODE=U6 **not confirmed** equal to segment U6 until linkage proven.

**SME confirmation needed?** **Yes** — confirm U6 is ISWL current COI authority; confirm NC is out of scope for QUIKCOI.

**Recommended next action:** Trace U6 on all 8 ISWL coverages; map to rate rows; compare to 800 ISWL U6 extract rows; profile NR/UL/UI for COI context.

**Code change needed?** **Yes** (after segment proof)  

**Business decision needed?** **Yes**

---

## 4. Guaranteed COI → QUIKGCOI

**Area:** Guaranteed COI → QUIKGCOI  

**Current state (repo):** **Not implemented.** No `QUIKGCOI`. U6 excluded from WL loader (same as NC/BP).

**Prior assumption (extract — superseded):** PAAGERAT `TYPE_CODE=U6` ≈ guaranteed COI (**800 ISWL rows**).

**Manual finding:** **U5 = Guaranteed COI Rates Segment.** **U6 is current COI, not guaranteed.**

**Revised assumption:** **Primary QUIKGCOI candidate is U5 segment** → resolved rate table. PAAGERAT **`TYPE_CODE=U5`** (**200 ISWL rows** in May extract) aligns with manual better than U6. Prior **U6→GCOI mapping is incorrect.** PPBEN `UV_GUAR_COI_RATE` disproven (all zero).

**QLAdmin target:** `QUIKGCOI`

**Implemented already?** **No**

**Current source table used:** None

**Expected source table (after segment trace):** Rate rows resolved from **U5**; PAAGERAT U5 rows by coverage.

**Segment path to trace:** `PCOVRSGT → U5 → PAAGERAT / PAAGE / PDAGE`; NR/UL/FC as for QUIKCOI.

**Dimensions preserved?** N/A; U5 row coverage across all 8 plans unverified until segment trace.

**Validation gap:** U5 not traced; prior U6-as-GCOI confounded segment vs TYPE_CODE; QUIKGCOI schema absent.

**TYPE_CODE / segment confirmed?** **Manual: U5 = guaranteed COI.** Extract TYPE_CODE=U5 **not confirmed** equal to segment U5 until linkage proven.

**SME confirmation needed?** **Yes** — confirm U5 is guaranteed COI authority for ISWL.

**Recommended next action:** Trace U5 on all 8 ISWL coverages; profile PAAGERAT U5 by coverage; **abandon U6-as-GCOI hypothesis.**

**Code change needed?** **Yes** (after segment proof)  

**Business decision needed?** **Yes**

---

## 5. Surrender charges → QUIKISSC

**Area:** Surrender charges → QUIKISSC  

**Current state (repo):** **Not implemented.** No `QUIKISSC`. TP, TX, SL in `EXCLUDED_TYPE_CODES` for WL rate pipeline.

**Prior assumption (extract — superseded):** PDAGE `TYPE_CODE=TP`/`TX` (**2,128 ISWL rows each**) as inference-only surrender candidates.

**Manual finding:** **SR → SL** is preferred path (Full Surrender → Full Surrender Load). **TP = Tax Valuation Premiums; TX = Tax Reserve Factors** — **not surrender.** Fallback: **U7/U8** (legacy monthaversary surrender load).

**Revised assumption:** **TP/TX removed from QUIKISSC candidates.** Primary path: **`PCOVRSGT → SR → SL`**. U7/U8 only if SR/SL absent. Do not use PDAGE TP/TX for QUIKISSC unless SME proves client-specific reuse (manual says no).

**QLAdmin target:** `QUIKISSC`

**Implemented already?** **No**

**Current source table used:** None

**Expected source table (after segment trace):** SR/SL segment constants or linked rate rows; fallback U7/U8; policy validation `PPBENTYP.BF_CURR_SURR_LOAD`, `PPRBNUL.SURR_LOAD`.

**Segment path to trace:** `PCOVRSGT → SR → SL`; fallback U7/U8.

**Dimensions preserved?** N/A — duration/policy-year schedule expected.

**Validation gap:** SR/SL not traced; prior TP/TX finding superseded; QUIKISSC schema absent.

**TYPE_CODE / segment confirmed?** **Manual: SR/SL preferred; TP/TX are tax data.**

**SME confirmation needed?** **Yes** — SR/SL vs U7/U8 for CSO ISWL; confirm TP/TX are tax-only.

**Recommended next action:** Trace SR on all 8 ISWL coverages; resolve SL child segment; validate vs policy surrender load fields.

**Code change needed?** **Yes** (after segment proof)  

**Business decision needed?** **Yes**

---

## 6. Gross premiums → QUIKGPS

**Area:** Gross premiums → QUIKGPS  

**Current state (repo):** **Pipeline exists; ISWL rows absent.** `Rate_Table` PR → `QuikGps`; `paagerat_pr_loader.py` filters **PR only**. **ISWL: zero PR rows** (Rate_Table, PAAGERAT, PDAGE). BP (**1,164 ISWL rows**) excluded from loader. `iswl-prem.csv` not used (correct).

**Prior assumption:** BP inferred as GP; PR standard but empty for ISWL.

**Manual finding:** **BP = Billable Premium Segment** — credible ISWL premium source. **PR = Premium Segment** (standard LifePRO, but **not present for ISWL in extracts**). Also: BI, UG, UH, UX, UY, UZ, MP; expenses may nest in BP (U1/U2/U3).

**Revised assumption:** **BP is elevated primary candidate for QUIKGPS**, not PR. Segment linkage must prove BP → QuikGps. Rate type (A/I/O/D) determines PAAGERAT vs PDAGE. VARGP alignment across ISWL tables still required.

**QLAdmin target:** `QUIKGPS` (`QuikGps` / `QuikPlGp`)

**Implemented already?** **Partial** — QuikGps infrastructure (R5); **no ISWL population**.

**Current source table used:** `Rate_Table_Extract_20260427.csv` (PR); `PAAGERAT` (PR only)

**Expected source table (after segment trace):** Rate rows from **BP** segment (or BI/UG/UH/UX/UY/UZ/MP if linkage points there); **not PR** for ISWL.

**Segment path to trace:** `PCOVRSGT → BP (or BI/UG/UH/UX/UY/UZ/MP) → PAAGERAT/PDAGE`

**Dimensions preserved?** QuikGps supports issue-age×duration and attained-age; BP shape TBD after U6/BP rate-type inspection.

**Validation gap:** No ISWL GP rows via PR; BP not traced; VARGP not validated for ISWL; senior plan BP coverage TBD.

**TYPE_CODE / segment confirmed?** **Manual: BP = Billable Premium.** Extract TYPE_CODE=BP **not confirmed** equal to segment BP until linkage proven.

**SME confirmation needed?** **Yes** — BP vs BI/UG/UH for QUIKGPS; QuikGps grid vs BP rate shape.

**Recommended next action:** Trace BP on all 8 ISWL coverages; profile PAAGERAT BP; compare to PPBEN/PPRBNUL premium fields.

**Code change needed?** **Yes** (BP loader after segment proof)  

**Business decision needed?** **Yes**

---

## 7. Cash values → QUIKCVS

**Area:** Cash values → QUIKCVS  

**Current state (repo):** **Implemented — routing and catalog.** CV → `QuikCvs`/`QuikPlCv` via `rate_pipeline.py`. ISWL MPLANs in catalog (`1658C1` PASS). R7a: **18,128 CV rows** for `1658C1` from Rate_Table. CSO crosswalk on QuikPlCv keys. Variation flags set.

**Prior assumption:** Rate_Table CV proven routing; PDAGE CV strong alternate.

**Manual finding:** **CV = Cash Values Segment.** Tabular CV as UL/ISWL floor. Rate type O/D → age/duration file (`PDAGE`).

**Revised assumption:** CV remains **strongest QUIKCVS source** — manual **confirms** segment meaning. Implementation path unchanged until **Rate_Table vs May PDAGE parity** completed and business approves May source. Do not switch routing on TYPE_CODE grep alone; trace CV segment on PCOVRSGT.

**QLAdmin target:** `QUIKCVS`

**Implemented already?** **Yes** (routing + emit infra). **Unverified** (value parity, all 8 plans in production DBFs).

**Current source table used:** `Rate_Table_Extract_20260427.csv`

**Expected source table:** Rate_Table CV (current) or `PDAGE_AgeDuration_Rates_Extract_20260530.csv` TYPE=CV (**12,084 ISWL rows**) after parity + sign-off.

**Segment path to trace:** `PCOVRSGT → CV → PDAGE or Rate_Table` (confirm rate type D/O).

**Dimensions preserved?** **Yes** — issue age × duration × sex × UW × band × CNTL (CV0–CV9).

**Validation gap:** No PDAGE parity study; R3 value compare blocked; May ZIP has no Rate_Table.

**TYPE_CODE / segment confirmed?** **Yes** — manual CV = Cash Values; R3/R5 routing CV→QuikCvs confirmed. PDAGE substitution not confirmed.

**SME confirmation needed?** **Yes** — PDAGE vs Rate_Table for production; reference DBF value sign-off.

**Recommended next action:** CV parity by coverage × duration × band × sex × UW × value; confirm all 8 MPLANs in emitted QuikCvs.

**Code change needed?** **Maybe** — only if PDAGE replaces Rate_Table after parity  

**Business decision needed?** **Yes**

---

## Summary matrix (research-only)

| Area | QLAdmin target | Repo implemented? | Manual primary segment | Extract evidence | Still blocked? |
|------|----------------|---------------------|------------------------|------------------|----------------|
| Interest | QUIKUINT | Partial (NFOINT/MDEPINT) | A1, G1, LN | PPBEN FV_GUAR 4.50%; PRBENINT in ZIP | **Yes** |
| Expenses | Product pattern | Partial (MANNLFEE) | UF, U1–U3, G2, G3, GF | No expense TYPE_CODE tables | **Yes** |
| Current COI | QUIKCOI | No | **U6** (not NC) | U6: 800 ISWL rows; NC: 690 (withdrawn) | **Yes** |
| Guaranteed COI | QUIKGCOI | No | **U5** (not U6) | U5: 200 ISWL rows | **Yes** |
| Surrender | QUIKISSC | No | **SR → SL** | TP/TX removed; SR/SL not traced | **Yes** |
| Gross premium | QUIKGPS | Infra only | **BP** | BP: 1,164 ISWL; PR: 0 | **Yes** |
| Cash value | QUIKCVS | **Yes** (routing) | CV | Rate_Table + PDAGE 12,084 ISWL CV | **Partial** |

---

## Assumption revision table (extract vs Product Book)

| Code | Prior extract inference | Product Book | Revised QLA use |
|------|-------------------------|--------------|-----------------|
| NC | QUIKCOI candidate | Net Premium Credited | **Withdrawn** from QUIKCOI |
| U6 | QUIKGCOI candidate | Current COI Rates | **QUIKCOI** |
| U5 | Underused | Guaranteed COI Rates | **QUIKGCOI** |
| BP | GP candidate (weak) | Billable Premium | **QUIKGPS** (primary) |
| PR | Standard premium | Premium Segment | Standard; **0 ISWL rows** in extract |
| TP | QUIKISSC inference | Tax Valuation Premiums | **Do not use** for QUIKISSC |
| TX | QUIKISSC inference | Tax Reserve Factors | **Do not use** for QUIKISSC |
| SR/SL | Preferred | Full Surrender / Load | **Required** QUIKISSC path |
| U7/U8 | Fallback | Legacy surrender load | QUIKISSC fallback |
| CV | QUIKCVS | Cash Values | **Confirmed** |

---

## Cross-cutting gaps

1. **Segment hierarchy not implemented** — converter does not traverse `PPRDF → PCOMP → PCOVR → PCOVRSGT → PSEGT → rates`.
2. **TYPE_CODE grep is insufficient** — manual definitions supersede prior PDDIC-based inference; linkage still required per segment.
3. **Missing May ZIP files** — `PSEGT`, `PDINT`/`PDINTTBL` needed for complete trace.
4. **QLAdmin UL table schemas** — QUIKUINT, QUIKCOI, QUIKGCOI, QUIKISSC not documented in repo.
5. **NAR/corridor/monthaversary** — NR, UL, UI, FC, MR segments may be required for COI correctness, not rates alone.
6. **Rate-shape audit not performed** — CV (issue-age×duration) vs U5/U6/BP (rate type A/I/O/D) must be uniform per plan across QLAdmin tables.
7. **WL rate pipeline scope** — `TYPE_TO_TABLE` covers CV/PR/NP/RV/DB/DV only; excludes NC, U5, U6, BP, TP, TX by design.

---

## Recommended research sequence (no code)

1. **PCOVRSGT segment trace** on all 8 ISWL coverages: U6, U5, BP, SR/SL, A1/G1/LN, UF/U1/U2/U3.
2. **QUIKCVS parity** — Rate_Table CV vs May PDAGE CV.
3. **Request client extracts** — PSEGT, PDINT/PDINTTBL.
4. **Eric/SME confirmation** — question list below.
5. **Rate-shape audit** — per plan, per table family, before any loader design.

---

## Eric / SME question list (revised)

Use with Eric, actuarial, or LifePRO SME. Confirm Product Book definitions apply to **CSO ISWL** setup.

### Segment definition confirmation

1. Do Product Book segment definitions apply to CSO’s ISWL products for:
   - **U6** = Current COI Rates  
   - **U5** = Guaranteed COI Rates  
   - **BP** = Billable Premium  
   - **NC** = Net Premium Credited (not COI)  
   - **TP** = Tax Valuation Premiums  
   - **TX** = Tax Reserve Factors  
   - **SR/SL** = Full Surrender / Surrender Load  
   - **A1/G1/LN** = Current / Guaranteed / Loan interest  

2. For ISWL **current COI (`QUIKCOI`)**, should authority trace through segment **U6** (not NC)?

3. For ISWL **guaranteed COI (`QUIKGCOI`)**, should authority trace through segment **U5** (not U6)?

4. For ISWL **billable/gross premiums (`QUIKGPS`)**, should authority trace through **BP**, or another segment (BI, UG, UH, UX, UY, UZ, MP)?

5. For ISWL **surrender charges (`QUIKISSC`)**, is setup **SR → SL**, or legacy **U7/U8**?

6. Are **TP/TX** used only for tax valuation/reserve in CSO’s LifePRO setup, or for any surrender purpose?

### Expense and premium nesting

7. Where are ISWL expenses maintained?
   - Standalone: UF, U1, U2, U3, G2, G3, GF  
   - Embedded in BP/BI/UG/UH/UX/UY/UZ premium logic  
   - Policy-level `POLICY_FEE` / `quikridr.MANNLFEE` only  

8. Does **BP** include premium collection loads (U1/U2/U3) that must be separated for QLAdmin expense reporting?

### Interest

9. For ISWL **interest (`QUIKUINT`)**, should current/guaranteed/loan rates trace through **A1/G1/LN**, **PRBENINT**, **PDINT/PDINTTBL**, or another source?

10. Is **4.50%** (CSO crosswalk / PPBEN `FV_GUAR_RATE` / `MDEPINT`) the guaranteed rate for QUIKUINT **G1**, or only a dividend/NFO display rate?

11. Does **`quikplan.NFOINT` + `quikdvdp.MDEPINT`** satisfy the governance rule requiring a **QUIKUINT** record for UL-class plans, or must a separate QUIKUINT table be loaded?

### Cash values and extracts

12. Should May **`PDAGE TYPE_CODE=CV`** replace April **`Rate_Table` CV** for production `QUIKCVS`, assuming parity is confirmed?

13. Why was **`Rate_Table_Extract`** omitted from the May 20260530 ZIP?

14. Can the client provide **`PSEGT`** and **`PDINT`/`PDINTTBL`** extracts (missing from May ZIP) for segment-to-rate linkage?

### NAR, corridor, and COI context

15. For ISWL COI, are **NR** (NAR calculation), **UL** (corridor), **UI** (monthaversary), and **FC** (fund contract) segments configured and required for QLAdmin setup beyond rate tables alone?

16. Does QLAdmin expect **rates only** for QUIKCOI/QUIKGCOI, or full plan behavior including NAR/corridor rules?

### Product scope

17. Why are requested MPLANs/coverages (**1668B1, 1669B2, 1678CS, 668 CEN I, 678/679 CEN SEN**) absent from ISWL fleet extracts?

18. Can actuarial provide **reference DBFs** or Help extracts for QUIKUINT, QUIKCOI, QUIKGCOI, QUIKISSC physical layouts?

---

## Implementation gate (unchanged)

**No code changes** until:

- Segment traces documented for each QLA target on all 8 ISWL coverages  
- SME confirms segment definitions for CSO ISWL  
- QLAdmin physical schemas obtained where missing  
- QUIKCVS parity decision documented (if applicable)  

---

**Related documents:**  
`docs/research/ISWL_LifePRO_to_QLAdmin_Master_Reference.md`  
`docs/research/ISWL_Product_Book_Manual_Findings_Addendum.md`  
`docs/research/ISWL_Gap_Report_Manual_Revised_Summary.md` (superseded by this revision — retained for audit trail)  
`docs/research/ISWL_Zip_Research_Executive_Summary_20260530.md`  
`Issue_Log_Items/Issue_ISWL_Research/ISWL_Forensic_Audit_Trail.md`
