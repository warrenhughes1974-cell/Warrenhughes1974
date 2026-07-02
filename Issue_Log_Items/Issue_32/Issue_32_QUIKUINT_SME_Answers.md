# Issue #32 — QUIKUINT SME Answer Log

**Issue:** #32 — ISWL Phase 5 QUIKUINT  
**Date:** 2026-06-30 (SME gate closure)  
**Mode:** Documentation only — no code changes  
**Status:** **All SME gates CLOSED** — **READY FOR DEVELOPMENT**

---

## SME gate closure summary

| Gate | Question | SME answer | Status |
|------|----------|------------|--------|
| **1** | MGTDRATE when no PDINT G1 rows | Mirror current declared A1 interest | **CLOSED** |
| **2** | Current tier only vs full history | Load all historical effective dates when available; else current rate | **CLOSED** |
| **3** | CENII IDENT for all 8 ISWL MPLANs | **YES** — use CENII for all eight | **CLOSED** |
| Schema | QuikUint 4-field layout | QLAdmin Help §7.223 | **CLOSED** (prior) |
| Loan | Loan on QuikUint? | No — separate QuikPlan/QuikPlSt track | **CLOSED** (prior) |

---

## 1. SME answers (final)

### Gate 1 — Guaranteed interest (MGTDRATE) — **CLOSED**

**Question:** Since there are no PDINT TYPE=G1 rows, should MGTDRATE mirror the current declared interest A1, or is there another source?

**Answer:** MGTDRATE should mirror the current declared interest.

**Decision:** **`MGTDRATE = MCURRATE`** from CENII / A1 / PDINTTBL `DECLARED_RATE` on each emitted tier.

---

### Gate 2 — Effective dates / emit scope — **CLOSED**

**Question:** Should QuikUint include only the current active interest rate for each plan, or should all historical effective dates be converted?

**Answer:** Load all historical effective dates if available. If historical rates are not available, load the current rate.

**Decision:**

- Emit **all PDINTTBL historical tiers** for CENII / TYPE=A1 when available.
- **MEFFDATE** = `PDINTTBL.START_DATE` for each tier.
- **Fallback:** If no historical tiers exist for an MPLAN, emit **one current-tier row** only.

---

### Gate 3 — PDINT identifier — **CLOSED**

**Question:** Can you confirm CENII is the correct PDINT IDENT to use for all eight ISWL MPLANs?

**Answer:** **YES.**

**Decision:** **`PDINT IDENT = CENII`** for all eight ISWL MPLANs:

`1658C1`, `1658CS`, `1659C2`, `1659CR`, `1659CS`, `1659SR`, `1669SR`, `1679CS`

---

### 1.1 QLAdmin QuikUint schema — **CONFIRMED**

| Field | Type | Len | Authority |
|-------|------|-----|-----------|
| MPLAN | C | 6 | QLAdmin Help §7.223 |
| MEFFDATE | D | 8 | QLAdmin Help §7.223 |
| MGTDRATE | N | 8.4 | Guaranteed initial interest rate |
| MCURRATE | N | 8.4 | Current interest rate |

**Index:** `MPLAN + DTOS(MEFFDATE)` on `QuikUint.ntx`

---

### 1.2 Loan interest — **CONFIRMED**

Loan interest is **not** emitted to QuikUint. Route to `quikplan.LOANINT` / `QuikPlSt.MLOANINT` (separate Issue #32 track).

---

### 1.3 Current interest (A1 → MCURRATE) — **CONFIRMED**

**Hierarchy:** `PCOVRSGT → PSEGT(A1) → PDINT(CENII, TYPE=A1) → PDINTTBL → MCURRATE`

---

## 2. Final authoritative mapping

| QUIKUINT field | LifePRO source | Transform |
|----------------|----------------|-----------|
| **MPLAN** | Crosswalk | All **8 ISWL MPLANs** |
| **MEFFDATE** | PDINTTBL | **START_DATE** of each historical tier |
| **MCURRATE** | PDINTTBL | **DECLARED_RATE** from CENII / A1 |
| **MGTDRATE** | PDINTTBL | **Same value as MCURRATE** on each tier |
| *(loan)* | — | **Not QuikUint** — QuikPlan / QuikPlSt |

**Rate format:** Percent literal N(8.4) — `4.50000` = 4.5% (no divide-by-100).

---

## 3. Expected output (SME-approved)

**Formula:** `8 MPLANs × number of CENII/A1 historical tiers per MPLAN`

CENII / A1 PDINTTBL source contains **6 schedule rows** (DINT_RULE 0 × 3 tiers + DINT_RULE 3 × 3 tiers):

| DINT_RULE | START_DATE | END_DATE | DECLARED_RATE |
|-----------|------------|----------|---------------|
| 0 | 19800101 | 19981231 | 7.00000 |
| 0 | 19990101 | 20011231 | 5.00000 |
| 0 | 20020101 | 20991231 | 4.50000 |
| 3 | 19800101 | 19881231 | 11.00000 |
| 3 | 19890101 | 20011231 | 9.00000 |
| 3 | 20020101 | 20991231 | 4.50000 |

| Scenario | Expected QuikUint rows |
|----------|------------------------:|
| Full history (6 tiers × 8 MPLANs) | **~48** |
| Fallback — current tier only (1 × 8) | **8** |

**PR-5 implementation (revised after historical tier validation):** Use **union merge** — collect all unique `START_DATE` tiers from **both** DINT_RULE 0 and DINT_RULE 3. **Do not filter to Rule 3 only** (that drops Rule 0 tier at 19990101 @ 5%). See [`Issue_32_QUIKUINT_Historical_Tier_Validation.md`](Issue_32_QUIKUINT_Historical_Tier_Validation.md).

| Scenario | Expected QuikUint rows |
|----------|------------------------:|
| **Union merge (PR-5 default)** | **32** (8 × 4 unique START_DATEs) |
| Fallback — current tier only | **8** |

**Union schedule per MPLAN:**

| MEFFDATE | MCURRATE / MGTDRATE | Source rule |
|----------|--------------------:|-------------|
| 19800101 | 11.00000 | Rule 3 (tie-break at collision) |
| 19890101 | 9.00000 | Rule 3 |
| 19990101 | 5.00000 | Rule 0 |
| 20020101 | 4.50000 | Both (identical) |

---

## 4. Blocker classification (final)

| Item | Status |
|------|--------|
| QuikUint schema | **CONFIRMED** |
| Loan not on QuikUint | **CONFIRMED** |
| MGTDRATE mirrors MCURRATE | **CONFIRMED** |
| CENII for all 8 MPLANs | **CONFIRMED** |
| Full historical tier emit | **CONFIRMED** |
| MEFFDATE = PDINTTBL.START_DATE | **CONFIRMED** |
| A1 → MCURRATE hierarchy | **CONFIRMED** |
| Rate format N(8.4) percent | **CONFIRMED** |
| DINT_RULE selection | **Union merge** — both rules 0 and 3; tie-break Rule 3 at 19800101 | **CONFIRMED** (validation 2026-06-30) |
| Loader / validator design | **IMPLEMENTATION READY** |

---

## 5. Readiness

**Recommendation:** **READY FOR DEVELOPMENT**

All three SME gates are **CLOSED**. Development Agent may start **PR-5 QUIKUINT** using [`ISWL_QUIKUINT_Next_Stage_Prompt.md`](../../docs/research/ISWL_Implementation/ISWL_QUIKUINT_Next_Stage_Prompt.md).
