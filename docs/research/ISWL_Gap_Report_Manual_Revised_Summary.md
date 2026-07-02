# ISWL Gap Report — Manual-Revised Summary

**Date:** 2026-06-28 (Product Book); **updated 2026-06-30** (Issue #31 PSEGT/PDINT)  
**Supersedes assumptions in:** `ISWL_Implementation_Gap_Report.md` (extract-inference sections only)  
**Authority added:** LifePRO Product Book (`Product.pdf`) — see `ISWL_Product_Book_Manual_Findings_Addendum.md`  
**PSEGT authority added:** `QLA_Migration/Source/PSEGT_Segment_Extract_20260629.csv` — see `ISWL_Segment_Trace_Addendum_20260629.md`  
**Code changes:** None

This document revises the implementation gap assessment after Product Book manual findings. Repo implementation status is unchanged; **source-path assumptions and SME questions** are updated.

---

## QUIKCVS

**Area:** Cash values → QUIKCVS  

**Prior assumption:** CV → QuikCvs via Rate_Table is proven routing; May PDAGE CV is strong alternate (12,084 ISWL rows).  

**Manual finding:** `CV` = Cash Values Segment; tabular CV is UL/ISWL floor concept. Rate type O/D → age/duration file (`PDAGE`).  

**Revised assumption:** CV remains **strongest** QUIKCVS source. Manual **confirms** CV segment semantics; does not change need for Rate_Table vs PDAGE parity before routing switch.  

**Source tables to inspect:** `Rate_Table_Extract_20260427.csv` (current); `PDAGE_AgeDuration_Rates_Extract_20260530.csv` TYPE=CV; segment CV via `PCOVRSGT` → rate pointer.  

**Segment path to trace:** `PPRDF → PCOMP → PCOVR → PCOVRSGT → (CV segment) → PDAGE or PAAGE/PAAGERAT` per rate type.  

**Still blocked?** **No (source)** — PSEGT CV segment wired 8/8; Rate_Table + PDAGE rows on all 8 coverages. Parity + reference DBF remain.  

**Recommended next action:** Run CV parity; confirm all 8 ISWL MPLANs in emitted QuikCvs.  

**Code change now?** **No**

---

## QUIKUINT

**Area:** Interest values → QUIKUINT  

**Prior assumption:** Partial via `quikplan.NFOINT` + `quikdvdp.MDEPINT` (4.50%); sources TBD (`PRBENINT`, PPBEN `FV_GUAR_RATE`).  

**Manual finding:** ISWL is UL-style; interest via segments **A1** (current), **G1** (guaranteed), **LN** (loan); declared interest tables (`PDINT`/`PDINTTBL`); monthaversary rules (`UI`). Product Book supports QUIKUINT-class setup beyond WL NFOINT.  

**Revised assumption:** **NFOINT/MDEPINT alone are insufficient** for full ISWL interest per manual + governance. Authoritative path is **A1/G1/LN segment trace** → rate/constants, with PPBEN `FV_GUAR_RATE=4.50` as **validation** evidence only.  

**Source tables to inspect:** `PRBENINT_BenefitRatesINT_Extract_20260530.csv`; **`PDINT`/`PDINTTBL` (received 20260629)**; `PPBEN` (`FV_GUAR_RATE`); `PLOAN` (`INTEREST_RATE` for loan validation).  

**Segment path to trace:** `PCOVRSGT → A1 / G1 / LN → PDINT/PDINTTBL or PRBENINT or PSEGT constant`.  

**Still blocked?** **Partially** — PSEGT A1/G1/LN wired 8/8; PDINT CENII A1 **4.50%**; no QUIKUINT loader/schema; G1/LN not in PDINT TYPE_CODE.  

**SME question needed?** **Yes** — PDINT IDENT→8 MPLAN map; QUIKUINT field layout; G1 vs NFOINT 4.50%.  

**Recommended next action:** ~~Request PSEGT/PDINT~~ **DONE** — obtain QUIKUINT DBF; confirm CENII applies to all ISWL variants.  

**Code change now?** **No**

---

## Expenses

**Area:** Expenses  

**Prior assumption:** Unknown product expense tables; partial `quikridr.MANNLFEE` from `POLICY_FEE`; search UF/U1/U2/U3 in PCOVR/PCOMP.  

**Manual finding:** Expense segments UF, U1, U2, U3, G2, G3, GF; expenses may be **nested in BP/BI/UG/UH/UX/UY/UZ** premium logic, not standalone tables.  

**Revised assumption:** Expenses are **multi-component and possibly embedded** in billable premium assembly — not a single `POLICY_FEE` column. MANNLFEE is at best one fee dimension.  

**Source tables to inspect:** `PCOMP`, `PCOVR`, `PCOVRSGT`; premium segments BP/BI/UG/UH/UX/UY/UZ; policy validation `PPBEN.BENEFIT_FEE`, `PPRBNUL` if present.  

**Segment path to trace:** `UF/U1/U2/U3/G2/G3/GF` and nested references from `BP/BI/UG/UH/UX/UY/UZ`.  

**Still blocked?** **Partially** — UF on PSEGT via 659 CEN II slots (8/8 wiring); **U1/U2/U3/G2/G3/GF absent** from PSEGT extract.  

**SME question needed?** **Yes** — expense components in nested BP/UG/UH vs standalone UF; MANNLFEE scope.  

**Recommended next action:** SME confirm expense model; decode UF Rate_Table rows on 659 CEN II.  

**Code change now?** **No**

---

## QUIKCOI

**Area:** Current COI → QUIKCOI  

**Prior assumption:** PAAGERAT `TYPE_CODE=NC` ≈ current COI (690 ISWL rows); trace U6 segment as alternate.  

**Manual finding:** **NC = Net Premium Credited — NOT current COI.** **U6 = Current COI Rates Segment.** COI depends on NAR/corridor/monthaversary (NR, UL, UI, FC, MR).  

**Revised assumption:** **Primary candidate is U6 segment** (and rate rows resolved from U6), **not NC.** Extract `TYPE_CODE=U6` (800 ISWL rows) may align with U6 segment if linkage proves it — still not direct emit. NC rows are **misclassified** in prior research as COI.  

**Source tables to inspect:** `PAAGERAT` / `PAAGE` / `PDAGE` rows resolved from **U6** segment (not NC); `PPBEN` UV fields (disproven for rates).  

**Segment path to trace:** `PCOVRSGT → U6 → rate table`; also NR, UL, UI, FC, MR for COI context.  

**Still blocked?** **Yes** — no loader; NC path **withdrawn**; U6 trace not done; QUIKCOI schema absent.  

**SME question needed?** **Yes** — confirm U6 is ISWL current COI authority; confirm NC is out of scope for QUIKCOI.  

**Recommended next action:** Search `PCOVRSGT` for U6 on ISWL coverages; map U6 to PAAGERAT/PDAGE rows; compare to 800 ISWL U6 extract rows.  

**Code change now?** **No**

---

## QUIKGCOI

**Area:** Guaranteed COI → QUIKGCOI  

**Prior assumption:** PAAGERAT `TYPE_CODE=U6` ≈ guaranteed COI (800 ISWL rows) — conflict with segment doc saying U6=current.  

**Manual finding:** **U5 = Guaranteed COI Rates Segment.** U6 is **current** COI, not guaranteed.  

**Revised assumption:** **Primary candidate is U5 segment** → resolved rate table. PAAGERAT **`TYPE_CODE=U5`** (200 ISWL rows) is more credible for GCOI than U6. Prior U6→GCOI mapping is **incorrect per manual**.  

**Source tables to inspect:** `PAAGERAT` U5 rows; `PAAGE`/`PDAGE` if U5 segment rate type requires; all 8 coverages via segment trace.  

**Segment path to trace:** `PCOVRSGT → U5 → rate table`; supporting NR/UL/FC as for QUIKCOI.  

**Still blocked?** **Yes** — no loader; U5 trace not done; incomplete coverage if U5 rows sparse on senior plans.  

**SME question needed?** **Yes** — confirm U5 is guaranteed COI authority for ISWL.  

**Recommended next action:** Trace U5 on all 8 ISWL coverages; profile PAAGERAT U5 by coverage; abandon U6-as-GCOI hypothesis.  

**Code change now?** **No**

---

## QUIKISSC

**Area:** Surrender charges → QUIKISSC  

**Prior assumption:** SR/SL preferred; PDAGE TP/TX (2,128 ISWL rows each) as **inference-only** surrender candidates.  

**Manual finding:** **SR → SL** preferred path. **TP = Tax Valuation Premiums; TX = Tax Reserve Factors** — not surrender. U7/U8 legacy fallback.  

**Revised assumption:** **TP/TX removed from surrender candidates.** Primary path **SR → SL** only; U7/U8 if SR/SL absent. Prior ZIP “TP/TX candidate” finding is **superseded**.  

**Source tables to inspect:** `PCOVRSGT` for SR/SL/U7/U8; policy fields `PPBENTYP.BF_CURR_SURR_LOAD`, `PPRBNUL.SURR_LOAD`; **not** PDAGE TP/TX for QUIKISSC.  

**Segment path to trace:** `PCOVRSGT → SR → SL → rate or constant`; fallback U7/U8.  

**Still blocked?** **Yes** — no loader; SR/SL trace not performed; QUIKISSC schema absent.  

**SME question needed?** **Yes** — SR/SL vs U7/U8 for CSO ISWL; confirm TP/TX are tax-only.  

**Recommended next action:** Trace SR on ISWL coverages; resolve SL child segment; validate against policy surrender load fields.  

**Code change now?** **No**

---

## QUIKGPS

**Area:** Gross premiums → QUIKGPS  

**Prior assumption:** PR disproven (0 ISWL rows); BP inferred as GP candidate (1,164 ISWL rows); PR loader exists but empty for ISWL.  

**Manual finding:** **BP = Billable Premium Segment** — credible premium source. **PR = Premium Segment** (standard but absent in extract). Premium assembly may involve BI, UG, UH, UX, UY, UZ, MP.  

**Revised assumption:** **BP is the elevated primary candidate** for ISWL billable/gross premium, not PR. Segment linkage must prove BP → QUIKGPS. BP may embed expense loads (U1/U2/U3).  

**Source tables to inspect:** `PAAGERAT` BP rows by coverage; `PDAGE` if BP rate type is duration-based; `PPBEN` (`ANN_PREM_PER_UNIT`, `MODE_PREMIUM`); `PPRBNUL` premium fields.  

**Segment path to trace:** `PCOVRSGT → BP (or BI/UG/UH/UX/UY/UZ/MP) → PAAGERAT/PDAGE`; check nested U1/U2/U3.  

**Still blocked?** **Yes** — no BP loader; PR path confirmed empty for ISWL; VARGP axis alignment unvalidated.  

**SME question needed?** **Yes** — BP vs BI/UG/UH for QUIKGPS; whether QuikGps grid matches BP rate shape.  

**Recommended next action:** Trace BP on all 8 ISWL coverages; profile PAAGERAT BP dimensions; compare to policy premium fields.  

**Code change now?** **No**

---

## Cross-cutting revision summary

| Topic | Prior (extract inference) | After Product Book |
|-------|---------------------------|-------------------|
| NC | QUIKCOI candidate | **Withdrawn** — Net Premium Credited |
| U6 | QUIKGCOI candidate | **QUIKCOI** candidate |
| U5 | Mentioned, underused | **QUIKGCOI** primary candidate |
| BP | GP candidate (inferred) | **QUIKGPS** primary candidate (Billable Premium) |
| PR | Standard GP path | Standard segment; **zero ISWL rows** |
| TP/TX | QUIKISSC inference | **Removed** — tax valuation/reserve |
| SR/SL | Preferred (manual ref) | **Required** primary QUIKISSC path |
| Mapping method | TYPE_CODE grep | **Segment hierarchy trace mandatory** |

---

## Recommended research sequence (unchanged priority, revised paths)

1. **QUIKCVS** — CV parity (unchanged).  
2. **Segment trace on PCOVRSGT** for U6, U5, BP, SR/SL, A1/G1/LN, UF/U1/U2/U3 across 8 ISWL coverages.  
3. **Request PSEGT + PDINT** extracts (missing from May ZIP).  
4. **SME confirmation** (Eric question list in addendum §14).  
5. **Gap report implementation items** — only after segment proof + schemas.

---

**Related:** `ISWL_Product_Book_Manual_Findings_Addendum.md` | `ISWL_Implementation_Gap_Report.md`
