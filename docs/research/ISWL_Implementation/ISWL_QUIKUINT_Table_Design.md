# ISWL QUIKUINT Table-by-Table Design

**Project:** LifePRO → QLAdmin — QUIKUINT (UL Interest Rates)  
**Issue:** #32 — Phase 5  
**Version baseline:** v57.39  
**Date:** 2026-06-30 (SME gate closure)  
**Mode:** Planning only  
**Readiness:** **READY FOR DEVELOPMENT**

---

## ISWL coverage ↔ MPLAN reference

| Coverage ID | MPLAN | Description |
|-------------|-------|-------------|
| 658 CEN I | 1658C1 | 658 CEN I |
| 658 CEN SD | 1658CS | 658 CEN SD |
| 659 CEN II | 1659C2 | 659 CEN II |
| 659 CEN SR | 1659CR | 659 CEN SR |
| 659 CEN SD | 1659CS | 659 CEN SD |
| 659 SR GD | 1659SR | 659 SR GD |
| 669 SR GD | 1669SR | 669 SR GD |
| 679 CEN SD | 1679CS | 679 CEN SD |

**Hub segment:** `659 CEN II` — carries `A1`, `G1`, `LN` for all 8 coverages via shared PCOVRSGT slots.

---

# QUIKUINT

## 1. LifePRO hierarchy

```text
PCOMP
  PRODUCT_ID = {658 CEN I | … | 679 CEN SD}
  ↓
PCOVR
  COVERAGE_ID = PRODUCT_ID
  POLICY_FORM_NUM → crosswalk MPLAN
  ↓
PCOVRSGT
  SEGT_FLAG = Y
  SEGT_ID = {659 CEN II | L14 | native segment per coverage}
  ↓
PSEGT (20260629 extract)
  SEGMENT_ID = PCOVRSGT.SEGT_ID
  SEGT_TYPE = A1 | G1 | LN  (8/8 ISWL coverages confirmed)
  ↓
PDINT (Declared Interest — rule header)
  IDENT + TYPE_CODE + DINT_RULE + EFF_DATE + LOW/HIGH_DATE + SEQ
  ↓
PDINTTBL (Declared Interest — rate schedule)
  IDENT + TYPE_CODE + DINT_RULE + IDX + START_DATE + END_DATE + DECLARED_RATE
  ↓
Crosswalk → MPLAN (1658C1 … 1679CS)
  ↓
QLAdmin QuikUint (Help §7.223)
```

**Example chain (659 CEN SD → credited rate):**

`PCOMP(659 CEN SD)` → `PCOVR` → `PCOVRSGT(SEGT_ID=659 CEN II, A1 slot)` → `PSEGT(659 CEN II, A1)` → `PDINT(IDENT=CENII, TYPE=A1)` → `PDINTTBL(DECLARED_RATE=4.50)` → `PLAN=1659CS` → `QuikUint.MCURRATE`.

**PPRDF:** Not in repo; hierarchy starts at PCOMP (accepted for ISWL trace).

---

## 2. Source analysis

### 2.1 PDINT (rule header)

**File:** `QLA_Migration/Source/PDINT_DeclaredInterestRates_Extract_20260629.csv`

| Metric | Value |
|--------|------:|
| Rows | 10 (+ header separator) |
| Distinct IDENTs | 8 |

**Columns (authoritative):**

| Column | Role |
|--------|------|
| IDENT | Interest table identifier — links to segment dictionary (SME map) |
| TYPE_CODE | Interest type in LifePRO (`A1`, `C1`, `C3` in extract) |
| DINT_RULE | Rule variant within IDENT+TYPE (multiple rows per IDENT) |
| EFF_DATE | Rule effective date |
| SEQ | Sequence within rule set |
| LOW_DATE / HIGH_DATE | Applicability window |
| LOW_PROCESS_DUR / HIGH_PROCESS_DUR | Duration bounds |
| INVESTMENT_CODE | Investment linkage (if used) |
| RATE_DUR_PERIOD_CD | Duration period code |
| MULTIPLIER | Rate multiplier |
| DINT_KEY0 | Surrogate key |

**Primary key (logical):** `(IDENT, TYPE_CODE, DINT_RULE, EFF_DATE, SEQ)`

**Foreign keys:** IDENT → PSEGT segment dictionary (inferred, not FK in extract); TYPE_CODE ↔ PSEGT `SEGT_TYPE` for `A1` only (proven).

**TYPE_CODE distribution:**

| TYPE_CODE | PDINT rows | PSEGT ISWL slot | QUIKUINT role |
|-----------|----------:|-----------------|---------------|
| A1 | 5 | A1 8/8 | **MCURRATE** (credited/current) |
| C1 | 4 | — | Not ISWL UL interest v1 |
| C3 | 1 | — | Dividend (`DIV01`) — exclude |
| G1 | **0** | G1 8/8 | **MGTDRATE** — **gap** |
| LN | **0** | LN 8/8 | Loan — **not QuikUint** |

### 2.2 PDINTTBL (rate schedule)

**File:** `QLA_Migration/Source/PDINTTBL_DeclaredInterestRates_Extract_20260629.csv`

| Metric | Value |
|--------|------:|
| Rows | 37 (+ header separator) |
| Distinct IDENTs | 8 |

**Columns:**

| Column | Role |
|--------|------|
| IDENT | Join to PDINT |
| TYPE_CODE | Join to PDINT |
| DINT_RULE | Join to PDINT |
| EFF_DATE | Join to PDINT |
| SEQ | Join to PDINT |
| IDX | Schedule index within rule |
| START_DATE | Rate tier start |
| END_DATE | Rate tier end |
| DECLARED_RATE | **Authoritative numeric rate** (N 8.4 compatible) |
| RATE_GUAR_DUR | Guaranteed duration (if used) |
| DINT_KEY0 | Surrogate key |

**Primary key (logical):** `(IDENT, TYPE_CODE, DINT_RULE, EFF_DATE, SEQ, IDX)`

**Join to PDINT:** All six header keys must match before reading schedule rows.

### 2.3 PDINT ↔ PDINTTBL interaction

```text
PDINT row (header)
  IDENT=CENII, TYPE=A1, DINT_RULE=3, EFF_DATE=19800101, SEQ=1
    ↓ 1:N
PDINTTBL rows (schedule tiers)
  IDX=1: 1980-01-01 → 1988-12-31 @ 11.00%
  IDX=2: 1989-01-01 → 2001-12-31 @  9.00%
  IDX=3: 2002-01-01 → 2099-12-31 @  4.50%  ← current tier
```

**Rate selection rule (proposed — SME confirm):**

1. Resolve IDENT from segment map for MPLAN.
2. Filter PDINT where `TYPE_CODE` matches PSEGT role (`A1` for credited).
3. Select PDINT row by active `EFF_DATE` / date windows for conversion generation.
4. Join PDINTTBL; pick tier where `START_DATE ≤ anchor_date ≤ END_DATE`.
5. Map `DECLARED_RATE` → `MCURRATE` and/or `MGTDRATE`.

### 2.4 Secondary sources (validation only)

| Source | Use | Authority |
|--------|-----|-----------|
| PPBEN `FV_GUAR_RATE` | Cross-check 4.50% | Policy-level validation |
| CSO crosswalk / NFOINT | Cross-check 4.50% | Plan-level validation |
| PRBENINT | Profile ISWL rows | Candidate — not primary until traced |
| PLOAN / QuikPlSt | Loan rate | Issue #32 — separate from QuikUint |

---

## 3. Source reader (planned)

| Item | Detail |
|------|--------|
| **Source files** | PDINT + PDINTTBL extracts; PCOVRSGT; PCOVR; PSEGT; crosswalk XLSX |
| **Reader** | **New** — `pdint_uint_loader.py` (proposed name) |
| **Parser** | CSV DictReader; strip padded LifePRO column names |
| **Segment validation** | Reuse `SegmentResolver` + PSEGT gate for A1/G1/LN |
| **Already implemented?** | **No** |
| **Need modification?** | N/A — greenfield loader |
| **Pipeline family** | **Outside** factor-grid (`build_factor_grid`) — plan-level rows |

---

## 4. Transformation logic

### 4.1 Grouping model

Unlike QuikCoi/QuikGps (segmentation grid), **QuikUint groups by plan + effective date**:

```text
Group key: (MPLAN, MEFFDATE)
One PDINTTBL tier → one QuikUint row
SME-approved: emit ALL CENII/A1 historical tiers per MPLAN
Fallback: one current-tier row per MPLAN when history unavailable
```

### 4.2 Final field mapping (SME confirmed)

| QUIKUINT field | LifePRO source | Transform | Status |
|----------------|----------------|-----------|--------|
| MPLAN | Crosswalk | All **8 ISWL MPLANs** | **CONFIRMED** |
| MEFFDATE | PDINTTBL | **START_DATE** of each historical tier (D8 `YYYYMMDD`) | **CONFIRMED** |
| MCURRATE | PDINTTBL | **DECLARED_RATE** via CENII / **TYPE=A1** | **CONFIRMED** |
| MGTDRATE | PDINTTBL | **Same value as MCURRATE** on each tier | **CONFIRMED** |
| *(loan)* | — | **`quikplan.LOANINT`** / **`QuikPlSt.MLOANINT`** — **not QuikUint** | **CONFIRMED** |

**Rate format:** `DECLARED_RATE` is percent-scale (`4.50000` = 4.5%). Emit as N(8.4) without divide-by-100. Round to 4 decimal places; pad to schema width on DBF emit.

**END_DATE:** Used only to select active tier (`START_DATE ≤ anchor ≤ END_DATE`). Not emitted to QuikUint.

**PDINT.EFF_DATE:** Header join key with `(IDENT, TYPE_CODE, DINT_RULE, SEQ)` — **not** MEFFDATE.

### 4.3 IDENT map — **CONFIRMED**

| MPLAN | Coverage | PDINT IDENT |
|-------|----------|-------------|
| 1658C1 | 658 CEN I | **CENII** |
| 1658CS | 658 CEN SD | **CENII** |
| 1659C2 | 659 CEN II | **CENII** |
| 1659CR | 659 CEN SR | **CENII** |
| 1659CS | 659 CEN SD | **CENII** |
| 1659SR | 659 SR GD | **CENII** |
| 1669SR | 669 SR GD | **CENII** |
| 1679CS | 679 CEN SD | **CENII** |

SME confirmed: **CENII for all eight ISWL MPLANs.**

### 4.4 DINT_RULE handling — union merge (validated 2026-06-30)

CENII has two A1 rules with **different schedules** — not duplicates.

| DINT_RULE | EFF_DATE | Tiers | Role |
|-----------|----------|------:|------|
| 3 | 19800101 | 3 | Original declared-interest rule |
| 0 | 20030813 | 3 | Later restatement (revised early tiers) |

**PR-5 emit mode: `union_merge`** — include unique START_DATEs from **both** rules.

| MEFFDATE | Rate | Source | Notes |
|----------|-----:|--------|-------|
| 19800101 | 11.00000 | Rule 3 | Tie-break over Rule 0 (7.00000) |
| 19890101 | 9.00000 | Rule 3 | Rule 0 has no equivalent |
| 19990101 | 5.00000 | Rule 0 | **Omitted if Rule 3 only** — SME violation |
| 20020101 | 4.50000 | Both | Identical |

**Do not filter to Rule 3 only.** See [`Issue_32_QUIKUINT_Historical_Tier_Validation.md`](../../Issue_Log_Items/Issue_32/Issue_32_QUIKUINT_Historical_Tier_Validation.md).

---

## 5. Output mapping — QuikUint (confirmed Help §7.223)

| Output field | Type | Len | Source | Transformation | Default | Validation |
|--------------|------|-----|--------|----------------|---------|------------|
| MPLAN | C | 6 | Crosswalk | ISWL allowlist | — | Required; 8 MPLANs |
| MEFFDATE | D | 8 | PDINTTBL | Tier START_DATE or rule EFF_DATE | — | Unique per MPLAN+date |
| MGTDRATE | N | 8.4 | PDINTTBL | DECLARED_RATE (G1 path) | — | ≥ 0; matches PPBEN spot-check |
| MCURRATE | N | 8.4 | PDINTTBL | DECLARED_RATE (A1 path) | — | ≥ 0 |

**No supporting key table** documented for QuikUint.

**Related tables (not QuikUint):**

| Table | Field | Purpose |
|-------|-------|---------|
| QuikPlan | LOANINT | Plan-level loan rate |
| QuikPlSt | MLOANINT | State loan rate override |
| QuikPlSt | MLOANINTX | Advance/arrears (Issue #32) |

---

## 6. Expected row counts (SME-approved, validated)

| Emit mode | ISWL QuikUint rows | Assumption |
|-----------|-------------------:|------------|
| **Union merge (PR-5 default)** | **32** | 8 MPLANs × 4 unique START_DATEs (Rules 0+3 merged) |
| **Fallback — current tier only** | **8** | 1 tier/MPLAN when history unavailable |

~~Rule 3 only (24 rows)~~ — **rejected**; omits Rule 0 tier at 19990101 @ 5%.  
~~Both rules raw (48 rows)~~ — **rejected**; duplicate/conflicting MEFFDATE keys.

---

## 7. Validation strategy

See [`ISWL_QUIKUINT_Validation_Strategy.md`](ISWL_QUIKUINT_Validation_Strategy.md).

---

## 8. Development complexity

**Medium–High** (segment + PDINT join + effective-date logic; outside existing factor-grid pipeline)

**Expected new files:**

| File | Purpose |
|------|---------|
| `qla_core/pdint_uint_loader.py` | PDINT hierarchy → QuikUint rows |
| `qla_core/rate_dbf_schema.py` | Add `QuikUint` layout (4 fields) |
| `qla_core/rate_pipeline.py` | Wire uint stream (minimal extension) |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | `iswl_phase5` block |
| `tools/validators/iswl_quikuint_reconcile.py` | V-UINT-01–06 |

**Regression:** Must not alter QuikCvs, QuikGps, QuikCoi, QuikGcoi row counts from Issue #31 baselines.

---

## 9. Edge cases

| Case | Handling |
|------|----------|
| No PDINT IDENT for MPLAN | EXCLUDE + audit (do not invent rate) |
| Multiple active PDINT rules | Config/SME selects DINT_RULE |
| G1 slot with no PDINT G1 row | **MGTDRATE = MCURRATE** (SME confirmed) |
| LN segment | Skip QuikUint; document loan path separately |
| PPBEN rate ≠ PDINTTBL | WARNING — do not override PDINT without SME |
| Non-ISWL IDENTs in catalog | Exclude from ISWL allowlist emit |
