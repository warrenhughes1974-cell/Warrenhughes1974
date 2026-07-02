# ISWL Table-by-Table Design

**Project:** LifePRO → QLAdmin — ISWL rate / UL factor tables  
**Version baseline:** v57.39  
**Date:** 2026-06-30 (updated — QUIKCOI/QUIKGCOI transform finalized)  
**Mode:** Planning only

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

**Hub segment:** `659 CEN II` carries U5, U6, BP, CV, A1, G1, LN, SR, SL, UF, etc. for all 8 coverages via shared PCOVRSGT slots.

---

# 1. QUIKCVS

## 1.1 LifePRO hierarchy

```text
PCOMP
  PRODUCT_ID = {658 CEN I | 658 CEN SD | 659 CEN II | … | 679 CEN SD}
  ↓
PCOVR
  COVERAGE_ID = PRODUCT_ID
  POLICY_FORM_NUM → crosswalk MPLAN
  ↓
PCOVRSGT
  SEGT_FLAG = Y
  SEGT_ID = {658 CEN I | 659 CEN II | native CV segment per coverage}
  ↓
PSEGT (20260629 extract)
  SEGMENT_ID = PCOVRSGT.SEGT_ID
  SEGT_TYPE = CV  (8/8 ISWL coverages confirmed)
  ↓
Rate Table (dual source — choose after parity)
  Primary (repo today): Rate_Table_Extract TYPE_CODE=CV at parent COVERAGE_ID
  Alternate: PDAGE_AgeDuration_Rates_Extract TYPE=CV
  ↓
Policy Form Crosswalk
  COVERAGE_ID / POLICY_FORM_NUM → PLAN (1658C1 … 1679CS)
  ↓
QLAdmin
  QuikPlCv (key / assumptions: MORT, ETIMORT, NFOINT, INTMETHCV via CSO crosswalk)
  QuikCvs (factor grid: CV0–CV9 × CNTL pages)
  quikplan.VARGP = 2
```

**Example chain (659 CEN SD):**

`PCOMP(659 CEN SD)` → `PCOVR` → `PCOVRSGT(SEGT_ID=659 CEN II, SEGT_TYPE slot CV)` → `PSEGT(659 CEN II, CV)` → `Rate_Table(COVERAGE_ID=659 CEN SD, TYPE=CV)` → `PLAN=1659CS` → `QuikCvs`.

## 1.2 Source reader

| Item | Detail |
|------|--------|
| **Source files** | `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv` (primary); `QLA_Migration/Source/PDAGE_AgeDuration_Rates_Extract_20260530.csv` (parity candidate); `plan_analysis/source_data/coverage/PCOVRSGT.csv`; `QLA_Migration/Source/PSEGT_Segment_Extract_20260629.csv`; `QLA_Migration/Source/PCOVR_Coverage_Extract_20260530.csv`; `plan_analysis/PCOMP.csv`; crosswalk XLSX |
| **Reader** | `qla_core/rate_factor_loader.py` — `transform_source()`, `LoaderConfig` |
| **Parser** | CSV DictReader; issue-age × duration pivot via `build_factor_grid()` |
| **Segment validation** | `tools/research/iswl_segment_trace.py` (research); optional gate in loader |
| **Already implemented?** | **Yes** for Rate_Table CV → QuikCvs (non-ISWL plans) |
| **Need modification?** | **Yes** — ISWL MPLAN filter / allowlist; optional PDAGE routing; PSEGT CV gate |
| **Need new reader?** | **No** (unless PDAGE becomes authoritative — then extend `LoaderConfig` source selector) |

## 1.3 Transformation logic

| Dimension | Source field | Transform |
|-----------|--------------|-----------|
| PLAN | Crosswalk | `COVERAGE_ID` → authoritative 6-char MPLAN |
| Issue age | `AGE` / `ISSUE_AGE` | Zero-pad to C2; cap at 99 |
| Duration | `DURATION` / `POLICY_YEAR` | Map to CNTL page + CV0–CV9 column via `duration_to_cntl_col()` |
| Gender | `SEX` | `SEX_MAP`: F/M/J |
| UW class | `UWCLS` / `UW_CLASS` | `UWCLASS_MAP`: 0→00, N→NS, S→SM, P→PR, B→ST |
| Band | `BAND` | `BAND_MAP`: 1→01, 2→02, 3→03 |
| Issue country | Config default | `ISSCNTRY` = `0000` (ALL) unless plan-specific |
| Issue state | Config default | `ISSUEST` = `00` (ALL) |
| Effective date | Config | `19000101` (`STANDARD_EFFDATE`) |
| Factor value | `VALUE` / rate column | Scale to CHAR(7), 2 decimal places default |

**Joins:**

1. Rate row `COVERAGE_ID` = PCOVR parent coverage (direct for CV in Rate_Table).
2. PSEGT confirms `CV` capability on resolved segment.
3. CSO crosswalk supplies QuikPlCv assumption codes per PLAN + gender + UW.

**Grid key:** `(PLAN, AGE, CNTL, GENDER, UWCLASS, BAND, ISSCNTRY, ISSUEST, EFFDATE)`.

## 1.4 Output mapping — QuikCvs

| Output field | Type | Len | Source | Transformation | Default | Validation |
|--------------|------|-----|--------|----------------|---------|------------|
| PLAN | C | 6 | Crosswalk MPLAN | Upper/strip | — | Must be in ISWL allowlist for ISWL emit |
| AGE | C | 2 | Rate issue age | zfill(2); cap 99 | — | Required |
| CNTL | C | 2 | Duration decade | `duration_to_cntl_col(dur)` | — | 00–99 pages |
| CV0–CV9 | C | 7 | Rate factor | Format 7-char, 2 dec | blank if no cell | No duplicate grid cell |
| GENDER | C | 1 | SEX | SEX_MAP | — | F/M/J |
| UWCLASS | C | 2 | UW | UWCLASS_MAP | — | NS/SM/00/PR/ST |
| BAND | C | 2 | BAND | BAND_MAP | 00 if N/A | 01–03 |
| ISSCNTRY | C | 4 | Config | Segmentation default | 0000 | — |
| ISSUEST | C | 2 | Config | Segmentation default | 00 | — |
| EFFDATE | D | 8 | Config | STANDARD_EFFDATE | 19000101 | Must match QuikPlNb |

## 1.4b Output mapping — QuikPlCv (key table)

| Output field | Source | Transform |
|--------------|--------|-----------|
| PLAN, GENDER, UWCLASS, BAND, ISSCNTRY, ISSUEST, EFFDATE | Grid keys | Same as factor rows |
| MORT | CSO crosswalk | `mort_code_default` or gender/UW column |
| ETIMORT | CSO crosswalk | default or specific; blank allowed |
| NFOINT | CSO crosswalk | ISWL → code from crosswalk (4.50% path) |
| INTMETHCV | CSO crosswalk | `qla_intmethcv_code` |

## 1.5 Validation strategy

See [`ISWL_Validation_Strategy.md`](ISWL_Validation_Strategy.md) § QUIKCVS.

## 1.6 Development complexity

**Medium**

**Expected files:**

- `qla_core/rate_factor_loader.py` (ISWL gate, optional PDAGE path)
- `qla_core/rate_pipeline.py` (config wiring)
- `plan_analysis/phase_r5_rate_loader/rate_loader_config.json`
- `tools/research/iswl_quikcvs_parity.py` (new validation script)
- `qla_core/cso_mortality_crosswalk.py` (verify ISWL rows only — likely no change)

---

# 2. QUIKGPS

## 2.1 LifePRO hierarchy

```text
PCOMP → PCOVR → PCOVRSGT
  SEGT_ID = {658 CEN I | 659 CEN II | native BP slot}
  ↓
PSEGT
  SEGT_TYPE = BP  (8/8 confirmed)
  ↓
PAAGERAT
  COVERAGE_ID = SEGT_ID (segment id, not parent coverage)
  TYPE_CODE = BP
  SEQ = attained age
  ↓
SegmentResolver
  SEGT_ID → parent COVERAGE_ID → PLAN
  ↓
QLAdmin
  QuikGps (VARGP=3 attained-age grid)
  QuikPlGp (key table — minimal assumptions)
  quikplan.VARGP = 3
```

**Example (679 CEN SD):** `PCOVRSGT(SEGT_ID=659 CEN II)` → `PAAGERAT(COVERAGE_ID=659 CEN II, TYPE=BP)` → parent `679 CEN SD` → `PLAN=1679CS`.

## 2.2 Source reader

| Item | Detail |
|------|--------|
| **Source files** | `PAAGERAT_AttainedAge_Rates_Extract_20260428.csv`; `PCOVRSGT.csv`; `PCOVR` extract; crosswalk |
| **Reader** | **Pattern from** `qla_core/paagerat_pr_loader.py` — **not yet BP** |
| **Parser** | Filter `TYPE_CODE=BP`; VARGP=3 single-column grid |
| **Already implemented?** | **Partial** — PR only in production loader |
| **Need modification?** | **Yes** — add BP type filter + ISWL scope |
| **Need new reader?** | **Recommended** — `paagerat_bp_loader.py` or shared `paagerat_attained_age_loader.py` with `type_codes` param |

## 2.3 Transformation logic

| Dimension | Source | Transform |
|-----------|--------|-----------|
| Attained age | `SEQ` | zfill(2) → AGE; cap 99 |
| Gender | `SEX` | SEX_MAP |
| UW class | `UWCLS` | UWCLASS_MAP |
| Band | `BAND` | BAND_MAP |
| Factor | `VALUE_FLOAT` | GP0 column only (CNTL=00, col 0) |
| PLAN | SegmentResolver | Parent coverage → crosswalk |
| Segment tier | Resolver | 0 = parent match; 1 = child segment |

**ISWL PAAGERAT BP row counts (parent coverage):**

| Parent coverage | MPLAN | BP rows |
|-----------------|-------|---------|
| 658 CEN SD | 1658CS | 444 |
| 659 CEN SD | 1659CS | 152 |
| 669 SR GD | 1669SR | 172 |
| 679 CEN SD | 1679CS | 396 |
| **Total** | | **1,164** |

**Gap:** `1658C1`, `1659C2`, `1659CR`, `1659SR` — PSEGT BP present; zero PAAGERAT BP on parent (rates via hub segment only on 4 parents above).

## 2.4 Output mapping — QuikGps

| Output field | Type | Len | Source | Transformation | Default | Validation |
|--------------|------|-----|--------|----------------|---------|------------|
| PLAN | C | 6 | Crosswalk | From parent resolution | — | ISWL allowlist |
| AGE | C | 2 | PAAGERAT.SEQ | Attained age, cap 99 | — | Required |
| CNTL | C | 2 | Fixed | `00` (VARGP=3) | 00 | — |
| GP0 | C | 7 | VALUE_FLOAT | 7-char factor | — | Single column populated |
| GP1–GP9 | C | 7 | — | Blank | blank | VARGP=3 |
| GENDER | C | 1 | SEX | SEX_MAP | — | — |
| UWCLASS | C | 2 | UWCLS | UWCLASS_MAP | — | — |
| BAND | C | 2 | BAND | BAND_MAP | — | — |
| ISSCNTRY | C | 4 | Config | Default | 0000 | — |
| ISSUEST | C | 2 | Config | Default | 00 | — |
| EFFDATE | D | 8 | Config | STANDARD_EFFDATE | 19000101 | — |

**Do not map PR → QUIKGPS for ISWL.** PR rows (328 on waiver segments) remain separate PR path.

## 2.5 Validation strategy

See [`ISWL_Validation_Strategy.md`](ISWL_Validation_Strategy.md) § QUIKGPS.

## 2.6 Development complexity

**Medium**

**Expected files:**

- `qla_core/paagerat_bp_loader.py` (new) or generalized loader
- `qla_core/rate_dbf_schema.py` — document BP→QuikGps path (not TYPE_TO_TABLE Rate_Table)
- `qla_core/rate_pipeline.py` — wire BP stream after PR
- `qla_core/rate_validation.py` — VARGP=3 plan set includes ISWL MPLANs with BP
- `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` — `paagerat_bp_type_codes: ["BP"]`

---

# 3. QUIKCOI

## 3.1 LifePRO hierarchy

```text
PCOMP → PCOVR → PCOVRSGT
  SEGT_ID = {658 CEN I | 659 CEN II}
  ↓
PSEGT
  SEGT_TYPE = U6  (8/8 — Current COI Rates Segment)
  ↓
PAAGERAT
  TYPE_CODE = U6
  COVERAGE_ID = SEGT_ID
  ↓
SegmentResolver → PLAN
  ↓
QLAdmin QuikCoi (QLAdmin Help §7.73 — confirmed)
  quikplan.VARGP = 3
```

**Withdrawn paths:** NC (Net Premium Credited), PPBEN UV fields, direct U6 without segment chain, issue-age × duration pivot from PAAGERAT.

## 3.2 Source reader

| Item | Detail |
|------|--------|
| **Source files** | `PAAGERAT_AttainedAge_Rates_Extract_20260428.csv`; `PCOVRSGT.csv`; `PCOVR` extract; `PSEGT_Segment_Extract_20260629.csv`; crosswalk |
| **Reader** | **None** — new loader required |
| **Template** | `paagerat_pr_loader.py` (attained-age scalar pattern) + `build_factor_grid()` |
| **Already implemented?** | **No** |
| **Need new reader?** | **Yes** — `paagerat_ul_coi_loader.py` (recommended shared U5/U6 core) |
| **Schema** | **Confirmed** — QLAdmin Help §7.73 |

## 3.3 Transformation logic — attained-age scalar emit

**Authoritative rule:** One PAAGERAT row produces exactly one QuikCoi row. PAAGERAT has **no duration column**; do **not** pivot ten rows into QX0–QX9.

| Dimension | Source | Transform |
|-----------|--------|-----------|
| PLAN | SegmentResolver → crosswalk | Parent coverage → MPLAN |
| Attained age | `SEQ` (1-based, 1–100) | → `AGE` C2, zero-pad, cap 99 |
| Control | (fixed) | `CNTL = "00"` |
| Rate | `VALUE_INFO` | → `QX0` CHAR(10); **never use `VALUE_FLOAT` when VALUE_INFO populated** |
| Durations | — | `QX1`–`QX9` **blank** |
| Gender / UW / Band | `SEX` / `UWCLS` / `BAND` | Standard maps |
| Country / State / Eff date | Config | `0000` / `00` / `19000101` |
| Hierarchy gate | PSEGT | `SEGT_TYPE=U6` on segment before emit |
| RECORD_SEQ | PAAGERAT | Must be `1` (primary table) |

**Grid key (output uniqueness):** `(PLAN, AGE, CNTL, GENDER, UWCLASS, BAND, ISSCNTRY, ISSUEST, EFFDATE)`.

**ISWL PAAGERAT U6 source counts:**

| Segment ID | Resolves to MPLAN | U6 rows |
|------------|-------------------|---------|
| `658 CEN I` | `1658CS` | 400 |
| `659 CEN II` | `1679CS` | 400 |
| **Total** | | **800** |

**Expected QuikCoi output:** **~792–800 rows** (8 tuples × SEQ 100 may cap-collide at AGE=99).

**Gap (document, do not invent rates):** 6/8 MPLANs (`1658C1`, `1659C2`, `1659CR`, `1659CS`, `1659SR`, `1669SR`) have PSEGT U6 capability but zero PAAGERAT U6 rows. SME/client confirmation required for partial fleet emit.

## 3.4 Output mapping — QuikCoi (confirmed)

QLAdmin Help §7.73 — index key: `PLAN + GENDER + UWCLASS + BAND + ISSCNTRY + ISSUEST`.

| Output field | Type | Len | Source | Transformation | Default | Validation |
|--------------|------|-----|--------|----------------|---------|------------|
| PLAN | C | 8 (Help); ISWL MPLAN 6 | Crosswalk | Segment-resolved MPLAN | — | `1658CS`, `1679CS` for v1 |
| AGE | C | 2 | `SEQ` | Attained age; zfill(2); cap 99 | — | VARGP=3 semantics |
| CNTL | C | 2 | Fixed | `"00"` | 00 | No duration paging for ISWL |
| QX0 | C | 10 | `VALUE_INFO` | Format CHAR(10) | — | Authoritative rate field |
| QX1–QX9 | C | 10 | — | **Blank** | blank | Intentionally unused |
| GENDER | C | 1 | `SEX` | SEX_MAP | — | F/M/J |
| UWCLASS | C | 2 | `UWCLS` | UWCLASS_MAP | — | — |
| BAND | C | 2 | `BAND` | BAND_MAP | — | — |
| ISSCNTRY | C | 4 | Config | Default | 0000 | — |
| ISSUEST | C | 2 | Config | Default | 00 | — |
| EFFDATE | D | 8 | Config | STANDARD_EFFDATE | 19000101 | — |

## 3.5 Validation strategy

See [`ISWL_Validation_Strategy.md`](ISWL_Validation_Strategy.md) § QUIKCOI.

## 3.6 Development complexity

**Medium**

**Expected files:**

- `qla_core/rate_dbf_schema.py` — add `QuikCoi` layout (`QX` prefix, CHAR(10))
- `qla_core/paagerat_ul_coi_loader.py` (new, parameterized U6/U5)
- `qla_core/rate_pipeline.py` — wire U6 stream + PSEGT gate
- `tools/validators/iswl_quikcoi_reconcile.py` (new)

---

# 4. QUIKGCOI

## 4.1 LifePRO hierarchy

```text
PCOMP → PCOVR → PCOVRSGT(SEGT_ID=659 CEN II)
  ↓
PSEGT
  SEGT_TYPE = U5  (8/8 — Guaranteed COI Rates Segment)
  ↓
PAAGERAT
  TYPE_CODE = U5
  COVERAGE_ID = SEGT_ID
  ↓
SegmentResolver → PLAN
  ↓
QLAdmin QuikGcoi (QLAdmin Help §7.93 — confirmed)
  quikplan.VARGP = 3
```

## 4.2 Source reader

| Item | Detail |
|------|--------|
| **Source files** | Same as QUIKCOI |
| **Reader** | **None** |
| **Already implemented?** | **No** |
| **Need new reader?** | **Yes** — shared `paagerat_ul_coi_loader.py`; filter `TYPE_CODE=U5` |
| **Schema** | **Confirmed** — QLAdmin Help §7.93 |

## 4.3 Transformation logic

Identical attained-age scalar emit as QUIKCOI except `TYPE_CODE=U5` → `QuikGcoi`.

**ISWL PAAGERAT U5 source counts:**

| Segment ID | Resolves to MPLAN | U5 rows |
|------------|-------------------|---------|
| `659 CEN II` | `1679CS` | 200 |

**Segmentation:** F/M, band 1, UWCLASS=SM only (2 tuples × 100 SEQ).

**Expected QuikGcoi output:** **~198–200 rows** (2 tuples × SEQ 100 cap handling).

**Gap:** 7/8 MPLANs have PSEGT U5 capability but no PAAGERAT U5 rows. SME/client confirmation for partial fleet emit.

## 4.4 Output mapping — QuikGcoi (confirmed)

QLAdmin Help §7.93 — index key: `PLAN + AGE + CNTL`. Same field layout as QuikCoi (`PLAN` C6).

| Output field | Type | Len | Source | Notes |
|--------------|------|-----|--------|-------|
| PLAN | C | 6 | Crosswalk | `1679CS` only for v1 |
| AGE | C | 2 | `SEQ` | Attained age; cap 99 |
| CNTL | C | 2 | Fixed | `"00"` |
| QX0 | C | 10 | `VALUE_INFO` | Authoritative rate |
| QX1–QX9 | C | 10 | — | **Blank** |
| GENDER, UWCLASS, BAND | C | — | PAAGERAT | Standard maps |
| ISSCNTRY, ISSUEST, EFFDATE | C/D | — | Config | Standard defaults |

## 4.5 Validation strategy

See [`ISWL_Validation_Strategy.md`](ISWL_Validation_Strategy.md) § QUIKGCOI.

## 4.6 Development complexity

**Medium** (incremental after QUIKCOI — same loader core, `TYPE_CODE=U5` filter)

**Expected files:**

- Extend `paagerat_ul_coi_loader.py` for U5 → `QuikGcoi`
- `qla_core/rate_dbf_schema.py` — add `QuikGcoi` layout
- `qla_core/rate_pipeline.py` — wire U5 stream
- `tools/validators/iswl_quikgcoi_reconcile.py` (new)

---

## Appendix A — PSEGT capability matrix (ISWL)

| SEGT_TYPE | QLAdmin target | PSEGT 8/8 | PAAGERAT ISWL rows |
|-----------|----------------|-----------|-------------------|
| CV | QUIKCVS | Yes | Rate_Table 72,271; PDAGE 12,084 |
| BP | QUIKGPS | Yes | 1,164 (4/8 parents) |
| U6 | QUIKCOI | Yes | 800 (2/8 parents) |
| U5 | QUIKGCOI | Yes | 200 (1/8 parent) |
| NC | — (not COI) | Yes | Do not load |
| PR | QuikGps (non-ISWL PR) | Rider slots | 328 waiver — not ISWL BP |

## Appendix B — rate_dbf_schema.py current routing

```python
TYPE_TO_TABLE = {"CV": "QuikCvs", "DB": "QuikDbs", "TV": "QuikTvs",
                 "NP": "QuikNps", "DV": "QuikDvs", "PR": "QuikGps"}
# U5, U6, BP excluded from Rate_Table stream — PAAGERAT path required
```

## Appendix C — Transform model comparison (ISWL)

| Target | Source | Grid model | One source row → |
|--------|--------|------------|------------------|
| QUIKCVS | Rate_Table / PDAGE | Issue age × duration (VARGP=2) | One duration cell; pivot 10 into CV0–CV9 |
| QUIKGPS | PAAGERAT BP | Attained age scalar (VARGP=3) | One row → GP0 only |
| QUIKCOI | PAAGERAT U6 | Attained age scalar (VARGP=3) | **One row → QX0 only** |
| QUIKGCOI | PAAGERAT U5 | Attained age scalar (VARGP=3) | **One row → QX0 only** |

**Withdrawn for ISWL U5/U6:** issue-age × duration pivot; ten-duration population of QX0–QX9; `VALUE_FLOAT` as rate source; schema-blocked status.

## Appendix D — authoritative research documents

- `Issue_Log_Items/Issue_31/Issue_31_Extract_Validation_Report.md`
- `docs/research/ISWL_Segment_Trace/ISWL_Segment_Trace_Addendum_20260629.md`
- `docs/research/ISWL_Implementation_Gap_Report.md`
- `docs/research/ISWL_Product_Book_Manual_Findings_Addendum.md`
