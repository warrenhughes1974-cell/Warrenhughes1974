# ISWL QUIKISSC Table-by-Table Design

**Project:** LifePRO → QLAdmin — QUIKISSC (ISWL Surrender Charges)  
**Issue:** #33 — Phase 6  
**Version baseline:** v57.40  
**Date:** 2026-06-28  
**Mode:** Planning only  
**Readiness:** **READY AFTER SME CONFIRMATION**

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

**Hub segment:** `659 CEN II` — carries **SR**, **SL** (and U5, U6, BP, CV, A1, G1, LN, UF, …) for all 8 coverages via shared PCOVRSGT slots.

---

# QUIKISSC

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
  SEGT_ID = 659 CEN II (hub slots — majority of UL types)
  ↓
PSEGT (20260629 extract)
  SEGMENT_ID = 659 CEN II
  SEGT_TYPE = SR | SL  (8/8 ISWL coverages confirmed)
  SEGT_DATA = rate pointer / child-segment wiring (hex → ASCII)
  ↓
Rate schedule
  Primary candidate: Rate_Table TYPE_CODE=SL on SEGT_ID coverage
  Fallback: segment constants; NOT PDAGE SL (zeros); NOT TP/TX
  ↓
Crosswalk → MPLAN (1658C1 … 1679CS)
  ↓
QLAdmin QuikIssc (Help §7.144)
```

**Example chain (659 CEN SD → surrender schedule):**

`PCOMP(659 CEN SD)` → `PCOVR` → `PCOVRSGT(SEGT_ID=659 CEN II, SR/SL slots)` → `PSEGT(659 CEN II, SR)` → `PSEGT(659 CEN II, SL)` → `Rate_Table(SL, duration schedule)` → `PLAN=1659CS` → `QuikIssc.SCHG01..14`.

**PPRDF:** Not in repo; hierarchy starts at PCOMP (accepted for ISWL trace).

---

## 2. Source analysis

### 2.1 PSEGT (segment registry)

**File:** `QLA_Migration/Source/PSEGT_Segment_Extract_20260629.csv`

| Metric | SR | SL |
|--------|----|----|
| ISWL 8/8 | ✅ | ✅ |
| Hub SEGMENT_ID | `659 CEN II` | `659 CEN II` |
| Global segment count | 2 | 2 |

**Key columns:** `SEGMENT_ID`, `SEGT_TYPE`, `SEGT_DATA`, `SEGT_KEY0`, `ROW_COLUMN`

**SL payload clues (CORRELATION ONLY):**

- ASCII fragment: `659 CEN IISLD000`  
- Rate name fragment: **`OSLNS00XT`**  
- Modifier: `MB01`, `MOD_DATE=20030630`

**SR payload clues:**

- ASCII fragment: `659 CEN IISRY659 CEN II` with embedded Y/N child flags  
- References same hub segment ID

### 2.2 PCOVRSGT (segment linkage)

**File:** `plan_analysis/source_data/coverage/PCOVRSGT.csv`

| Metric | Value |
|--------|------:|
| Active ISWL slots | 191 |
| Slots resolving in PSEGT | 185 (96.9%) |
| Hub inheritance | All 8 coverages reference `659 CEN II` in active slots |

**Resolution code:** `qla_core/rate_segment_resolution.py` — `PAAGERAT.COVERAGE_ID = PCOVRSGT.SEGT_ID → parent PCOVR.COVERAGE_ID`

### 2.3 Rate_Table (primary rate candidate)

**File:** `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv`

**Filter (provisional):** `COVERAGE_ID = 659 CEN II`, `TYPE_CODE = SL`

| Column | Role |
|--------|------|
| COVERAGE_ID | Segment ID (hub) |
| TYPE_CODE | SL (Rate_Table vocabulary — must match PSEGT proof) |
| AGE | Issue/attained age axis (0 in hub rows) |
| SEX | Gender |
| BAND | Band |
| UNDERWRITING_CLASS | UW class |
| DURATION | Policy year / duration index → SCHG column |
| VALUE | Surrender charge amount (percent — format TBD) |

**Hub row count:** 14 (durations 1–14, Male, S, Band 1)

**Pipeline note:** `SL` is in `EXCLUDED_TYPE_CODES` for WL CV conversion — QUIKISSC requires a **dedicated loader**, not inclusion in existing WL TYPE map.

### 2.4 PDAGE (secondary — not authoritative)

**File:** `QLA_Migration/Source/PDAGE_AgeDuration_Rates_Extract_20260530.csv`

- 12 SL rows on hub — all **VALUE1_FLOAT = 0.0**  
- **Do not use** for emit unless SME proves Rate_Table wrong

### 2.5 PAAGERAT

**No surrender TYPE_CODE** — not a source for QUIKISSC.

### 2.6 Withdrawn sources

| Source | ISWL hub rows | Status |
|--------|-------------:|--------|
| PDAGE TP/TX | 2,128 each | Tax — excluded |
| Rate_Table TP/TX | 19,780 each | Tax — excluded |
| U7/U8 PSEGT | 0 | Absent |

### 2.7 Policy validation fields (future)

| Table / field | Purpose |
|---------------|---------|
| PPBENTYP.BF_CURR_SURR_LOAD | Current surrender load validation |
| PPRBNUL.SURR_LOAD | Policy surrender load |
| PPRBNUL.LAPSE_SURR_LOAD | Lapse surrender load |
| PFNDD.SURRENDER_LOAD | Fund surrender load |

---

## 3. Transform logic (provisional)

### 3.1 Segment gates

```python
# Pseudocode — planning only
for coverage in ISWL_COVERAGE_IDS:
    assert psegt_has_type(resolve_segt_id(coverage), "SR")
    assert psegt_has_type(resolve_segt_id(coverage), "SL")
# Expect: 8/8 for SR and SL
```

### 3.2 Rate load

```python
# After SME confirms pointer:
schedule = load_surrender_schedule(
    segment_id="659 CEN II",
    seg_type="SL",
    pointer=decode_segt_data(sl_row),
)
# schedule: list of (duration, value) sorted by duration
```

### 3.3 Pivot to QuikIssc

```python
row = {
    "PLAN": mplan,
    "AGE": schedule.age,
    "GENDER": schedule.gender,
    "UWCLASS": map_uwclass(schedule.uw),
    "BAND": schedule.band,
    "ISSCNTRY": "0000",
    "ISSUEST": "00",
}
for d, val in schedule.durations:
    row[f"SCHG{d:02d}"] = format_rate(val)  # N(8.4) — format TBD
```

---

## 4. Output mapping table (provisional)

| QuikIssc field | LifePRO source | Rule | SME |
|----------------|----------------|------|-----|
| PLAN | PCOVR → crosswalk | 8 ISWL MPLANs | Q6 |
| AGE | Rate_Table.AGE | 0 = all ages? | Q5 |
| GENDER | Rate_Table.SEX | M/F | Q5 |
| UWCLASS | Rate_Table.UNDERWRITING_CLASS | `S` → **`SM`** (`UWCLASS_MAP`, PR-1–PR-4) | D |
| BAND | Rate_Table.BAND | Pad to 2 chars | — |
| ISSCNTRY | Config default | 0000 | Q5 |
| ISSUEST | Config default | 00 | Q5 |
| SCHG01 | VALUE @ DURATION=1 | Percent literal TBD | Q4 |
| … | … | … | … |
| SCHG14 | VALUE @ DURATION=14 | | |
| SCHG15–20 | — | Blank/zero unless extended | Q9 |

---

## 5. Complexity assessment

| Factor | Rating | Notes |
|--------|--------|-------|
| Hierarchy proof | **Medium** | SR/SL wired; pointer decode remaining |
| Rate shape | **Low–Medium** | Duration pivot (not 10-wide factor grid) |
| Dimensional expansion | **Medium** | Source has 1 tuple; SME may require more |
| MPLAN replication | **Low** | Likely shared hub schedule |
| Regression risk | **Low** | Additive phase6 gate |
| SME dependency | **High** | Multiple open gates |

---

## 6. Related QLAdmin tables

| Table | Relationship |
|-------|--------------|
| QuikPlan | Plan master — surrender variation flags |
| QuikCvs | CV floor vs fund value less surrender charge |
| QuikDvs | Dividend variation — independent |
| QuikIswl | UL values — adjacent family |
| QuikIsrr | Partial surrender — separate scope |

---

## 7. Expected files (PR-6 — future)

| File | Action |
|------|--------|
| `qla_core/quikissc_loader.py` | Create |
| `qla_core/rate_dbf_schema.py` | Add QuikIssc fields |
| `qla_core/rate_dbf_writer.py` | QuikIssc writers |
| `qla_core/rate_pipeline.py` | Wire iswl_phase6 |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | iswl_phase6 block |
| `tools/validators/iswl_quikissc_reconcile.py` | V-ISSC checks |
| `Issue_Log_Items/Issue_33/output/Phase6_QUIKISSC/` | Artifacts |

**Do not modify** Phase 1–5 loader behavior except shared config wiring.
