# ISWL QUIKISSC Implementation Blueprint

**Project:** LifePRO → QLAdmin Conversion Platform  
**Issue:** #33 — ISWL Phase 6 QUIKISSC  
**Version baseline:** v57.40 (post–PR-5 QUIKUINT)  
**Date:** 2026-06-28  
**Mode:** Planning only — no code changes  
**Authority:** Issue #31 segment trace (20260629), Product Book addendum, QLAdmin Help §7.144 (PDF p.821), Issue #32 QUIKUINT closeout  
**SME log:** [`Issue_33_SME_Questions.md`](../../Issue_Log_Items/Issue_33/Issue_33_SME_Questions.md) — **OPEN**

---

## Scope

Implementation blueprint for **QUIKISSC** — ISWL surrender charge schedules for the 8 MPLAN fleet.

| Target | QLAdmin table | Readiness |
|--------|---------------|-----------|
| QUIKISSC | `QuikIssc` | **READY AFTER SME CONFIRMATION** |

**ISWL fleet (8 MPLANs):** `1658C1`, `1658CS`, `1659C2`, `1659CR`, `1659CS`, `1659SR`, `1669SR`, `1679CS`

**Prerequisites:** Issue #31 PR-1–PR-4 **CLOSED**; Issue #32 PR-5 QUIKUINT **APPROVED**.

**Out of scope for Phase 6:** Expenses, QuikIsrr (partial surrender), DBF production emit / `app.py` integration (unless explicitly requested).

---

## Mandatory hierarchy (QUIKISSC)

```text
PPRDF (not in repo — optional top link)
  ↓
PCOMP (PRODUCT_ID = ISWL coverage)
  ↓
PCOVR (COVERAGE_ID, POLICY_FORM_NUM)
  ↓
PCOVRSGT (SEGT_FLAG=Y → SEGT_ID)
  ↓
PSEGT (SEGMENT_ID + SEGT_TYPE ∈ {SR, SL})
  ↓
Rate schedule (Rate_Table / PDAGE / SEGT_DATA constants — TBD after pointer decode)
  ↓
Policy Form Crosswalk → authoritative MPLAN
  ↓
QuikIssc (PLAN + dimensions + SCHG01..SCHG20)
```

**Non-negotiable rules:**

1. **Never map from TYPE_CODE alone** — prove PCOVRSGT → PSEGT(SR/SL) first.  
2. **SR → SL** is the preferred Product Book path; U7/U8 only if SR/SL absent (ISWL: absent).  
3. **Do not use TP/TX** — tax valuation/reserve data.  
4. **Do not use PAAGERAT** — no surrender TYPE_CODE in extract.

---

## SME gate status (updated 2026-06-30 — post forensic pointer resolution)

Forensic decode ([`Issue_33_Forensic_Pointer_Resolution.md`](../../Issue_Log_Items/Issue_33/Issue_33_Forensic_Pointer_Resolution.md)) and the SME sign-off package ([`Issue_33_QUIKISSC_SME_Answers.md`](../../Issue_Log_Items/Issue_33/Issue_33_QUIKISSC_SME_Answers.md)) reduced all open items to approve-or-correct decisions.

| Gate | Decision | Status |
|------|----------|--------|
| Segment path SR/SL | Hub `659 CEN II`, 8/8 coverages | **FORENSICALLY RESOLVED** — SME sign-off A |
| Rate source | `PSEGT(SL)` → `OSLNS00XT`/`SLD000` → **Rate_Table TYPE_CODE=SL** (PDAGE SL rejected — zero) | **FORENSICALLY RESOLVED** — SME sign-off A |
| U7/U8 fallback | Not present for ISWL | **CLOSED** |
| TP/TX exclusion | Tax only — not surrender | **CLOSED** |
| QuikIssc schema | Help §7.144 — SCHG01–20 | **CLOSED** |
| Percent format | Percent literal `100.0000` = 100%; fields **SCHG01–SCHG20** N(8.4) | **FORENSICALLY RESOLVED** — SME sign-off F |
| Dimensional scope | Varies by duration only; `SEX=M`, `UWCLASS=S→SM`, `BAND=1`, `AGE=0` | **C CLOSED**; **D established** |
| Shared schedule | Replicate hub schedule to 8 MPLANs → **8 rows** | **FORENSICALLY RESOLVED** — SME sign-off B |
| SCHG15–20 | Blank (no source durations 15–20) | **CLOSED** (SME Gate E) |

---

## Provisional authoritative mapping (pending SME)

| QuikIssc field | LifePRO source (provisional) | Transform |
|----------------|------------------------------|-----------|
| **PLAN** | Crosswalk | Each **8 ISWL MPLANs** |
| **AGE** | Rate row AGE | Attained age (0 in hub SL extract) |
| **GENDER** | Rate row SEX | M/F/J/U |
| **UWCLASS** | Rate row UNDERWRITING_CLASS | `S` → **`SM`** (`UWCLASS_MAP`) |
| **BAND** | Rate row BAND | Band code |
| **ISSCNTRY** | Segmentation default | `0000` unless filing variation |
| **ISSUEST** | Segmentation default | `00` unless filing variation |
| **SCHG01..SCHGN** | Rate_Table SL VALUE | Duration *n* surrender charge |

---

## Provisional transform (PR-6 — after SME closure)

```text
For each ISWL MPLAN in ISWL_MPLAN_ALLOWLIST:
  1. PCOVRSGT → PSEGT gate: SR slot resolves (8/8)
  2. PCOVRSGT → PSEGT gate: SL slot resolves (8/8)
  3. Decode PSEGT(659 CEN II, SL).SEGT_DATA rate pointer
  4. Load surrender schedule rows (expect duration-indexed percentages)
  5. Validate SR → SL parent/child relationship (Product Book)
  6. Pivot DURATION 1..N → SCHG01..SCHGN on QuikIssc row
  7. Replicate or vary schedule per MPLAN per SME decision
  8. Format SCHG as N(8.4) per SME percent literal rule
```

---

## Hub surrender schedule (CORRELATION ONLY — not approved for emit)

Rate_Table `659 CEN II` / TYPE_CODE=**SL** / M / S / Band 1:

| Duration | VALUE |
|----------|------:|
| 1–2 | 100.0000 |
| 3 | 70.0000 |
| 4 | 60.0000 |
| 5 | 50.0000 |
| 6 | 40.0000 |
| 7 | 30.0000 |
| 8 | 20.0000 |
| 9 | 15.0000 |
| 10 | 10.0000 |
| 11 | 8.0000 |
| 12 | 6.0000 |
| 13 | 4.0000 |
| 14 | 2.0000 |

**Do not emit until segment pointer proof + SME sign-off.**

---

## QLAdmin target schema (confirmed)

**Source:** QLAdmin Help **§7.144** — `QuikIssc` (ISWL Surrender Charges)

| Field | Type | Len | Description |
|-------|------|-----|-------------|
| PLAN | C | 6 | Plan code |
| AGE | N | 3 | Attained age |
| GENDER | C | 1 | Gender |
| UWCLASS | C | 2 | Underwriting class |
| BAND | C | 2 | Insurance band |
| ISSCNTRY | C | 4 | Issue country |
| ISSUEST | C | 2 | Issue state |
| SCHG01–SCHG20 | N | 8.4 | Surrender charge duration 1–20 |

**Index key:** `PLAN + GENDER + UWCLASS + BAND + ISSCNTRY + ISSUEST`

---

## Expected output (forensically determined — pending SME sign-off)

Forensic analysis confirmed the SL schedule varies by **duration only** (`SEX=M`, `UWCLASS=S`, `BAND=1`, `AGE=0` are all constant). One dimension tuple → one row per MPLAN.

| Metric | Value |
|--------|------:|
| ISWL MPLANs | 8 |
| Rows per MPLAN | 1 |
| **Total QuikIssc rows** | **8** |
| Duration columns populated | 14 (SCHG01–14) |
| Duration columns blank | 6 (SCHG15–20) |

---

## Implementation approach (PR-6 — after SME)

1. **Research task:** PSEGT SL pointer decode (`OSLNS00XT`) — **COMPLETE** (see forensic resolution).  
2. **New loader:** `qla_core/quikissc_loader.py` — segment-gated duration pivot (not PAAGERAT).  
3. **Schema:** Add `QuikIssc` to `rate_dbf_schema.py`.  
4. **Pipeline:** Wire `iswl_phase6` in config; separate from factor grids.  
5. **Validator:** `tools/validators/iswl_quikissc_reconcile.py`.

**Do not reuse** PAAGERAT attained-age scalar loader or WL `EXCLUDED_TYPE_CODES` emit path without segment proof.

---

## Recommendation

**READY AFTER SME CONFIRMATION** — launch SME Review Agent to close gates in [`Issue_33_SME_Questions.md`](../../Issue_Log_Items/Issue_33/Issue_33_SME_Questions.md), then Development Agent with [`ISWL_QUIKISSC_Next_Stage_Prompt.md`](ISWL_QUIKISSC_Next_Stage_Prompt.md).

See also: [`ISWL_QUIKISSC_Table_Design.md`](ISWL_QUIKISSC_Table_Design.md), [`ISWL_QUIKISSC_Validation_Strategy.md`](ISWL_QUIKISSC_Validation_Strategy.md).
