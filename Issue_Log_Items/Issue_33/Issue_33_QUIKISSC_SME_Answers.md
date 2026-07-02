# Issue #33 — QUIKISSC SME Answer Log

**Issue:** #33 — ISWL Phase 6 QUIKISSC (Surrender Charges)  
**Date:** 2026-06-30 (updated — SME follow-up research)  
**Mode:** Documentation only — no code changes  
**Status:** **READY AFTER SME CONFIRMATION** — Gates C/E closed; Gates A/B/D/F research-resolved  
**Basis:** [`Issue_33_Forensic_Pointer_Resolution.md`](Issue_33_Forensic_Pointer_Resolution.md), [`Issue_33_QUIKISSC_SME_Followup_Answers.md`](Issue_33_QUIKISSC_SME_Followup_Answers.md)

---

## SME gate closure summary

| Gate | Question | Answer / research | Status |
|------|----------|-------------------|--------|
| **A** | OSLNS00XT/SLD000 → Rate_Table SL | Payload tokens; schedule = Rate_Table `TYPE_CODE=SL` by `SEGMENT_ID` | **OPEN** — strong evidence; awaiting APPROVE |
| **B** | Replicate hub schedule to 8 MPLANs | All 8 coverages inherit `659 CEN II` SL via PCOVRSGT (8/8) | **OPEN** — strong evidence; awaiting APPROVE |
| **C** | AGE=0 single all-age row | **Yes** — no age expansion | **CLOSED** |
| **D** | UWCLASS S → QLAdmin code | **`SM`** per established `UWCLASS_MAP` (PR-1–PR-4) | **OPEN** — established in repo; awaiting confirm |
| **E** | SCHG15–20 blank | **Yes** — blank; source durations 1–14 only | **CLOSED** |
| **F** | Percent literal format | **`100.0000` = 100%** (N(8.4) percent literal) | **OPEN** — strong evidence; awaiting APPROVE |
| — | TP/TX excluded | Tax data only | **CLOSED** |
| — | U7/U8 absent | 0/8 | **CLOSED** |
| — | QuikIssc schema §7.144 | Confirmed | **CLOSED** |
| — | PDAGE SL rejected | All zero | **CLOSED** |

---

## 1. SME answers (received)

### Gate C — AGE=0 all-age row — **CLOSED**

**Question:** Does AGE=0 represent a single all-age QuikIssc row with no age-specific expansion?

**Answer:** **Yes.**

**Decision:** Emit **one QuikIssc row per MPLAN** with `AGE=0`. Do not expand by attained age.

---

### Gate E — SCHG15–SCHG20 — **CLOSED**

**Question:** Should SCHG15–SCHG20 be blank because source only has durations 1–14?

**Answer:** **Yes.**

**Decision:** Populate `SCHG01`–`SCHG14` from durations 1–14; emit `SCHG15`–`SCHG20` **blank** at CSV level (no carry-forward, no synthetic zero).

---

## 2. Research-resolved items (awaiting SME approve/confirm)

Full evidence: [`Issue_33_QUIKISSC_SME_Followup_Answers.md`](Issue_33_QUIKISSC_SME_Followup_Answers.md)

### Gate A — OSLNS00XT / SLD000 — awaiting APPROVE

**What they are:**

| Token | Classification |
|-------|----------------|
| **SLD000** | Segment-local schedule variant code in PSEGT SL `SEGT_DATA` (suffix of `…ISL` identity) |
| **OSLNS00XT** | 12-character internal LifePRO rate-structure identifier in PSEGT payload (length-prefixed at byte offset 0x20) |

**Not** physical table names in repo extracts. Appear **only** in PSEGT hex payloads (4 field occurrences across `659 CEN II` and `668 SPWL` SL rows).

**Why Rate_Table TYPE_CODE=SL:**

1. PSEGT SL segment carries pointer tokens.
2. Only non-zero schedule: `Rate_Table` where `COVERAGE_ID = PSEGT.SEGMENT_ID` and `TYPE_CODE=SL`.
3. PDAGE SL rejected (all zeros).
4. Same `OSLNS00XT` on `668 SPWL` but different schedule → join is **segment ID + TYPE_CODE**, not token alone.

**SME:** ☐ APPROVE  ☐ CORRECT: ____________________

---

### Gate B — Shared 659 CEN II hub — awaiting APPROVE

**Why hub applies to all 8 MPLANs:**

All 8 ISWL coverages have active PCOVRSGT slots pointing to `659 CEN II`. PSEGT confirms SR/SL on that hub segment. Senior plans inherit the hub — they do not define native SL segments.

| Coverage | MPLAN | Hub slots | SL via hub |
|----------|-------|----------:|:----------:|
| 658 CEN I | 1658C1 | 8 | Yes |
| 658 CEN SD | 1658CS | 8 | Yes |
| 659 CEN II | 1659C2 | 17 | Yes |
| 659 CEN SR | 1659CR | 15 | Yes |
| 659 CEN SD | 1659CS | 15 | Yes |
| 659 SR GD | 1659SR | 14 | Yes |
| 669 SR GD | 1669SR | 14 | Yes |
| 679 CEN SD | 1679CS | 7 | Yes |

**Missing SL via hub:** none.

**Decision:** Replicate hub `659 CEN II` Rate_Table SL schedule to all 8 MPLANs → **8 QuikIssc rows**.

**SME:** ☐ APPROVE  ☐ CORRECT: ____________________

---

### Gate D — UWCLASS mapping — awaiting CONFIRM

**Source:** Rate_Table SL (`659 CEN II`) uses **`UNDERWRITING_CLASS=S` only**.

**Established crosswalk** (`qla_core/rate_dbf_schema.py`, used PR-1–PR-4):

| LifePRO | QLAdmin | Label |
|---------|---------|-------|
| `S` | **`SM`** | SMOKER |
| `P` | `PR` | PREFERRED |

**Decision:** Map source `S` → **`UWCLASS=SM`** on QuikIssc (same crosswalk as QuikCvs/QuikGps/QuikCoi/QuikGcoi).

**SME:** ☐ CONFIRM SM  ☐ CORRECT (target): ____________________

---

### Gate F — Percent format — awaiting APPROVE

**Target fields:** `SCHG01`–`SCHG20` — NUMERIC(8.4) per Help §7.144.

**Source values:** `100.0000000`, `70.0000000`, … `2.0000000` (percent ladder).

**Decision:** Emit percent literals — **`100.0000` = 100%** — not decimal `1.0000`. Consistent with QUIKUINT N(8.4) convention.

**SME:** ☐ APPROVE  ☐ CORRECT: ____________________

---

## 3. Final authoritative mapping (pending Gates A/B/D/F sign-off)

| QuikIssc field | LifePRO source | Transform | Gate |
|----------------|----------------|-----------|------|
| PLAN | Crosswalk | Each of 8 ISWL MPLANs | B |
| AGE | Rate_Table.AGE | `0` | **C — CLOSED** |
| GENDER | Rate_Table.SEX | `M` | — |
| UWCLASS | Rate_Table.UNDERWRITING_CLASS | `S` → **`SM`** | D |
| BAND | Rate_Table.BAND | `1` → `01` | — |
| ISSCNTRY | Default | `0000` | — |
| ISSUEST | Default | `00` | — |
| SCHG01–SCHG14 | Rate_Table SL VALUE @ DURATION 1–14 | Percent literal N(8.4) | F |
| SCHG15–SCHG20 | — | **Blank** | **E — CLOSED** |

**Hub SL schedule anchor (`659 CEN II` / M / SM / Band 01):**

| Duration | SCHG | Value |
|----------|------|------:|
| 1 | SCHG01 | 100.0000 |
| 2 | SCHG02 | 100.0000 |
| 3 | SCHG03 | 70.0000 |
| 4 | SCHG04 | 60.0000 |
| 5 | SCHG05 | 50.0000 |
| 6 | SCHG06 | 40.0000 |
| 7 | SCHG07 | 30.0000 |
| 8 | SCHG08 | 20.0000 |
| 9 | SCHG09 | 15.0000 |
| 10 | SCHG10 | 10.0000 |
| 11 | SCHG11 | 8.0000 |
| 12 | SCHG12 | 6.0000 |
| 13 | SCHG13 | 4.0000 |
| 14 | SCHG14 | 2.0000 |
| 15–20 | SCHG15–20 | (blank) |

---

## 4. Expected output

| Metric | Value |
|--------|------:|
| ISWL MPLANs | 8 |
| Rows per MPLAN | 1 |
| **Total QuikIssc rows** | **8** |
| SCHG populated | SCHG01–14 |
| SCHG blank | SCHG15–20 |

---

## 5. Readiness

**Recommendation:** **READY AFTER SME CONFIRMATION**

Gates **C** and **E** are **CLOSED**. Gates **A**, **B**, **D**, and **F** are research-resolved with source evidence — awaiting SME approve/confirm only.

Upon closure of A/B/D/F: status → **READY FOR DEVELOPMENT**; route to Development Agent via [`ISWL_QUIKISSC_Next_Stage_Prompt.md`](../../docs/research/ISWL_Implementation/ISWL_QUIKISSC_Next_Stage_Prompt.md).

---

## Sign-off

| Role | Name | Decision | Date |
|------|------|----------|------|
| SME / Actuarial | __________ | ☐ Approve A/B/D/F  ☐ Corrections noted | __________ |
| Conversion Lead | __________ | ☐ Acknowledged | __________ |
