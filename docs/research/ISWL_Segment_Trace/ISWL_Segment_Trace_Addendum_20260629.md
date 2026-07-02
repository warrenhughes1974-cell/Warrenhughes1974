# ISWL Segment Trace Addendum — 20260629 Extracts

**Supersedes blocker in:** `ISWL_Segment_Trace_Report.md` (2026-06-28)  
**Issue:** #31 follow-up  
**Evidence:** `iswl_segment_trace_bundle_20260629.json`

---

## Blocker removed

The May 20260530 ZIP blocker on **PSEGT**, **PDINT**, and **PDINTTBL** is **removed**.

| File | Location |
|------|----------|
| PSEGT | `QLA_Migration/Source/PSEGT_Segment_Extract_20260629.csv` |
| PDINT | `QLA_Migration/Source/PDINT_DeclaredInterestRates_Extract_20260629.csv` |
| PDINTTBL | `QLA_Migration/Source/PDINTTBL_DeclaredInterestRates_Extract_20260629.csv` |

---

## Revised executive summary

| QLA area | Prior (2026-06-28) | After 20260629 extracts |
|----------|---------------------|-------------------------|
| **QUIKCVS** | Partial | **Fully resolved** (8/8; parity check open) |
| **QUIKUINT** | Blocked | **Partially resolved** (PSEGT A1/G1/LN wired; PDINT CENII 4.50%) |
| **QUIKCOI** | Partial | **Partially resolved** (U6 wired 8/8; PAAGERAT 2/8) |
| **QUIKGCOI** | Partial | **Partially resolved** (U5 wired 8/8; PAAGERAT 1/8) |
| **QUIKGPS** | Partial | **Partially resolved** (BP wired 8/8; PAAGERAT 4/8) |
| **QUIKISSC** | Blocked | **Partially resolved** (SR/SL wired 8/8; rate pointer TBD) |
| **Expenses** | Blocked | **Partially resolved** (UF wired; U1–U3/G2/G3/GF absent) |

---

## Hierarchy now traceable

```text
PCOVR → PCOVRSGT.SEGT_ID → PSEGT.SEGMENT_ID → PSEGT.SEGT_TYPE → PAAGERAT | PDAGE | Rate_Table | PDINT/PDINTTBL
```

- ISWL PCOVRSGT active slots: **191**
- Slots resolving in PSEGT: **185** (96.9%)
- **PPRDF** still not in repo — top link absent

---

## Target code summary (PCOVRSGT → PSEGT, 8 ISWL coverages)

| Code | Coverages wired | Authoritative |
|------|----------------:|---------------|
| U5, U6, BP, CV, A1, G1, LN, SR, SL, UF | **8/8** | Partial (CV strongest) |
| U1, U2, U3, G2, G3, GF | **0/8** | No |

Full matrix: `ISWL_Segment_Trace_Matrix_20260629.csv`

---

## Key finding — segment dictionary vs native coverage

- **Slot wiring (8/8):** Most ISWL coverages reference shared segment IDs (`659 CEN II`, `658 CEN I`, `L14`, …), inheriting full UL segment type sets through PSEGT.
- **Native dictionary:** When `PSEGT.SEGMENT_ID = coverage`, senior plans (`659 SR GD`, `669 SR GD`) often expose only **CV** (+ BP on some) — confirms sparse actuarial setup for grandfathered variants.

---

## Next steps

1. **Implementation Planning Agent** — QUIKCVS parity + conditional emit plan  
2. **SME Review Agent** — PDINT IDENT map; U6/U5 semantics; SR/SL payload decode  
3. **Source Dependency Agent** — **closed** for PSEGT/PDINT; optional PPRDF request remains  

*No converter, loader, catalog, or rulebook changes in this research pass.*
