# ISWL Data Gaps and Questions

**Date:** 2026-06-28 (updated 2026-06-30 — Issue #31 PSEGT/PDINT follow-up)  
**Related:** `ISWL_Source_Discovery_Report.md`, Issue #21D interest strategy, `Issue_31_PSEGT_PDINT_Followup_Report.md`

---

## 0. Gaps cleared by 20260629 extracts (Issue #31)

| # | Prior gap | Status after PSEGT/PDINT/PDINTTBL |
|---|-----------|-----------------------------------|
| C1 | PSEGT missing — cannot map PCOVRSGT slots to Product Book codes | **CLEARED** — 696 rows; 185/191 ISWL slots join |
| C2 | PDINT/PDINTTBL missing — QUIKUINT A1/G1/LN blocked | **PARTIALLY CLEARED** — PDINT A1 (CENII 4.50%); G1/LN not in PDINT TYPE_CODE |
| C3 | Segment hierarchy blocked at PSEGT layer | **CLEARED** for PCOVRSGT→PSEGT→rates path |

---

## 1. Confirmed gaps (LifePRO source does not contain required QLA value)

| # | QLA requirement | Gap | Impact |
|---|-----------------|-----|--------|
| G1 | **Expenses** (monthly per policy, % of premium, per $1,000) | No expense table, TYPE_CODE, or PCOVR field identified in available extracts | Cannot populate QUIKAEXP or equivalent ISWL expense setup |
| G2 | **Surrender charges → QUIKISSC** | No SC/SUR/ISSC TYPE_CODE for any ISWL coverage | Cannot build surrender charge schedule in QLAdmin |
| G3 | **Gross premiums → QUIKGPS from LifePRO PR** | Zero `PR` rows in Rate_Table and PAAGERAT for all 8 ISWL coverages | Standard WL GP loader path has no ISWL source rows |
| G4 | **Guaranteed COI → QUIKGCOI** | U5 PSEGT wired 8/8; PAAGERAT U5 on 1/8 (679 CEN SD) | Segment-ID indirection; SME confirm |
| G5 | **COI → QUIKCOI** | U6 PSEGT wired 8/8; PAAGERAT U6 on 2/8 SD parents | Same; NC not primary COI path per Product Book |
| G6 | **PPBEN policy-level interest/COI fields** | ~~Source empty~~ — PDINT CENII supplements | Map IDENT to all 8 MPLANs |
| G7 | **QLAdmin UL table schemas** | QUIKUINT, QUIKCOI, QUIKGCOI, QUIKISSC field layouts not in repo | Cannot finalize column-level mapping |
| G8 | **Reference DBFs for ISWL plans** | R3 reconciliation: plans like `1658C1` absent from supplied target rate DBFs | Cannot value-validate emitted factors |

---

## 2. Partial coverage gaps (data exists but incomplete or unconfirmed)

| # | Area | What exists | What is missing |
|---|------|-------------|-----------------|
| P1 | Interest / QUIKUINT | CSO 4.50% plan-level; Issue #21D MDEPINT strategy | Current credited rate source; loan rate; QUIKUINT vs NFOINT distinction |
| P2 | GP / QUIKGPS | PAAGERAT `BP` on 6 plans; `iswl-prem.csv` matrix | BP semantics; MPLAN mapping for iswl-prem; plans 659 SR GD / 669 SR GD have no PAAGERAT |
| P3 | CV / QUIKCVS | CV rows all 8 plans in Rate_Table | EFFDATE/segment defaults; populated QLAdmin target for value compare |
| P4 | COI / GCOI | NC + U6 on flagship plans | Confirmation of TYPE_CODE meaning; U5 on 659 CEN II unexplained |

---

## 3. Structural inconsistencies

| # | Observation | Risk |
|---|-------------|------|
| S1 | Rate_Table CV/NP/RV use **issue age × duration** (VARGP=2 style); PAAGERAT NC/U6/BP use **attained age (SEQ)** | QUIKCOI/GCOI/GPS may need different QuikPlan variation codes than QUIKCVS |
| S2 | Rate_Table UW classes **P/S** (2 classes); iswl-prem segments use **10 PFSA codes** (MSP, MRN, FJV, …) | Direct merge of iswl-prem and LifePRO segments will mismatch |
| S3 | PAAGERAT absent entirely for **659 SR GD** and **669 SR GD** | Senior/grandfathered plans may rely on Rate_Table only or external sources |
| S4 | `659 CEN II` has extra TYPE_CODEs **TP, TX, SL, UF** in Rate_Table (excluded from loader) | Product variant with additional actuarial tables not mapped to QLA |

---

## 4. Questions for business / actuarial / LifePRO IT

### Plan identification and scope

1. Are all eight MPLAN codes (`1658C1` through `1679CS`) in scope for **full** QUIKUINT/COI/GCOI/ISSC/GPS/CVS setup, or only the high-volume plans (e.g. `1658C1`, `1659C2`)?
2. How do `659 SR GD` and `669 SR GD` differ actuarially from `659 CEN SR` / central variants — and where are their COI/GP rates stored given **no PAAGERAT rows**?

### TYPE_CODE semantics (blocking for COI/GCOI/GP)

3. What does **`NC`** represent in PAAGERAT for ISWL — current cost of insurance?
4. What does **`U6`** represent — guaranteed cost of insurance?
5. What does **`U5`** represent on `659 CEN II` only?
6. What does **`BP`** represent — base premium / gross premium / modal factor?
7. Why are **`PR`** (premium rate) rows absent from both Rate_Table and PAAGERAT for ISWL while CV/NP/RV are present?

### Interest (QUIKUINT)

8. For ISWL, is **plan-level 4.50%** (CSO crosswalk / NFOINT code A) sufficient for QUIKUINT guaranteed rate, or must **policy-level** `FV_GUAR_RATE` from PPBEN be loaded?
9. Does **`UV_CURR_COI_RATE`** represent dividend accumulation crediting, UL COI interest, or something else for ISWL?
10. Where is the **loan credited rate** stored for ISWL — plan table, state override (`QuikPlSt.MLOANINT`), or policy loan record?

### Surrender and expenses

11. Where are **ISWL surrender charge** schedules maintained in LifePRO (table name / TYPE_CODE)?
12. Where are **expense charges** (monthly policy, % premium, per $1,000) stored?

### PFSA / iswl-prem.csv

13. Is **`PFSA Rates/iswl-prem.csv`** authoritative for ISWL gross premium in QLAdmin, or a legacy PFSA artifact superseded by LifePRO extracts?
14. How do iswl-prem row prefixes (`MSP B2`, `FJV B2`, …) map to the eight QLA MPLAN codes and LifePRO UW classes P/S?

### QLAdmin schema

15. Can actuarial provide **reference DBFs** or Help extracts for QUIKUINT, QUIKCOI, QUIKGCOI, QUIKISSC physical layouts?
16. Does ISWL require **QUIKUINT** records per Data_Goverence UL rule even though interest is also on quikplan/quikdvdp?

---

## 5. Extract and environment gaps

| Gap | Action |
|-----|--------|
| `QLA_Migration/Source/` empty (gitignored) | Unzip `LifePRO_Extracts_20260530.zip` (or current monthly) locally for PPBEN/PPOLC analysis |
| `reference_dbf/` not populated | Obtain QLAdmin V5 template DBFs including UL rate tables |
| No LifePRO data dictionary in repo | Request TYPE_CODE legend from LifePRO team |

---

## 6. Items explicitly out of scope for this research

- Implementing MDEPINT fix (Issue #21D Track A — separate approved work)
- Running full rate loader emit or migration batch
- Modifying `app.py`, rulebooks, crosswalks, or validators
- Assuming PFSA premium reconciliation patterns apply to ISWL without source proof

---

*End of document*
