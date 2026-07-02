# Issue #33 — QUIKISSC SME Follow-Up Answers (Conversion Lead)

**Issue:** #33 — ISWL Phase 6 QUIKISSC  
**Date:** 2026-06-30  
**Mode:** Research and documentation only — no code changes  
**Audience:** Conversion Lead / SME review

---

## A. What OSLNS00XT / SLD000 Are

### Where they appear

| Token | Appears in | Count |
|-------|------------|------:|
| `OSLNS00XT` | `PSEGT` hex payloads only (`SEGT_DATA`, `ROW_COLUMN`) | 4 field hits (2 segments × 2 fields) |
| `SLD000` | Same PSEGT payloads | Same |

**Not found** in: `Rate_Table`, `PDAGE`, `PCOVRSGT`, `PCOVR`, or any other repo extract as plain text.

### Byte-level decode (659 CEN II / SL)

```
Offset 0x00: 659 CEN IISLD000     ← segment key + schedule variant code
Offset 0x20: 0C OSLNS00XT         ← 0x0C = length 12; fixed-width identifier token
Offset 0x40+: PN.I ... F ... NN   ← additional LifePRO control flags (not decoded to table names)
SEGT_KEY0:   659 CEN IISL
```

Same `OSLNS00XT` token appears on **`668 SPWL` / SL** as well.

### Classification

| Token | What it is | What it is NOT |
|-------|------------|----------------|
| **SLD000** | Segment-local **schedule variant code** embedded in the SL segment payload (suffix of segment identity `…ISL` + `D000`) | Not a CSV table name in repo |
| **OSLNS00XT** | **Internal LifePRO rate-structure identifier** in PSEGT `SEGT_DATA` (12-char token with length prefix) | Not a row in Rate_Table; not a file in repo |

These are **PSEGT segment payload tokens / internal pointers**, not standalone rate-table names.

### Why this supports Rate_Table TYPE_CODE=SL (hierarchy proof)

1. **Segment gate:** ISWL coverages resolve to `PSEGT(SEGMENT_ID=659 CEN II, SEGT_TYPE=SL)`.
2. **Payload gate:** That PSEGT row carries `OSLNS00XT` + `SLD000` — the runtime pointer context for the load schedule.
3. **Schedule gate:** The only **non-zero** duration-indexed schedule in repo for that segment is **`Rate_Table` where `COVERAGE_ID=659 CEN II` and `TYPE_CODE=SL`** (14 rows, durations 1–14).
4. **Rejection gate:** `PDAGE TYPE_CODE=SL` rows for the same segment exist but all values are **0.0** — not authoritative.
5. **Disambiguation proof:** `659 CEN II` and `668 SPWL` share the **same** `OSLNS00XT` token but have **different** Rate_Table SL schedules (14 vs 10 durations). Therefore the runtime join is **`PSEGT.SEGMENT_ID + TYPE_CODE=SL`**, not the token string alone.

**Conclusion:** `OSLNS00XT`/`SLD000` identify the SL segment's rate-structure context; the authoritative schedule rows are in **Rate_Table TYPE_CODE=SL** keyed by **`COVERAGE_ID = PSEGT.SEGMENT_ID`**.

---

## B. Why 659 CEN II Applies to All 8 MPLANs

### Hub pattern (not one-plan-native)

`659 CEN II` is a **shared LifePRO hub segment** — a segment dictionary reused across multiple ISWL coverages via PCOVRSGT slot inheritance. This is the same hub pattern used for QUIKUINT (A1/G1/LN), QUIKCOI (U6), and QUIKGPS (BP).

### PCOVRSGT → PSEGT proof (all 8 ISWL coverages)

| Coverage ID | MPLAN | Active PCOVRSGT slots | Hub `659 CEN II` slots | SR via hub | SL via hub | Native SR/SL on own segment |
|-------------|-------|----------------------:|-----------------------:|:----------:|:----------:|----------------------------|
| 658 CEN I | 1658C1 | 24 | 8 | Yes | Yes | No |
| 658 CEN SD | 1658CS | 24 | 8 | Yes | Yes | No |
| 659 CEN II | 1659C2 | 24 | 17 | Yes | Yes | **Yes** (hub is native here) |
| 659 CEN SR | 1659CR | 24 | 15 | Yes | Yes | No |
| 659 CEN SD | 1659CS | 24 | 15 | Yes | Yes | No |
| 659 SR GD | 1659SR | 24 | 14 | Yes | Yes | No |
| 669 SR GD | 1669SR | 24 | 14 | Yes | Yes | No |
| 679 CEN SD | 1679CS | 23 | 7 | Yes | Yes | No |

**Missing SL via hub:** none (8/8).

### Hierarchy chain (per MPLAN)

```text
PCOVR (coverage) → PCOVRSGT (SEGT_FLAG=Y, SEGT_ID=659 CEN II)
  → PSEGT (659 CEN II, SEGT_TYPE=SR)  [parent]
  → PSEGT (659 CEN II, SEGT_TYPE=SL)  [child — schedule holder]
  → Rate_Table (COVERAGE_ID=659 CEN II, TYPE_CODE=SL)
  → Crosswalk → PLAN (each MPLAN)
  → QuikIssc
```

Senior/grandfathered plans (`659 SR GD`, `669 SR GD`) do **not** define their own SL segment dictionary; they inherit the hub through PCOVRSGT slots.

### Replication decision

Because all 8 MPLANs resolve to the **same hub SL schedule**, PR-6 emits **one QuikIssc row per MPLAN** using the shared `659 CEN II` Rate_Table SL values — **8 rows total**.

---

## C. UWCLASS Source Value Analysis

### Source values (ISWL, relevant extracts)

| Extract | Context | UW values found |
|---------|---------|-----------------|
| Rate_Table SL (`659 CEN II`) | Surrender schedule | **`S` only** |
| Rate_Table (all ISWL rows) | Broader inventory | `P` (67,571 rows), `S` (184,379 rows) |
| PAAGERAT (ISWL) | COI/GPS streams | `P`, `S` (column populated) |

### Established QLAdmin crosswalk (PR-1–PR-4)

From `qla_core/rate_dbf_schema.py` — **business-confirmed**:

| LifePRO source | QLAdmin UWCLASS | Label |
|----------------|-----------------|-------|
| `S` | **`SM`** | SMOKER |
| `P` | `PR` | PREFERRED |
| `N` | `NS` | NON-SMOKER |
| `0` | `00` | NOT APPLICABLE |
| `B` | `ST` | STANDARD |

Used by `rate_factor_loader.transform_source()` → `map_uwclass()` for QuikCvs, QuikGps, QuikCoi, QuikGcoi (PR-1–PR-4).

### QUIKISSC mapping (research conclusion)

| LifePRO | QLAdmin | Basis |
|---------|---------|-------|
| `UNDERWRITING_CLASS=S` on Rate_Table SL | **`UWCLASS=SM`** | Established repo crosswalk; only UW value on SL schedule |

**Classification:** **ESTABLISHED IN REPO** — not a guess. SME should **confirm** (not invent) that the same crosswalk applies to QuikIssc.

---

## D. QLAdmin QuikIssc Field / Percent Format Analysis

### Target fields (Help §7.144)

**Table:** `QuikIssc` — ISWL Surrender Charges  
**Index:** `PLAN + GENDER + UWCLASS + BAND + ISSCNTRY + ISSUEST`

| Field | Type | Length | Decimals | Description |
|-------|------|-------:|---------:|-------------|
| PLAN | CHARACTER | 6 | — | Plan code |
| AGE | NUMERIC | 3 | — | Attained age |
| GENDER | CHARACTER | 1 | — | M, F, J, U |
| UWCLASS | CHARACTER | 2 | — | Underwriting class |
| BAND | CHARACTER | 2 | — | Insurance band |
| ISSCNTRY | CHARACTER | 4 | — | Issue country |
| ISSUEST | CHARACTER | 2 | — | Issue state |
| **SCHG01–SCHG20** | **NUMERIC** | **8** | **4** | **Surrender charge duration 1–20** |

Surrender charge values are stored in **`SCHG01` through `SCHG20`** — not in a separate rate column.

### Percent literal vs decimal

| Evidence | Finding |
|----------|---------|
| QLAdmin Help §7.144 | Describes fields as "Surrender charge duration N" — **no numeric examples** in Help |
| LifePRO source (`Rate_Table SL`) | Values `100.0000000`, `70.0000000`, … `2.0000000` — canonical **percent ladder** |
| QUIKUINT precedent (PR-5, Help §7.223) | N(8.4) percent literals (`4.5000` = 4.5%) |
| Decimal interpretation test | `1.0000` would imply 1% at duration 1 — contradicts source `100.0000000` |

**Conclusion:** Emit **`100.0000` = 100%** (percent literal in N(8.4)), not `1.0000`.

---

## E. SME Answers Received (partial)

| Gate | Question | SME answer | Status |
|------|----------|------------|--------|
| **C** | AGE=0 single all-age row? | **Yes** — no age expansion | **CLOSED** |
| **E** | SCHG15–20 blank? | **Yes** — source has durations 1–14 only | **CLOSED** |

---

## F. Remaining Gates

| Gate | Topic | Research status | SME status |
|------|-------|-----------------|------------|
| **A** | OSLNS00XT/SLD000 → Rate_Table SL | **STRONG EVIDENCE** (this document §A) | Awaiting APPROVE |
| **B** | Replicate hub to 8 MPLANs | **STRONG EVIDENCE** (this document §B) | Awaiting APPROVE |
| **C** | AGE=0 all-age row | Confirmed | **CLOSED** |
| **D** | UWCLASS S → SM | **ESTABLISHED IN REPO** (§C) | Awaiting confirm |
| **E** | SCHG15–20 blank | Confirmed | **CLOSED** |
| **F** | Percent literal format | **STRONG EVIDENCE** (§D) | Awaiting APPROVE |

---

## G. Recommendation

**READY AFTER SME CONFIRMATION**

Gates C and E are closed. Research resolves A, B, D, and F with source evidence. SME needs only to **approve or correct** four items (A, B, D confirm, F) — no open technical discovery remains.

Upon approval: update `Issue_33_QUIKISSC_SME_Answers.md` to **READY FOR DEVELOPMENT** and route to Development Agent (PR-6).
