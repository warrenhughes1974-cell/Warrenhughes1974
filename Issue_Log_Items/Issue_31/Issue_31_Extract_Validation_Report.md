# Issue #31 — Extract Validation & Segment Trace Report

**Date:** 2026-06-30  
**Mode:** Research / validation only — no code changes  
**Sources:** `QLA_Migration/Source/*_20260629.csv`  
**Baseline:** Prior ISWL segment trace (2026-06-28) + Product Book addendum

---

## A. New Extract Validation Summary

### PSEGT_Segment_Extract_20260629.csv

| Attribute | Value |
|-----------|-------|
| **Row count** | 696 |
| **Size** | 446,720 bytes |
| **Columns** | `SEGMENT_ID`, `SEGT_TYPE`, `SEGT_DATA`, `MOD_CODER`, `MOD_DATE`, `MOD_TIME`, `SEGT_UPD_COUNT`, `SEGT_KEY0`, `ROW_COLUMN` |
| **Key fields** | `SEGMENT_ID` + `SEGT_TYPE` (composite natural key) |
| **Duplicate keys** | **0** on (`SEGMENT_ID`, `SEGT_TYPE`) |
| **Null critical fields** | **0** null `SEGMENT_ID`; **0** null `SEGT_TYPE` |
| **Effective dates** | `MOD_DATE` only (maintenance); rate effective dates live in downstream tables |
| **Rate/segment relationship** | `SEGT_DATA` / `ROW_COLUMN` hex payloads — rate table pointer (not decoded in this pass) |
| **Distinct segment IDs** | 221 |
| **Distinct SEGT_TYPE values** | 64 |

**Structure note:** PSEGT is a **capability registry** — one `SEGMENT_ID` may appear on many rows, each declaring a supported `SEGT_TYPE`.

**Sample rows:**

| SEGMENT_ID | SEGT_TYPE | Notes |
|------------|-----------|-------|
| `0822 620` | PR | Legacy product segment |
| `658 CEN I` | U6 | ISWL current COI segment (also BP, CV, NC, …) |
| `659 CEN II` | U5 | ISWL hub — U5, U6, BP, CV, A1, G1, LN, SR, SL, UF, … |

**Data quality:** Clean keys; no obvious truncation. Six PCOVRSGT ISWL `SEGT_ID`s (e.g. `BMA658`, `DEFRA`) have no PSEGT row — 185/191 slots resolve (96.9%).

---

### PDINT_DeclaredInterestRates_Extract_20260629.csv

| Attribute | Value |
|-----------|-------|
| **Row count** | 10 |
| **Size** | 15,240 bytes |
| **Columns** | `IDENT`, `TYPE_CODE`, `DINT_RULE`, `EFF_DATE`, `SEQ`, `LOW_DATE`, `HIGH_DATE`, `LOW_PROCESS_DUR`, `HIGH_PROCESS_DUR`, `INVESTMENT_CODE`, `RATE_DUR_PERIOD_CD`, `MULTIPLIER`, audit fields |
| **Key fields** | `IDENT` + `TYPE_CODE` + `DINT_RULE` + `EFF_DATE` + `SEQ` |
| **Duplicate keys** | **1** — `SAL01` / C1 / EFF 19000101 / SEQ 1 appears twice |
| **Null critical fields** | None on key columns |
| **Effective dates** | `EFF_DATE`, `LOW_DATE`, `HIGH_DATE` |
| **Distinct IDENTs** | 8 (`CENII`, `DAR01`, `DIV01`, `IBA01`, `L1001`, `SAL01`, `SPWL`, `SPWL+`) |

**Sample:** `CENII` / `A1` / DINT_RULE 0 / EFF 20030813 — rule header pointing to PDINTTBL schedule.

**Data quality:** Small catalog extract; duplicate SAL01 row is minor; **not all 8 ISWL MPLANs represented by IDENT name**.

---

### PDINTTBL_DeclaredInterestRates_Extract_20260629.csv

| Attribute | Value |
|-----------|-------|
| **Row count** | 37 |
| **Size** | 6,084 bytes |
| **Columns** | `IDENT`, `TYPE_CODE`, `DINT_RULE`, `EFF_DATE`, `SEQ`, `IDX`, `START_DATE`, `END_DATE`, `DECLARED_RATE`, `RATE_GUAR_DUR`, `DINT_KEY0` |
| **Key fields** | `IDENT` + `TYPE_CODE` + `DINT_RULE` + `EFF_DATE` + `SEQ` + `IDX` |
| **Duplicate keys** | **1** — same SAL01 key as PDINT |
| **Rate field** | `DECLARED_RATE` (e.g. 4.50000, 7.00000) |
| **Effective dates** | `START_DATE` / `END_DATE` per schedule slice |

**Sample:** `CENII` / A1 — 7.00% (1980–1998), 5.00% (1999–2001), **4.50%** (2002–2099).

---

## B. PSEGT Segment Coverage Matrix

Classification via **mandatory chain:** `PCOVRSGT.SEGT_ID` (active, ISWL) → `PSEGT.SEGMENT_ID` → `PSEGT.SEGT_TYPE`.

| Code | PSEGT global | ISWL 8/8 linked | Classification | Notes |
|------|-------------|-----------------|----------------|-------|
| **U6** | 4 segs | **8/8** | **Confirmed in PSEGT** | Via `658 CEN I`, `659 CEN II`, `678 CEN SD` slots |
| **U5** | 3 segs | **8/8** | **Confirmed in PSEGT** | Primarily `659 CEN II` hub |
| **BP** | 8 segs | **8/8** | **Confirmed in PSEGT** | Billable premium segment |
| **CV** | 40 segs | **8/8** | **Confirmed in PSEGT** | Cash values |
| **A1** | 2 segs | **8/8** | **Confirmed in PSEGT** | Via `659 CEN II` |
| **G1** | 2 segs | **8/8** | **Confirmed in PSEGT** | Via `659 CEN II` |
| **LN** | 7 segs | **8/8** | **Confirmed in PSEGT** | Via `659 CEN II`, `L14` |
| **SR** | 2 segs | **8/8** | **Confirmed in PSEGT** | On `659 CEN II` only |
| **SL** | 2 segs | **8/8** | **Confirmed in PSEGT** | On `659 CEN II` only |
| **UF** | 1 seg | **8/8** | **Confirmed in PSEGT** | On `659 CEN II` only |
| **NC** | 5 segs | **8/8** | **Confirmed in PSEGT** | **Not QUIKCOI** (net premium credited) |
| **TP** | 11 segs | **8/8** | **Confirmed in PSEGT** | **Not QUIKISSC** (tax valuation) |
| **TX** | 11 segs | **8/8** | **Confirmed in PSEGT** | **Not QUIKISSC** (tax reserve) |
| **PR** | 103 segs | **8/8** | **Found but needs SME** | Linked via rider slots (`L14`, `1576 658/659`); **not QUIKGPS authority** |
| **U7** | 0 | 0/8 | **Not found** | Legacy surrender — absent |
| **U8** | 0 | 0/8 | **Not found** | Legacy surrender — absent |
| **U1, U2, U3** | 0 | 0/8 | **Not found** | Expense sub-types absent |
| **G2, G3, GF** | 0 | 0/8 | **Not found** | Guaranteed load segments absent |

---

## C. PDINT / PDINTTBL Interest Findings

**Relationship:** PDINT = rule header (`DINT_RULE`, date windows, multiplier); PDINTTBL = rate schedule detail (`DECLARED_RATE`, `START_DATE`, `END_DATE`, `IDX`).

**Hierarchy trace for interest:**

```text
PCOVRSGT (659 CEN II slot) → PSEGT (A1/G1/LN types) → PDINT (IDENT=CENII, TYPE=A1) → PDINTTBL (4.50% current)
```

| Link | Status |
|------|--------|
| PSEGT A1/G1/LN on all 8 ISWL coverages | **Proven** (via shared `659 CEN II` / `L14` slots) |
| PDINT IDENT → segment | **Partial** — `CENII` ↔ `659 CEN II` inferred; not all MPLANs named |
| PDINT G1/LN rows | **Sparse** — mostly A1/C1/C3 in extract |
| QUIKUINT buildable from extract alone | **No** — hierarchy proven; per-MPLAN credited/guaranteed/loan mapping needs SME |

**Key rate evidence:** `CENII` A1 declared **4.50%** from 2002-01-01 — matches PPBEN `FV_GUAR_RATE=4.50` on ISWL policies.

---

## D. ISWL Segment Trace Findings

**Chain used:**

```text
PCOMP (PRODUCT_ID = coverage) → PCOVR → PCOVRSGT → PSEGT → rate tables
```

**PPRDF:** Not in repo; no ISWL-named products in May PPRDF — top link still absent (non-blocking for segment trace).

### Authoritative mappings (hierarchy + rate evidence)

| QLA concept | PSEGT segment | Rate / data source | Hierarchy | Rate rows |
|-------------|---------------|-------------------|-----------|-----------|
| **Current COI (U6)** | `658 CEN I`, `659 CEN II` | PAAGERAT TYPE=U6 via SEGT_ID | **Proven** | 800 rows → parents **658 CEN SD**, **679 CEN SD** only |
| **Guaranteed COI (U5)** | `659 CEN II` | PAAGERAT TYPE=U5 | **Proven** | 200 rows → **679 CEN SD** only |
| **Gross premiums (BP)** | Multiple ISWL segs | PAAGERAT TYPE=BP | **Proven** | 1,164 rows → 4/8 parent coverages |
| **Cash values (CV)** | `658 CEN I`, `659 CEN II`, native CV | PDAGE + Rate_Table | **Proven** | 12,084 PDAGE + 72,271 Rate_Table ISWL CV |
| **Interest (A1/G1/LN)** | `659 CEN II`, `L14` | PDINT/PDINTTBL | **Proven slot**; **partial rate** | PDINT catalog only |
| **Surrender (SR/SL)** | `659 CEN II` | PSEGT confirmed; rate TBD | **Slot proven** | SL: 26 rows (PDAGE+RT); SR: 0 PAAGERAT |
| **Expenses (UF)** | `659 CEN II` | PSEGT confirmed | **Slot proven** | UF: 13 PDAGE rows; no PAAGERAT |
| **NC** | Multiple | PAAGERAT TYPE=NC | **Proven** — **not COI** | 690 rows (withdrawn as QUIKCOI) |

**Hub segment:** `659 CEN II` carries the full UL type dictionary for all eight ISWL coverages through shared PCOVRSGT slots.

---

## E. QLAdmin Output Readiness Matrix

| Output | Classification | Reason |
|--------|----------------|--------|
| **QUIKCVS** | **Implementation ready** (conditional) | PSEGT CV 8/8; PDAGE + Rate_Table rows 8/8; existing repo routing; **PDAGE vs Rate_Table parity still required** |
| **QUIKCOI** | **Strong evidence** | U6 hierarchy proven 8/8; PAAGERAT 800 rows; senior plans lack direct PAAGERAT on parent coverage |
| **QUIKGCOI** | **Strong evidence** | U5 hierarchy proven 8/8; PAAGERAT 200 rows on 679 CEN SD only |
| **QUIKGPS** | **Strong evidence** | BP hierarchy proven 8/8; PAAGERAT 1,164 rows on 4/8 parents; PR not authoritative per business rules |
| **QUIKUINT** | **Needs SME** | A1/G1/LN slots proven; PDINT CENII 4.50% supports guaranteed; **IDENT→MPLAN map and credited rate path incomplete** |
| **QUIKISSC** | **Blocked** | SR/SL PSEGT slots proven 8/8; **no PAAGERAT SR rows**; SL rows exist but rate pointer in SEGT_DATA not decoded; TP/TX withdrawn |
| **Expense setup** | **Needs client confirmation** | UF slot proven 8/8; U1–U3/G2/G3/GF absent from PSEGT; minimal UF rate rows |

---

## F. Changes to Prior Conclusions

| Topic | Old conclusion | New evidence | New conclusion | Reason |
|-------|----------------|--------------|----------------|--------|
| PSEGT availability | Missing — segment trace blocked | 696-row extract received | **Blocker removed** | File validates clean |
| U6/U5/BP mapping | Correlation only via TYPE_CODE | PSEGT + PCOVRSGT 8/8 | **Hierarchy confirmed** | Mandatory chain complete |
| PR for QUIKGPS | Zero ISWL PR rows (May/April research) | PAAGERAT 328 PR rows on `1576 658`/`1576 659` → SD/SR parents | **PR exists but not QUIKGPS source** | Rider/waiver segments; business rule: BP = billable premium |
| QUIKUINT | Blocked — no PDINT | PDINT + PDINTTBL received | **Partially unblocked** | Small catalog; SME map still needed |
| TP/TX → QUIKISSC | Withdrawn | PSEGT confirms TP/TX on ISWL slots | **Still withdrawn for QUIKISSC** | Product Book: tax valuation/reserve, not surrender |
| NC → QUIKCOI | Withdrawn | PSEGT confirms NC on ISWL | **Still withdrawn** | Net premium credited |

---

## G. Remaining Blockers / SME Questions

1. **PDINT IDENT → 8 MPLAN map** — which IDENT drives credited vs guaranteed vs loan for each coverage?
2. **QUIKISSC rate source** — decode `SEGT_DATA` for SR/SL on `659 CEN II`; confirm not TP/TX/SL TYPE_CODE alone.
3. **Senior plans** — `659 SR GD` / `669 SR GD`: sparse native PSEGT dictionary; zero PAAGERAT U6/BP on parent — alternate COI/GP source?
4. **QUIKCVS parity** — PDAGE (12,084 CV) vs Rate_Table (72,271 CV) row count mismatch — authoritative production path?
5. **Expense sub-types** — confirm U1/U2/U3/G2/G3/GF unused for ISWL (absent from PSEGT).
6. **PPRDF** — optional; confirm PCOMP-as-root is acceptable for ISWL hierarchy.

---

## H. Issue #31 Closure Recommendation

| Criterion | Met? |
|-----------|------|
| PSEGT contains required segment definitions | **Yes** — U5, U6, BP, CV, A1, G1, LN, SR, SL, UF confirmed 8/8 |
| PDINT/PDINTTBL contain declared interest data | **Partial** — yes for catalog IDENTs; not complete for all MPLANs |
| Segment-to-rate hierarchy traceable without missing links | **Partial** — PSEGT link complete; SR/SL rate pointer and senior-plan rates open |
| All QLA research can proceed without new source dependencies | **No** — QUIKISSC rate decode; optional PDAGE refresh for CV parity |

### Recommendation

**Close Issue #31 as: `Partially Resolved — Source Dependency Closed`**

- The **primary source dependency** (PSEGT, PDINT, PDINTTBL) is **satisfied**.
- Do **not** close as **Fully Resolved** or **Implementation Complete**.
- Open follow-on: Implementation Planning (QUIKCVS → COI/GCOI/GPS → UINT) + SME Review.

---

## I. Next Recommended Task

**Implementation Planning Agent — QUIKCVS first**

1. Run PDAGE vs Rate_Table CV parity analysis (May PDAGE vs April Rate_Table).
2. Document authoritative CV extract for production loader.
3. Parallel **SME Review Agent** for PDINT IDENT map and QUIKISSC SR/SL rate pointer.

No converter, loader, catalog, or rulebook changes until plan is approved.

---

*Machine evidence: `docs/research/ISWL_Segment_Trace/iswl_segment_trace_bundle_20260629.json`, `ISWL_Segment_Trace_Matrix_20260629.csv`*
