# ISWL Segment Trace Report

> **Superseded in part by:** [`ISWL_Segment_Trace_Addendum_20260629.md`](ISWL_Segment_Trace_Addendum_20260629.md) — PSEGT/PDINT/PDINTTBL extracts received (Issue #31). The 2026-06-28 blocker on missing PSEGT is **removed**. Use the addendum for current hierarchy status.

**Date:** 2026-06-28  
**Mode:** Research only — no code changes  
**Authority chain attempted:** `PPRDF → PCOMP → PCOVR → PCOVRSGT → Segment → Rate Table / Constant`

## Master references used

- `docs/research/ISWL_LifePRO_to_QLAdmin_Master_Reference.md`
- `docs/research/ISWL_Implementation_Gap_Report.md`
- `docs/research/ISWL_Product_Book_Manual_Findings_Addendum.md`
- `docs/research/ISWL_Gap_Report_Manual_Revised_Summary.md`

## Executive summary

| QLA area | Hierarchy trace | Authoritative source (proven) | Implementation readiness |
|----------|-----------------|------------------------------|--------------------------|
| QUIKCVS | Partial | `PDAGE` + April `Rate_Table` TYPE=CV (parent COVERAGE_ID) | **Routing ready**; parity analysis needed |
| QUIKUINT | **Blocked** | No PDINT/PDINTTBL/PSEGT; PPBEN FV_GUAR_RATE constant | **Blocked** — missing extracts |
| Expenses | **Blocked** | No typed rate rows for UF/U1–U3/G2/G3/GF in ISWL extracts | **Blocked** |
| QUIKCOI | Partial | PAAGERAT TYPE=U6 via segment chain → **658 CEN SD**, **679 CEN SD** only (800 rows) — Product Book U6 slot **not proven** | **SME + PSEGT** |
| QUIKGCOI | Partial | PAAGERAT TYPE=U5 → **679 CEN SD** only (200 rows) — not hierarchy-proven | **SME + PSEGT** |
| QUIKISSC | Partial | PDAGE/Rate_Table TP/TX present but **withdrawn** as surrender; SR/SL hierarchy not resolved | **SME + PSEGT** |
| QUIKGPS | Partial | PAAGERAT TYPE=BP — **not hierarchy-proven**; PR=0 confirmed | **SME + PSEGT** |

### Critical blocker

**`PSEGT` is not in the May 20260530 ZIP** (nor repo). Without PSEGT, Product Book segment codes (`U6`, `U5`, `BP`, `CV`, `A1`, …) **cannot be authoritatively mapped** to `PCOVRSGT` sequence slots or `SEGT_ID` values. This trace documents **partial** hierarchy plus **rate-table correlation** resolved through the **PAAGERAT → PCOVRSGT → parent COVERAGE_ID** chain where applicable.

### Segment resolution proof (PAAGERAT chain)

Mandatory chain applied: `PAAGERAT.COVERAGE_ID` = `PCOVRSGT.SEGT_ID` → parent `COVERAGE_ID`.

**U6 (current COI candidate):**
- Parent `658 CEN SD`: **400** rows; PAAGERAT.COVERAGE_ID (SEGT_ID) samples: `658 CEN I`
- Parent `679 CEN SD`: **400** rows; PAAGERAT.COVERAGE_ID (SEGT_ID) samples: `659 CEN II`

**U5 (guaranteed COI candidate):**
- Parent `679 CEN SD`: **200** rows; PAAGERAT.COVERAGE_ID (SEGT_ID) samples: `659 CEN II`

**BP (billable premium candidate):**
- Parent `658 CEN SD`: **444** rows; PAAGERAT.COVERAGE_ID (SEGT_ID) samples: `658 CEN I`, `658 CEN SD`
- Parent `659 CEN SD`: **152** rows; PAAGERAT.COVERAGE_ID (SEGT_ID) samples: `659 CEN SD`
- Parent `669 SR GD`: **172** rows; PAAGERAT.COVERAGE_ID (SEGT_ID) samples: `659 CEN SR`
- Parent `679 CEN SD`: **396** rows; PAAGERAT.COVERAGE_ID (SEGT_ID) samples: `659 CEN II`, `679 CEN SD`

**NC (withdrawn — net premium credited):**
- Parent `658 CEN SD`: **294** rows; PAAGERAT.COVERAGE_ID (SEGT_ID) samples: `658 CEN I`
- Parent `679 CEN SD`: **396** rows; PAAGERAT.COVERAGE_ID (SEGT_ID) samples: `659 CEN II`, `679 CEN SD`

**Prior direct COVERAGE_ID counting without segment resolution is withdrawn** — e.g. U6 rows attach to `658 CEN SD` / `679 CEN SD` parents via SEGT_ID `658 CEN I` / `659 CEN II`, not to flagship coverages directly.

### PPRDF linkage

PPRDF contains **no** rows matching ISWL coverage text. ISWL hierarchy **starts at PCOMP** where `PRODUCT_ID` equals coverage id (e.g. `658 CEN I`). PPRDF ISWL-linked rows via PCOMP keys: **0**.

### Withdrawn hypotheses (confirmed)

- **`NC` → QUIKCOI** — withdrawn (Net Premium Credited, not COI)
- **`TYPE_CODE=U6` → QUIKGCOI** — withdrawn; manual + trace supports U6 as **current** COI candidate only
- **`TP`/`TX` → QUIKISSC** — withdrawn (tax valuation / reserve)
- **`PR` → QUIKGPS for ISWL** — zero rows all sources

---

## QUIKUINT

### Segment(s) traced

`A1`, `G1`, `LN`

### Current repo behavior

Partial: `quikplan.NFOINT` + `quikdvdp.MDEPINT=4.50` for ISWL allowlist (`app.py` ~5618). No QUIKUINT loader.

### Source evidence

PPRDF rows (ISWL filter): 0. ZIP members: PDINT=None, PSEGT=None. PCOVR `ANN_GUAR_RATE` present on ISWL coverages (e.g. 658 CEN I). PPBEN `FV_GUAR_RATE=4.50` on 2,159 ISWL rows (May ZIP prior research).

### Segment hierarchy confirmed?

**Partial only** — `PSEGT` extract absent; `PCOVRSGT` slot→`SEGT_ID` mapped; Product Book segment type (e.g. U6) not resolved to slot without PSEGT.

### Source table resolved?

**Not resolved** — interest segments A1/G1/LN require PDINT/PDINTTBL/PRBENINT or PSEGT linkage; none available.

### Dimensions preserved?

See matrix — varies by table.

### All 8 ISWL MPLANs covered?

**0/8** coverages show rate rows for primary segment codes.

### QLAdmin target supported?

**No** — blocked by missing interest extracts.

### Gaps

- PSEGT absent
- PDINT/PDINTTBL absent from May ZIP
- Cannot trace A1/G1/LN through PCOVRSGT

### SME confirmation needed?

**Yes** — confirm whether 4.50% plan constant is sufficient vs policy-level PPBEN.

### Recommended next action

**Source Dependency Agent** — request PDINT/PDINTTBL/PSEGT extracts.

### Code change needed now? Yes/No

**No**

### Business decision needed? Yes/No

**Yes**


## Expenses

### Segment(s) traced

`UF`, `U1`, `U2`, `U3`, `G2`, `G3`, `GF`, `BI`, `UG`, `UH`, `UX`, `UY`, `UZ`

### Current repo behavior

Partial: Issue #21C maps `POLICY_FEE` → `quikridr.MANNLFEE` only.

### Source evidence

- `659 CEN II`: PAAGERAT=0, PDAGE=12, Rate_Table=1\n\nNo ISWL PAAGERAT/PDAGE rows for U1,U2,U3,G2,G3,GF. PCOMP lists riders (WP, FR, CR) but not expense segment types.

### Segment hierarchy confirmed?

**Partial only** — `PSEGT` extract absent; `PCOVRSGT` slot→`SEGT_ID` mapped; Product Book segment type (e.g. U6) not resolved to slot without PSEGT.

### Source table resolved?

**Not resolved** for UL expense segments.

### Dimensions preserved?

See matrix — varies by table.

### All 8 ISWL MPLANs covered?

**1/8** coverages show rate rows for primary segment codes.

### QLAdmin target supported?

**No**

### Gaps

- No rate rows for expense TYPE_CODEs\n- BP nesting (UF/U1 inside BP) not traceable without PSEGT

### SME confirmation needed?

**Yes** — segment type ↔ PCOVRSGT slot linkage.

### Recommended next action

SME: identify LifePRO table for monthly expense charges on ISWL.

### Code change needed now? Yes/No

**No**

### Business decision needed? Yes/No

**Yes**


## QUIKCOI

### Segment(s) traced

`U6`, `NR`, `UL`, `UI`, `FC`, `MR`, `NC`

### Current repo behavior

Not implemented. NC/U6/BP excluded from `TYPE_TO_TABLE` in `rate_dbf_schema.py`.

### Source evidence

### U6 (current COI candidate)\n- `658 CEN SD`: PAAGERAT=400, PDAGE=0, Rate_Table=0
- `679 CEN SD`: PAAGERAT=400, PDAGE=0, Rate_Table=0\n\n### PAAGERAT segment chain (U6)\n- Parent `658 CEN SD`: **400** rows; PAAGERAT.COVERAGE_ID (SEGT_ID) samples: `658 CEN I`
- Parent `679 CEN SD`: **400** rows; PAAGERAT.COVERAGE_ID (SEGT_ID) samples: `659 CEN II`\n\n### NC (withdrawn as COI)\n- `658 CEN SD`: PAAGERAT=294, PDAGE=0, Rate_Table=0
- `679 CEN SD`: PAAGERAT=396, PDAGE=0, Rate_Table=0\n\n- Parent `658 CEN SD`: **294** rows; PAAGERAT.COVERAGE_ID (SEGT_ID) samples: `658 CEN I`
- Parent `679 CEN SD`: **396** rows; PAAGERAT.COVERAGE_ID (SEGT_ID) samples: `659 CEN II`, `679 CEN SD`\n\nPCOVRSGT for 658 CEN I: 56 slots, active SEGT_IDs include `658 CEN I`, `659 CEN II`, `LIFE`, `LIFEWCV`, `DEFRA`, `AA9B2`, `BMA658`, `IBA01 45`, `L14` — **none labeled U6**.

### Segment hierarchy confirmed?

**Partial only** — `PSEGT` extract absent; `PCOVRSGT` slot→`SEGT_ID` mapped; Product Book segment type (e.g. U6) not resolved to slot without PSEGT.

### Source table resolved?

Correlated: **PAAGERAT** TYPE=U6 (800 ISWL rows, 658 CEN I + 659 CEN II only). **Not hierarchy-proven.**

### Dimensions preserved?

PAAGERAT U6: attained age (SEQ), sex, UW class — differs from CV issue-age×duration.

### All 8 ISWL MPLANs covered?

**2/8** coverages show rate rows for primary segment codes.

### QLAdmin target supported?

**Partial data** for 2/8 coverages (658 CEN SD, 679 CEN SD) after segment resolution; flagship 658 CEN I / 659 CEN II have zero direct PAAGERAT U6 rows.

### Gaps

- 659 SR GD, 669 SR GD: **zero PAAGERAT** for any TYPE\n- U6 absent for 658 CEN SD, 659 CEN SR/SD, 679 CEN SD\n- NC must not map to QUIKCOI

### SME confirmation needed?

**Yes** — confirm U6 segment slots; explain senior plan COI source.

### Recommended next action

Request PSEGT extract; SME map slots to Product Book codes.

### Code change needed now? Yes/No

**No**

### Business decision needed? Yes/No

**Yes**


## QUIKGCOI

### Segment(s) traced

`U5`

### Current repo behavior

Not implemented.

### Source evidence

- `679 CEN SD`: PAAGERAT=200, PDAGE=0, Rate_Table=0

### Segment hierarchy confirmed?

**Partial only** — `PSEGT` extract absent; `PCOVRSGT` slot→`SEGT_ID` mapped; Product Book segment type (e.g. U6) not resolved to slot without PSEGT.

### Source table resolved?

Correlated: **PAAGERAT** TYPE=U5 (200 ISWL rows). Not hierarchy-proven.

### Dimensions preserved?

See matrix — varies by table.

### All 8 ISWL MPLANs covered?

**1/8** coverages show rate rows for primary segment codes.

### QLAdmin target supported?

**Partial** — sparse coverage across fleet.

### Gaps

U6 is **not** used as guaranteed COI (confirmed policy). U5 rows do not cover all 8 MPLANs.

### SME confirmation needed?

**Yes**

### Recommended next action

Request PSEGT extract; SME map slots to Product Book codes.

### Code change needed now? Yes/No

**No**

### Business decision needed? Yes/No

**Yes**


## QUIKISSC

### Segment(s) traced

`SR`, `SL`, `U7`, `U8`, `TP`, `TX`

### Current repo behavior

Not implemented. TP/TX/SL in `EXCLUDED_TYPE_CODES`.

### Source evidence

### SR/SL\n- No ISWL rows for this TYPE_CODE in available extracts.\n- `659 CEN II`: PAAGERAT=0, PDAGE=12, Rate_Table=14\n\n### TP/TX (withdrawn)\n- `659 CEN II`: PAAGERAT=0, PDAGE=2128, Rate_Table=19780\n- `659 CEN II`: PAAGERAT=0, PDAGE=2128, Rate_Table=19780

### Segment hierarchy confirmed?

**Partial only** — `PSEGT` extract absent; `PCOVRSGT` slot→`SEGT_ID` mapped; Product Book segment type (e.g. U6) not resolved to slot without PSEGT.

### Source table resolved?

**Not resolved** — SR→SL parent/child not found in PCOVRSGT SEGT_ID labels.

### Dimensions preserved?

See matrix — varies by table.

### All 8 ISWL MPLANs covered?

**1/8** coverages show rate rows for primary segment codes.

### QLAdmin target supported?

**No** — surrender path not proven.

### Gaps

TP/TX are tax factors, not surrender. PCOMP has SC (discount) components, not SR/SL Product Book segments.

### SME confirmation needed?

**Yes** — confirm SR/SL slot numbers on ISWL forms.

### Recommended next action

Request PSEGT extract; SME map slots to Product Book codes.

### Code change needed now? Yes/No

**No**

### Business decision needed? Yes/No

**Yes**


## QUIKGPS

### Segment(s) traced

`BP`, `BI`, `UG`, `UH`, `UX`, `UY`, `UZ`, `MP`, `PR`

### Current repo behavior

`paagerat_pr_loader.py` filters PR only; zero ISWL PR rows.

### Source evidence

- `658 CEN SD`: PAAGERAT=444, PDAGE=0, Rate_Table=0
- `659 CEN SD`: PAAGERAT=152, PDAGE=0, Rate_Table=0
- `669 SR GD`: PAAGERAT=172, PDAGE=0, Rate_Table=0
- `679 CEN SD`: PAAGERAT=396, PDAGE=0, Rate_Table=0\n\nPR (all sources): **0 ISWL rows**.

### Segment hierarchy confirmed?

**Partial only** — `PSEGT` extract absent; `PCOVRSGT` slot→`SEGT_ID` mapped; Product Book segment type (e.g. U6) not resolved to slot without PSEGT.

### Source table resolved?

Correlated: **PAAGERAT** TYPE=BP (1,164 ISWL rows). Not hierarchy-proven.

### Dimensions preserved?

See matrix — varies by table.

### All 8 ISWL MPLANs covered?

**4/8** coverages show rate rows for primary segment codes.

### QLAdmin target supported?

**Partial data** — 6/8 coverages have BP rows; 659 SR GD / 669 SR GD lack PAAGERAT entirely.

### Gaps

BP segment slot unknown without PSEGT. Premium assembly segments UG/UH/UX/UY/UZ/MP: no ISWL rate rows.

### SME confirmation needed?

**Yes**

### Recommended next action

Request PSEGT extract; SME map slots to Product Book codes.

### Code change needed now? Yes/No

**No**

### Business decision needed? Yes/No

**Yes**


## QUIKCVS

### Segment(s) traced

`CV`

### Current repo behavior

**Implemented routing**: CV → QuikCvs via `rate_pipeline.py` / `TYPE_TO_TABLE`. Uses April Rate_Table.

### Source evidence

- `658 CEN I`: PAAGERAT=0, PDAGE=2112, Rate_Table=18124
- `658 CEN SD`: PAAGERAT=0, PDAGE=1824, Rate_Table=9113
- `659 CEN II`: PAAGERAT=0, PDAGE=1104, Rate_Table=9678
- `659 CEN SD`: PAAGERAT=0, PDAGE=1824, Rate_Table=9288
- `659 CEN SR`: PAAGERAT=0, PDAGE=2064, Rate_Table=9678
- `659 SR GD`: PAAGERAT=0, PDAGE=1500, Rate_Table=9700
- `669 SR GD`: PAAGERAT=0, PDAGE=864, Rate_Table=2340
- `679 CEN SD`: PAAGERAT=0, PDAGE=792, Rate_Table=4350\n\nPCOVRSGT SEGT_ID `LIFEWCV` on 658 CEN I seq 44 (semantic hint only — not proof).

### Segment hierarchy confirmed?

**Partial only** — `PSEGT` extract absent; `PCOVRSGT` slot→`SEGT_ID` mapped; Product Book segment type (e.g. U6) not resolved to slot without PSEGT.

### Source table resolved?

**PDAGE** (12,084 ISWL CV rows, May) + **Rate_Table_Extract_20260427** (repo). Parity not validated.

### Dimensions preserved?

Issue age × duration × sex × UW (VARGP=2 style in Rate_Table).

### All 8 ISWL MPLANs covered?

**8/8** coverages show rate rows for primary segment codes.

### QLAdmin target supported?

**Yes for loader path** — strongest ISWL area; parity analysis still required.

### Gaps

May PDAGE vs April Rate_Table equivalence unproven. PSEGT CV slot not confirmed.

### SME confirmation needed?

**Optional** — parity sign-off.

### Recommended next action

Run PDAGE vs Rate_Table parity analysis; then Implementation Planning for QUIKCVS hardening.

### Code change needed now? Yes/No

**No** (research phase)

### Business decision needed? Yes/No

**No** (unless parity fails)


## Authoritative source table conclusions

| QLA target | Authoritative source (research conclusion) | Confidence |
|------------|---------------------------------------------|------------|
| QUIKUINT | **Unresolved** — need PDINT/PDINTTBL + PSEGT | Blocked |
| Expenses | **Unresolved** | Blocked |
| QUIKCOI | **PAAGERAT U6** (correlated, 2 plans) — pending PSEGT proof | Low–Medium |
| QUIKGCOI | **PAAGERAT U5** (correlated) — pending PSEGT proof | Low–Medium |
| QUIKISSC | **Unresolved** — SR/SL path not traced | Blocked |
| QUIKGPS | **PAAGERAT BP** (correlated) — PR disproven | Medium (correlation only) |
| QUIKCVS | **PDAGE / Rate_Table CV** at parent COVERAGE_ID | Medium–High |

## PCOVRSGT snapshot (ISWL)

| Coverage | Slots | Active SEGT_ID (sample) |
|----------|-------|-------------------------|
| `658 CEN I` | 56 | `658 CEN I`, `658 CEN I`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `658 CEN I`, `659 CEN II`, `659 CEN II` |
| `658 CEN SD` | 56 | `658 CEN I`, `658 CEN I`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `658 CEN I`, `659 CEN II`, `659 CEN II` |
| `659 CEN II` | 56 | `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II` |
| `659 CEN SR` | 56 | `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II` |
| `659 CEN SD` | 56 | `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II` |
| `659 SR GD` | 56 | `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II` |
| `669 SR GD` | 56 | `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II`, `659 CEN II` |
| `679 CEN SD` | 56 | `679 CEN SD`, `679 CEN SD`, `659 CEN II`, `659 CEN II`, `678 CEN SD`, `678 CEN SD`, `659 CEN II`, `659 CEN II` |

---

*Generated by `tools/research/iswl_segment_trace.py`. Rate TYPE_CODE counts are correlation evidence only — not segment hierarchy authority.*
