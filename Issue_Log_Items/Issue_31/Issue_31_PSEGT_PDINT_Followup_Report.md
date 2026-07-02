# Issue #31 Follow-up Research — PSEGT / PDINT / PDINTTBL Validation

**Date:** 2026-06-30  
**Mode:** Research only — no converter, loader, catalog, rulebook, or output changes  
**New extracts:** `QLA_Migration/Source/` (20260629)  
**Machine evidence:** `docs/research/ISWL_Segment_Trace/iswl_segment_trace_bundle_20260629.json`

---

## 1. Executive summary

The **primary source-data dependency** identified for Issue #31 — missing **PSEGT**, **PDINT**, and **PDINTTBL** — is **removed**. All three extracts validate and join into the ISWL segment hierarchy at the `PCOVRSGT → PSEGT → rates/PDINT` layer.

**Issue #31 overall:** **Partially resolved** — source dependency cleared; **not** fully closed for QLAdmin implementation.

| Layer | Status |
|-------|--------|
| Source extracts (PSEGT / PDINT / PDINTTBL) | **Resolved** |
| Hierarchy trace through PSEGT | **Resolved** (185/191 ISWL PCOVRSGT slots → PSEGT) |
| QUIKCVS routing | **Fully resolved** (8/8 coverages; parity check remains) |
| QUIKUINT / COI / GCOI / GPS / ISSC / Expenses | **Partially resolved** — segment wiring proven; rate rows / QLAdmin schema gaps remain |
| PPRDF top-of-chain | **Still absent** from repo extracts |

---

## 2. Extract validation

| Extract | Rows | Size | Key fields | Quality |
|---------|-----:|-----:|------------|---------|
| **PSEGT** | 696 | 446,720 B | SEGMENT_ID, SEGT_TYPE, SEGT_DATA, SEGT_KEY0 | No null SEGMENT_ID; 221 distinct segment IDs; 64 SEGT_TYPE values |
| **PDINT** | 10 | 15,240 B | IDENT, TYPE_CODE, DINT_RULE, EFF_DATE, date range | 8 IDENTS; TYPE_CODE A1/C1/C3 |
| **PDINTTBL** | 37 | 6,084 B | IDENT, TYPE_CODE, DECLARED_RATE, START/END_DATE | Rate schedules for PDINT rules |

### PSEGT notes

- One row per `(SEGMENT_ID, SEGT_TYPE)` — segment **capabilities** keyed by segment instance ID (often equals coverage ID, e.g. `659 CEN II`).
- Target types present fleet-wide in PSEGT: U5 (3), U6 (4), BP (8), CV (40), A1 (2), G1 (2), LN (7), SR (2), SL (2), UF (1).
- **Absent fleet-wide:** U1, U2, U3, G2, G3, GF (0 rows each).

### PDINT / PDINTTBL notes

- **CENII + A1:** PDINTTBL shows **4.50%** from 2002-01-01 through 2099-12-31 — aligns with Issue #21D ISWL MDEPINT / PPBEN `FV_GUAR_RATE` validation path.
- **No PDINT rows with TYPE_CODE G1 or LN** in this extract — guaranteed/loan interest may be embedded in PSEGT payloads or other IDENTS.
- IDENTS: CENII, DAR01, DIV01, IBA01, L1001, SAL01, SPWL, SPWL+ (inferred link: **CENII → 659 CEN II** segment dictionary).

---

## 3. Hierarchy trace (re-evaluated)

### Intended chain

```text
PPRDF → PCOMP → PCOVR → PCOVRSGT → PSEGT → PAAGE/PAAGERAT or PDAGE or PDINT/PDINTTBL
```

### What is now traceable

| Link | Status | Evidence |
|------|--------|----------|
| PCOVR → ISWL coverages | **Yes** | 8/8 ISWL coverages in `PCOVR_Coverage_Extract_20260530.csv` |
| PCOVRSGT → ISWL | **Yes** | 191 active (Y) segment slots across 8 coverages |
| PCOVRSGT.SEGT_ID → PSEGT | **Yes** | **185/191** slots resolve (96.9%); 6 orphan SEGT_ID refs |
| PSEGT → Product Book codes | **Yes** | SEGT_TYPE column matches manual codes (U6, U5, BP, CV, A1, …) |
| PSEGT → PDINT | **Partial** | CENII/A1 linked to 659 CEN II; G1/LN not in PDINT extract |
| PSEGT → PAAGERAT / Rate_Table | **Partial** | TYPE_CODE rows exist; coverage attribution uses segment-ID indirection |
| PPRDF | **No** | Not in Source or repo staging |

### Authoritative mapping method

**PCOVRSGT slot resolution:** For each ISWL coverage, active slots reference `SEGT_ID` values; PSEGT returns all `SEGT_TYPE` capabilities for that segment ID. Cross-coverage references are common (e.g. `658 CEN I` slots reference `659 CEN II` segment dictionary).

**Coverage-native dictionary:** `PSEGT.SEGMENT_ID = <coverage>` defines which segment types are **native** to that product (stricter; senior plans often only BP+CV).

---

## 4. Target segment codes — ISWL fleet (PCOVRSGT → PSEGT)

| Code | PSEGT slot mapping (8 ISWL coverages) | Rate rows (any source) | Authoritative for mapping? |
|------|--------------------------------------:|------------------------:|---------------------------|
| **U5** | **8/8** | 200 (679 CEN SD PAAGERAT) | **Partial** — wired; rate on 1/8 |
| **U6** | **8/8** | 800 (658/679 SD variants PAAGERAT) | **Partial** — wired; rate on 2/8 |
| **BP** | **8/8** | 1,164 | **Partial** — wired; rate on 4/8 |
| **CV** | **8/8** | 84,355 + PDAGE | **Yes** — routing proven all 8 |
| **A1** | **8/8** | 0 (PDINT only) | **Partial** — wired; PDINT CENII 4.50% |
| **G1** | **8/8** | 0 | **Partial** — wired via 659 CEN II slots; no PDINT G1 |
| **LN** | **8/8** | 0 | **Partial** — wired via slots; loan rates TBD |
| **SR** | **8/8** | 0 | **Partial** — wired; surrender rate pointer TBD |
| **SL** | **8/8** | 26 (659 CEN II Rate_Table) | **Partial** |
| **UF** | **8/8** | 13 (659 CEN II Rate_Table) | **Partial** |
| **U1–U3, G2, G3, GF** | **0/8** | 0 | **No** — not in PSEGT extract |

Detail matrix: `docs/research/ISWL_Segment_Trace/ISWL_Segment_Trace_Matrix_20260629.csv`

---

## 5. QLAdmin target re-evaluation

| Target | Status | PSEGT wiring | Rate / PDINT data | Remaining blockers |
|--------|--------|:------------:|:-----------------:|------------------|
| **QUIKCVS** | **Fully resolved** | 8/8 | 8/8 (Rate_Table + PDAGE) | PDAGE vs Rate_Table parity sign-off |
| **QUIKUINT** | **Partially resolved** | 8/8 (A1/G1/LN slots) | PDINT A1 for CENII only | QUIKUINT schema; G1/LN PDINT; IDENT→all 8 MPLANs |
| **QUIKCOI** | **Partially resolved** | 8/8 (U6) | 2/8 PAAGERAT U6 | PAAGERAT uses SD parent IDs; SME confirm U6 semantics |
| **QUIKGCOI** | **Partially resolved** | 8/8 (U5) | 1/8 PAAGERAT U5 | Same segment-ID indirection |
| **QUIKGPS** | **Partially resolved** | 8/8 (BP) | 4/8 PAAGERAT BP | PR rows still absent |
| **QUIKISSC** | **Partially resolved** | 8/8 (SR/SL) | 1/8 SL Rate_Table | Decode SR→rate table pointer in PSEGT payload |
| **Expenses** | **Partially resolved** | 8/8 (UF via 659 CEN II) | 1/8 UF | **U1/U2/U3/G2/G3/GF absent** from PSEGT |

---

## 6. Issue #31 resolution recommendation

### Recommend: **Partially resolved — source dependency cleared**

Do **not** mark Issue #31 **fully resolved** for implementation.

| Criterion | Met? |
|-----------|:----:|
| PSEGT extract received and validated | ✅ |
| PDINT / PDINTTBL received and validated | ✅ |
| Primary ZIP/source dependency removed | ✅ |
| All 7 QLA areas implementation-ready | ❌ |
| QLAdmin UL table schemas in repo | ❌ |
| Expense segments U1–U3/G2/G3/GF sourced | ❌ |
| PPRDF chain complete | ❌ |

### Suggested Issue #31 status label

**`Resolved — Source Dependency`** with open child tracks:

1. **Implementation Planning** — QUIKCVS (parity + emit validation)
2. **SME Review** — PDINT IDENT mapping; U6/U5 vs PAAGERAT; SR/SL surrender decode
3. **Development** (future) — QUIKUINT/COI/GCOI/GPS/ISSC loaders after schema sign-off

---

## 7. Client / SME questions still required

1. Map PDINT `IDENT` values (**CENII**, **IBA01**, **SPWL**, etc.) to each of the **8 ISWL MPLANs** for credited vs guaranteed interest.
2. Where are **G1** and **LN** declared rates if not in PDINT TYPE_CODE?
3. Confirm **U6** PAAGERAT rows keyed to SD parent coverages (`658 CEN SD`, `679 CEN SD`) represent COI for all related MPLANs.
4. **SR/SL** — decode PSEGT payload rate pointer (Product Book: SR parent / SL child surrender schedule).
5. **Expenses** — are U1/U2/U3/G2/G3/GF embedded in premium segments (BP/UG/UH) rather than standalone PSEGT types?
6. **659 SR GD / 669 SR GD** — confirm COI/GP rate source given sparse native PSEGT dictionary (CV-only native types).
7. Production authoritative path: **PDAGE vs Rate_Table** for CV emit.

---

## 8. Related deliverables

| File | Purpose |
|------|---------|
| `ISWL_Segment_Trace_Addendum_20260629.md` | Segment trace update |
| `ISWL_Segment_Trace_Matrix_20260629.csv` | Per-code × per-coverage matrix |
| `ISWL_Hierarchy_Trace_20260629.csv` | Slot-level trace |
| `iswl_psegt_target_matrix_20260629.json` | Coverage-native PSEGT dictionary |
| `Issue_31_Resolution_Recommendation.md` | Status gate summary |

---

*Research only. No production code or output modified.*
