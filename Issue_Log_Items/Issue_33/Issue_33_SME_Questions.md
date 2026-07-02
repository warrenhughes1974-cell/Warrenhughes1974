# Issue #33 — QUIKISSC SME Questions

**Issue:** #33 — ISWL Phase 6 QUIKISSC  
**Date:** 2026-06-28  
**Status:** **OPEN** — gates must close before development  
**Authority:** Product Book addendum, PSEGT 20260629 extract, QLAdmin Help §7.144

---

## Gate summary

| Gate | Topic | Status |
|------|-------|--------|
| G1 | Segment path SR → SL vs U7/U8 | **OPEN** (strong evidence for SR/SL) |
| G2 | Rate table pointer from PSEGT SL payload | **OPEN** |
| G3 | Rate_Table SL as authoritative schedule | **OPEN** |
| G4 | Percent format (100.0 vs 1.0) | **OPEN** |
| G5 | Dimensional scope (gender / UW / age / band) | **OPEN** |
| G6 | Shared schedule across 8 MPLANs | **OPEN** |
| G7 | QuikIssc schema / SCHG15–20 handling | **OPEN** (schema found; semantics TBD) |
| G8 | TP/TX exclusion | **CLOSED** (tax only — do not use) |

---

## Priority 1 — Blocking development

### Q1. Segment authority path

For CSO ISWL, is surrender charge setup **`PCOVRSGT → PSEGT(SR) → PSEGT(SL)`** on hub **`659 CEN II`**, or legacy **U7/U8**?

**Research finding:** SR/SL **8/8** on all ISWL coverages via hub; U7/U8 **0/8**.

**Needed:** SME confirmation that SR/SL is authoritative for all 8 MPLANs.

---

### Q2. Rate source location

PSEGT SL payload on `659 CEN II` embeds **`OSLNS00XT`** and **`SLD000`**. Which LifePRO structure holds the surrender charge schedule?

**Candidates:**

| Source | Hub evidence | Status |
|--------|--------------|--------|
| Rate_Table TYPE_CODE=**SL** | 14 rows, duration 1–14, M/S/Band1 | CORRELATION ONLY |
| PDAGE TYPE_CODE=**SL** | 12 rows, all zero values | Unlikely authoritative |
| Segment constant in SEGT_DATA | Partial decode | NEEDS SME |
| Other (PRBEN*, table name OSLNS00XT) | Not extracted | UNKNOWN |

**Needed:** Definitive rate table name and join key from SL segment pointer.

---

### Q3. SR → SL parent/child wiring

Product Book requires tracing **SR parent → SL child**. PSEGT SR payload references `659 CEN II` with Y/N flags.

**Needed:** Which PCOVRSGT slot numbers map to SR vs SL? Is SL always reached through SR for ISWL?

---

### Q4. Percent literal format

Rate_Table SL VALUES for hub are **100.0000, 70.0000, … 2.0000** (duration-indexed).

**Needed:** For QuikIssc **SCHG01–SCHG14**, emit as:

- **Percent literals** (`100.0000` = 100% charge), or  
- **Decimal fractions** (`1.0000` = 100%)?

(Mirror QUIKUINT N(8.4) percent literal convention if applicable.)

---

### Q5. Dimensional scope for emit

Hub Rate_Table SL rows exist for **Male / UWCLASS S / Band 1 / AGE 0** only.

**Needed:**

1. Emit **Male-only** row per MPLAN, or expand to Female / Non-smoker?  
2. Does **AGE=0** mean “not age-rated” (single row per PLAN key)?  
3. Default **ISSCNTRY=0000 / ISSUEST=00** acceptable for all 8 MPLANs?

---

### Q6. Shared schedule across MPLANs

All 8 ISWL coverages inherit SR/SL from hub **`659 CEN II`** (same pattern as QUIKUINT CENII/A1).

**Needed:** Confirm **one surrender schedule replicated to all 8 MPLANs**, or per-MPLAN variation exists (especially **659 SR GD / 669 SR GD** senior plans).

---

## Priority 2 — Validation and reconciliation

### Q7. TP/TX exclusion

Confirm **TP = Tax Valuation Premiums** and **TX = Tax Reserve Factors** are **never** surrender charge sources for ISWL.

**Research finding:** Product Book + segment trace — **withdrawn** from QUIKISSC candidates.

**Status:** Awaiting formal SME ack (expected **CLOSED**).

---

### Q8. Policy-level validation

Which policy fields should reconciliation use?

- `PPBENTYP.BF_CURR_SURR_LOAD`  
- `PPRBNUL.SURR_LOAD` / `LAPSE_SURR_LOAD`  
- `PFNDD.SURRENDER_LOAD`

**Needed:** Preferred validation field(s) and sample policies for UAT.

---

### Q9. SCHG15–SCHG20

Rate source has **14 durations**; QuikIssc defines **SCHG01–SCHG20**.

**Needed:** Leave SCHG15–SCHG20 blank/zero, or extend schedule beyond year 14?

---

### Q10. Relationship to QuikCvs / QuikIswl

**Needed:** Confirm business rule: surrender charge applies to fund value with CV floor per master reference — any QuikPlan variation flags required for ISWL?

---

## Priority 3 — Reference materials

### Q11. Reference DBFs

Can actuarial provide **reference QuikIssc.dbf** (or CSV export) for one ISWL MPLAN showing expected row count and SCHG values?

---

### Q12. PDAGE vs Rate_Table authority

For surrender (once segment path proven), is **Rate_Table** or **PDAGE** production-authoritative? (PDAGE SL rows are all zero on hub.)

---

## Submission checklist (SME response log)

When gates close, create `Issue_33_QUIKISSC_SME_Answers.md` mirroring Issue #32 pattern with:

- Dated decisions per gate  
- Source validation evidence  
- Approved transform statement  
- Expected row count  
- Readiness upgrade to **READY FOR DEVELOPMENT**
