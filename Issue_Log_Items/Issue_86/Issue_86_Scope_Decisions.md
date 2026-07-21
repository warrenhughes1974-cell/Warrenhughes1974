# Issue #86 — Scope Decisions & Decisions Needed

**Opened:** 2026-07-19  
**Decisions locked:** 2026-07-19 — user confirmed D1-A / D2-A / D3-A (“Yes those are correct”).  
**Model:** Cursor Grok 4.5 (locked)  
**Code changes:** None  
**Status:** D1–D3 locked — Ready for Risk Review  

---

## DECISIONS — LOCKED 2026-07-19

| # | Decision | Locked choice |
|---|----------|---------------|
| **D1** | PROCDATE | **D1-A** — prior month-end (same as other dates) |
| **D2** | Historically blank date columns (e.g. CPNBILL) | **D2-A** — force prior month-end |
| **D3** | VERSION / UPDATENUM | **D3-A** — hard defaults `5.318` / `359` from screenshot |

**Config placement (clarified):** Not `Master_Crosswalk.csv`. Crosswalk is LifePRO↔QLAdmin plan/product mapping. QuikDate has no LifePRO source — defaults live in the QuikDate emit path (`qla_core/quikdate_converter.py`), optionally backed by a small `QLA_Migration/Configs/` defaults file if Development prefers config-over-code. Same pattern as DG-R-003 / other system-control rebuilds; not crosswalk rows.

---

## Locked scope boundaries

| ID | Decision |
|----|----------|
| **SD-86-1** | QuikDate is a **total rebuild** single-row emit (like other system-control rebuilds). Do **not** copy stale values from region DBF or LifePRO. |
| **SD-86-2** | Schema field **names/order** stay as verified in `data_governance/docs/QuikDate_Schema_Verification.md` / live `QUIKDATE.DBF`. |
| **SD-86-3** | **Date fields** use Governance prior-month-end of conversion run date (`prior_month_end`). `ESC_DATE` remains **blank**. |
| **SD-86-4** | **Non-date fields** default to screenshot values (PDUEDAYS / VERSION / UPDATENUM / ACH*). |
| **SD-86-5** | No LifePRO source extract. No MPOLICY / #25 / #26 impact. |
| **SD-86-6** | No production code until G1+G2+G3 and explicit Development approval. |
| **SD-86-7** | Defaults are **not** Master_Crosswalk entries; they are QuikDate emit/config defaults. |

---

## Recommended field matrix (Planning default)

Controlling date = conversion run date (default `date.today()`).  
Prior month end example for run date **2026-07-19** → **2026-06-30** (`20260630` in CSV).

| Field | Type | Proposed emit | Basis |
|-------|------|---------------|-------|
| PROCDATE | D | Prior month end | Data_Goverence “set all dates”; **D1** |
| ESC_DATE | D | Blank | DG-QUIKDATE-006 / screenshot |
| ANNDATE | D | Prior month end | All-dates rule |
| DIRBILL | D | Prior month end | DG-QUIKDATE-002 |
| PDUEDAYS | N | `31` | Screenshot |
| PACBILL | D | Prior month end | DG-QUIKDATE-001 |
| GRPBILL | D | Prior month end | All-dates rule |
| APLBILL | D | Prior month end | All-dates rule |
| LOANBILL | D | Prior month end | All-dates rule |
| REINBILL | D | Prior month end | DG-QUIKDATE-003 |
| CPNBILL | D | Prior month end | All-dates rule (was blank in region; **D2**) |
| VERSION | C | `5.318` | Screenshot |
| UPDATENUM | N | `359` | Screenshot |
| CCBILL | D | Prior month end | All-dates rule |
| ACHFILEID | N | `0` | DG-QUIKDATE-004 / screenshot |
| ACHFILEID2 | C | `A` | DG-QUIKDATE-005 / screenshot |

---

## Decisions needed (non-blocking for Risk with defaults)

### D1 — PROCDATE

| Option | Plain English |
|--------|---------------|
| **D1-A (recommended)** | PROCDATE = prior month end (same as other dates) |
| **D1-B** | PROCDATE = conversion run date (matches current region screenshot 07/19/2026) |

**Needed before Development:** Confirm D1-A or D1-B.

### D2 — Formerly blank date columns (CPNBILL; historically empty REINBILL)

| Option | Plain English |
|--------|---------------|
| **D2-A (recommended)** | Force prior month end (Data_Goverence “set all dates”) |
| **D2-B** | Leave blank if region historically blank |

**Needed before Development:** Confirm D2-A or D2-B.

### D3 — VERSION / UPDATENUM constants

| Option | Plain English |
|--------|---------------|
| **D3-A (recommended)** | Hard-code screenshot values `5.318` / `359` |
| **D3-B** | Leave blank (current partial emit behavior) |

**Needed before Development:** Confirm D3-A (strongly recommended — matches “default what you see on the screenshot”).

---

## Standing guards

- Do not invent LifePRO→QuikDate mapping  
- Do not alter unrelated converters / rulebooks  
- Preserve #25 MPOLICY padding and #26 MPREM  
- Audits under `QLA_Migration/Reports/` if needed; Output root = table CSV only  
