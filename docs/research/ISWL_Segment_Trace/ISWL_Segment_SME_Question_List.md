# ISWL Segment SME Question List

**Updated:** 2026-06-30 (post-PSEGT Issue #31)  
**Prior P0 blocker (PSEGT/PDINT request):** **Closed**

## Closed by research (no longer ask)

- ~~Provide PSEGT extract~~ — received 20260629
- ~~Provide PDINT/PDINTTBL~~ — received 20260629
- NC as QUIKCOI — withdrawn (Net Premium Credited)
- U6 as QUIKGCOI — withdrawn
- TP/TX as QUIKISSC — withdrawn
- PR as ISWL QUIKGPS — zero rows confirmed

## P0 — Still blocking implementation

1. **PDINT IDENT → MPLAN:** Map `CENII`, `IBA01`, and other IDENTs to each of the 8 ISWL MPLANs for credited (A1) vs guaranteed (G1) vs loan (LN) interest.
2. **QUIKISSC rate source:** PSEGT confirms SR/SL on `659 CEN II` for all 8 coverages — which rate table or segment data field holds surrender charge values?
3. **659 SR GD / 669 SR GD:** Zero PAAGERAT rows for U6/BP — where are COI and gross premium rates for these senior/grandfathered plans?
4. **QUIKCVS authoritative path:** May PDAGE CV vs April Rate_Table CV — which is production source?

## P1 — Mapping confirmation

5. Confirm **U6** (658 CEN I / 659 CEN II segments) → **QUIKCOI** and **U5** → **QUIKGCOI** per Product Book.
6. Confirm **BP** segments → **QUIKGPS** (billable premium).
7. Confirm expense segment **UF** is active on ISWL; are **U1/U2/U3/G2/G3/GF** unused for this product family (absent from PSEGT)?

## P2 — Implementation detail

8. Is plan-level **4.50%** sufficient for QUIKUINT guaranteed, or must policy-level PPBEN `FV_GUAR_RATE` drive credited rates?
9. Should PAAGERAT rows keyed to `658 CEN I` / `659 CEN II` SEGT_IDs roll up to parent coverages (658 CEN SD, 679 CEN SD) or emit per flagship coverage?

## PSEGT research notes for SME context

- PSEGT uses **multiple rows per SEGMENT_ID** (one row per supported SEGT_TYPE).
- **`659 CEN II`** is the primary UL hub segment (U5, U6, BP, CV, A1, G1, LN, SR, SL, UF, …).
- All 8 ISWL coverages reference shared segments via PCOVRSGT (not isolated per MPLAN).
