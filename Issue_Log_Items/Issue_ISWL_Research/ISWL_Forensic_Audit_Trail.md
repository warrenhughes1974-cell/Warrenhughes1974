# ISWL Forensic Audit Trail

**Date:** 2026-06-28  
**Purpose:** Reproduce and prove (or disprove) every ISWL discovery conclusion with file-level evidence  
**Scope:** Research validation only — no converter changes  
**Machine-readable evidence:** `ISWL_Forensic_Evidence.json` (regenerate via `python tools/research/iswl_forensic_evidence.py`)

---

## 10. Discovery methodology (read this first to reproduce)

### 10.1 Repository folders searched

| Path | Purpose |
|------|---------|
| `plan_analysis/source_data/rates/` | LifePRO rate extracts |
| `plan_analysis/source_data/coverage/` | PCOVR, PCOVRSGT |
| `plan_analysis/source_data/crosswalk/` | Policy Form Crosswalk |
| `QLA_Migration/Source/` | Monthly LifePRO policy extracts |
| `PFSA Rates/` | PFSA premium matrices |
| `PFSA Rates/reconciliation/` | PFSA plan↔CSV mapping drafts |
| `qla_core/` | Rate loader schema and CSO crosswalk |
| `plan_analysis/phase_r3_rate_reconciliation/` | CV routing proof |
| `plan_analysis/phase_r5_rate_loader/` | Excluded TYPE_CODE inventory |
| `Issue_Log_Items/Issue_21/Issue_21D/` | ISWL fleet / interest strategy |
| `_archive/old_research/` | Prior June 2026 discovery (not used as proof without re-validation) |

### 10.2 Searches performed

| Method | Query / pattern | Target |
|--------|-----------------|--------|
| Glob | `*ISWL*`, `*LifePRO*` | Filename discovery |
| Grep | `1658C1`, `658 CEN I`, `Interest-Sensitive` | Plan identity |
| Grep | `QUIKUINT`, `QUIKCOI`, `QUIKGCOI`, `QUIKISSC`, `QUIKAEXP` | QLA table references |
| Grep | `TYPE_TO_TABLE`, `EXCLUDED_TYPE` | Converter routing |
| Grep | `,SC,`, `,SUR,`, `,ISSC,`, `expense` | Surrender / expense negative search |
| Python CSV scan | Filter `COVERAGE_ID ∈ {8 ISWL forms}` | Row counts, TYPE_CODE inventory |
| Python CSV scan | `PPBEN` + `PLAN_CODE` trim (columns have trailing spaces) | Policy-level interest fields |

### 10.3 Scripts executed (2026-06-28)

```powershell
python tools/research/iswl_forensic_evidence.py
# Output: Issue_Log_Items/Issue_ISWL_Research/ISWL_Forensic_Evidence.json

python -c "<inline scans for TYPE_CODE inventory, PPBEN ISWL profile>"
```

### 10.4 Converter code inspected

| File | Lines | Finding |
|------|-------|---------|
| `qla_core/rate_dbf_schema.py` | 22–30 | `TYPE_TO_TABLE`: CV→QuikCvs, PR→QuikGps; `EXCLUDED_TYPE_CODES`: NN PN TP TX UF NF SL |
| `qla_core/rate_factor_loader.py` | 92–99 | Unmapped TYPE → status EXCLUDED |
| `qla_core/cso_mortality_crosswalk.py` | 54–57 | `ISWL_MPLAN_ALLOWLIST` (8 codes) |
| `qla_core/paagerat_pr_loader.py` | 50–71 | PAAGERAT loader filters **PR only** |
| `app.py` | 5618–5621 | `is_iswl_mplan()` sets `MDEPINT=4.50` on quikdvdp emit |
| `plan_analysis/phase_r3_rate_reconciliation/_reconcile.py` | 11–18 | Business-confirmed TYPE map |

### 10.5 Reports reviewed (supporting, re-validated against raw CSV)

- `Issue_Log_Items/Issue_ISWL_Research/ISWL_Source_Discovery_Report.md` (prior pass)
- `plan_analysis/phase_r3_rate_reconciliation/pilot_plan_reconciliation.md`
- `plan_analysis/phase_r5_rate_loader/emit_summary.json`
- `Issue_Log_Items/Issue_21/Issue_21D/Issue_21D_Interest_Rate_Strategy.md`

---

## Finding 1 — ISWL identity: eight MPLAN codes ↔ LifePRO coverage IDs

### Final classification: **PROVEN**

### 1. SOURCE FILE

| Attribute | Value |
|-----------|-------|
| **Filename** | `CSO_Mortiality_Crosswalk.csv` |
| **Full path** | `c:\Users\warren\Documents\GitHub\Warrenhughes1974\plan_analysis\source_data\rates\CSO_Mortiality_Crosswalk.csv` |
| **File type** | CSV (business-delivered crosswalk) |
| **Origin** | Actuarial / business crosswalk (not monthly LifePRO zip); documented in `qla_core/cso_mortality_crosswalk.py` line 49–51 |

Secondary source:

| Attribute | Value |
|-----------|-------|
| **Filename** | `Issue_21D_Interest_Rate_Population.csv` |
| **Full path** | `Issue_Log_Items/Issue_21/Issue_21D/Issue_21D_Interest_Rate_Population.csv` |
| **Origin** | Generated Issue #21D inventory from converted policy set |

### 2. HOW YOU DISCOVERED IT

1. Grep `Interest-Sensitive Whole Life` → CSO crosswalk rows 5–13, 47.
2. Read `qla_core/cso_mortality_crosswalk.py` → `ISWL_MPLAN_ALLOWLIST` explicit 8-code set.
3. Python count on `Issue_21D_Interest_Rate_Population.csv` → 2268 rows, 8 unique MPLAN values.
4. Cross-check `plan_analysis/phase_p3e_quikridr_authority_alignment/mplan_resolution_trace.csv` → rows like `658 CEN I,1658C1,1658C1,AUTHORIZED`.

### 3. SHOW THE EVIDENCE

**CSO crosswalk — all 8 ISWL rows (verbatim columns):**

```
658 CEN I,1658C1,...,Interest-Sensitive Whole Life,...,4.50%,NFOINT,A,...
658 CEN SD,1658CS,...,Interest-Sensitive Whole Life,...,4.50%,NFOINT,A,...
659 CEN II,1659C2,...,Interest-Sensitive Whole Life,...,4.50%,NFOINT,A,...
659 CEN SR,1659CR,...,Interest-Sensitive Whole Life,...,4.50%,NFOINT,A,...
659 CEN SD,1659CS,...,Interest-Sensitive Whole Life,...,4.50%,NFOINT,A,...
659 SR GD,1659SR,...,Interest-Sensitive Whole Life,...,4.50%,NFOINT,A,...
679 CEN SD,1679CS,...,Interest-Sensitive Whole Life,...,4.50%,NFOINT,A,...
669 SR GD,1669SR,...,Interest-Sensitive Whole Life,...,4.50%,NFOINT,A,...
```

**Code allowlist (`qla_core/cso_mortality_crosswalk.py` lines 54–57):**

```python
ISWL_MPLAN_ALLOWLIST = frozenset({
    "1658C1", "1658CS", "1659C2", "1659CR", "1659CS", "1659SR", "1669SR", "1679CS",
})
```

**Issue #21D population (Python 2026-06-28):**

- Data rows: **2268**
- Unique MPLAN: `1658C1, 1658CS, 1659C2, 1659CR, 1659CS, 1659SR, 1669SR, 1679CS`

**Sample policy row (`Issue_21D_Interest_Rate_Population.csv` line 13):**

```
010718309C,1658C1,658 CEN I,A,4,0.00,4.00,A,4.50%,4.50%,Dividend Accum Int Rate,4.00%,...
```

### 4. REASONING

The string `ISWL` does not appear as a LifePRO plan code. Identity is proven by:

- Business crosswalk labeling products **Interest-Sensitive Whole Life**
- One-to-one `lifepro_coverage_id` ↔ `qla_plan_code` for eight forms
- Fleet inventory uses exactly those eight MPLAN codes across 2268 policies

### 5. CONFIDENCE

**PROVEN** — three independent artifacts (CSO CSV, Python allowlist, Issue #21D inventory) agree on the same eight pairs. No inference required for identity.

### 6. ASSUMPTIONS

None for plan identity.

### 7. CROSS REFERENCES

- `qla_core/cso_mortality_crosswalk.py`
- `Issue_21D_Validation_Dependencies.md` (rule A-V1 lists same 8 MPLAN)
- `plan_governance/staged/emit_test/quikplan.csv` line 47 (`1658C1,...INTEREST-SENSITIVE WHOLE LIFE`)

### 8. SOURCE PROVENANCE

CSO file: business-delivered actuarial crosswalk (April 2026 refresh in repo). Issue #21D CSV: converter-derived inventory.

### 9. NEGATIVE SEARCHES

- Grep `ISWL` in LifePRO `Rate_Table` / `PAAGERAT` `COVERAGE_ID` → **no matches** (product name is in description, not ID)
- This does **not** invalidate ISWL identity; it explains why text search for "ISWL" fails

---

## Finding 2 — QUIKCVS ← Rate_Table TYPE_CODE = CV

### Final classification: **PROVEN** (source data + converter routing); value reconciliation **UNKNOWN**

### 1. SOURCE FILE

| Attribute | Value |
|-----------|-------|
| **Filename** | `Rate_Table_Extract_20260427.csv` |
| **Full path** | `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv` |
| **File type** | CSV — LifePRO rate table extract |
| **Origin** | Historical/client LifePRO rate extract (dated 20260427 in filename); consolidated under `plan_analysis/source_data/` per `plan_analysis/source_data/README.md` |

### 2. HOW YOU DISCOVERED IT

1. Read `qla_core/rate_dbf_schema.py` → `TYPE_TO_TABLE["CV"] = "QuikCvs"`.
2. Python filter `COVERAGE_ID ∈ ISWL_COV` → count TYPE_CODE frequencies.
3. Read `plan_analysis/phase_r3_rate_reconciliation/rate_reconciliation_report.csv` line 377+ → `658 CEN I,1658C1,CV,QuikCvs,...`.

### 3. SHOW THE EVIDENCE

**File dimensions (forensic JSON 2026-06-28):**

- Total data rows: **1,128,985**
- ISWL data rows: **251,950**
- ISWL `PR` rows: **0**
- ISWL CV row total: **72,271**

**ISWL CV rows per coverage (from `iswl_type_counts` in forensic JSON):**

| COVERAGE_ID | CV rows |
|-------------|---------|
| 658 CEN I | 18,124 |
| 658 CEN SD | 9,113 |
| 659 CEN II | 9,678 |
| 659 CEN SR | 9,678 |
| 659 CEN SD | 9,288 |
| 659 SR GD | 9,700 |
| 669 SR GD | 2,340 |
| 679 CEN SD | 4,350 |

**Sample records — `658 CEN I`, TYPE `CV` (forensic JSON):**

| AGE | SEX | BAND | UW | DURATION | VALUE |
|-----|-----|------|----|----------|-------|
| 0 | F | 1 | P | 1 | .0000000 |
| 0 | F | 1 | P | 2 | 1.0000000 |
| 0 | F | 1 | P | 3 | 3.0000000 |

**R3 reconciliation routing (actual CSV lines 377–379):**

```
658 CEN I,1658C1,CV,QuikCvs,F,01,PR,1,0,.0000000,,PLAN_NOT_IN_TARGET,,
658 CEN I,1658C1,CV,QuikCvs,F,01,PR,2,1,1.0000000,,PLAN_NOT_IN_TARGET,,
658 CEN I,1658C1,CV,QuikCvs,F,01,PR,3,2,3.0000000,,PLAN_NOT_IN_TARGET,,
```

Interpretation: transform maps LifePRO DURATION 1→QL duration 0, SEX F, BAND 1→01, UW P→PR. `PLAN_NOT_IN_TARGET` means supplied reference DBFs lacked plan `1658C1` — routing logic still executed.

**Columns in extract:**

```
COVERAGE_ID, TYPE_CODE, AGE, SEX, BAND, UNDERWRITING_CLASS, DURATION, VALUE
```

### 4. REASONING

- `CV` is business-confirmed cash value family in `TYPE_TO_TABLE`.
- Rows carry **issue age**, **duration**, **segmentation** (SEX/BAND/UW), and **VALUE** — same grain as `QuikCvs` (PLAN+AGE+CNTL+GENDER+UWCLASS+BAND+…+CV0–CV9) documented in `rate_dbf_schema.py`.
- All eight ISWL coverages have CV rows → not limited to one pilot plan.

### 5. CONFIDENCE

**High for mapping path** because:

- Direct LifePRO production-style extract (not PFSA)
- Converter already implements CV→QuikCvs (`rate_factor_loader.py`)
- R3 proves deterministic routing for `658 CEN I`

**Value match unverified** because reference DBFs did not contain plan `1658C1` (R3 blocker documented in `pilot_plan_reconciliation.md`).

### 6. ASSUMPTIONS

- **INFERENCE ONLY — NOT VERIFIED:** Default `EFFDATE=19000101`, `ISSCNTRY=0000`, `ISSUEST=00` acceptable for ISWL (loader config in `rate_dbf_schema.py` line 41).

### 7. CROSS REFERENCES

- `qla_core/rate_dbf_schema.py` lines 22–24
- `qla_core/rate_factor_loader.py` lines 92–99
- `plan_analysis/phase_r3_rate_reconciliation/_reconcile.py` lines 11–18
- `plan_analysis/phase_r4_loader_architecture/rate_factor_capacity_analysis.csv` — `1658C1,CV,18124,...`

### 8. SOURCE PROVENANCE

LifePRO `Rate_Table` extract dated **2026-04-27** in filename; stored in repo for rate-loader phases R3–R5. Not generated by converter.

### 9. NEGATIVE SEARCHES

- Searched ISWL `PR` in same file → **0 rows** (see Finding 4).
- Searched alternate CV source in PAAGERAT for ISWL → CV exists globally (1435 rows) but ISWL CV primary bulk is Rate_Table.

### Converter usage

| Status | Location |
|--------|----------|
| **Already used** | `qla_core/rate_factor_loader.py` — IN_SCOPE when `typ=="CV"` |
| **Already used** | `qla_core/rate_pipeline.py` — emits QuikCvs family |
| **Validated read-only** | `plan_analysis/phase_r3_rate_reconciliation/_reconcile.py` |

---

## Finding 3 — QUIKCOI ← PAAGERAT TYPE_CODE = NC

### Final classification: **SUPPORTED** (data exists) / **INFERRED** (NC = COI label)

### 1. SOURCE FILE

| Attribute | Value |
|-----------|-------|
| **Filename** | `PAAGERAT_AttainedAge_Rates_Extract_20260428.csv` |
| **Full path** | `plan_analysis/source_data/rates/PAAGERAT_AttainedAge_Rates_Extract_20260428.csv` |
| **Origin** | LifePRO attained-age rate extract (20260428) |

### 2. HOW YOU DISCOVERED IT

1. Listed all `TYPE_CODE` in PAAGERAT (Python) → includes `NC`, `U6`, `BP`, not `COI`.
2. Filter ISWL coverages → NC rows on 658 CEN I, 659 CEN II, 679 CEN SD only.
3. Compared value magnitudes: NC ~1.4–2.8 vs U6 ~0.06–0.15 → different factor families.
4. Prior hypothesis from `_archive/old_research/ISWL_Discovery_Summary.md` — **re-validated against raw rows**, not accepted on faith.

### 3. SHOW THE EVIDENCE

**Global PAAGERAT TYPE_CODE inventory (Python 2026-06-28):**

```
PR:14958 PU:1755 CV:1435 BP:1336 NP:950 RV:820 U6:800 NC:690 DB:628 NF:508 U5:417 YP:117 RD:10
```

**ISWL NC row counts:**

| COVERAGE_ID | NC rows |
|-------------|---------|
| 658 CEN I | 294 |
| 659 CEN II | 330 |
| 679 CEN SD | 66 |
| 658 CEN SD | **0** |
| 659 SR GD | **0** |
| 669 SR GD | **0** |

**Sample rows — `658 CEN I`, NC (forensic JSON):**

| SEX | BAND | UWCLS | SEQ | VALUE_INFO | VALUE_FLOAT |
|-----|------|-------|-----|------------|-------------|
| F | 1 | S | 11 | 1.4640000 | 0.0 |
| F | 1 | S | 12 | 1.4720000 | 0.0 |
| F | 1 | S | 13 | 1.4800000 | 0.0 |

**Critical data quality note:** Authoritative numeric is **`VALUE_INFO`**, not `VALUE_FLOAT` (always `0.0` in samples).

**Hex key decode (`AAGE_KEY0` for first NC sample):** contains substring `NC` + gender + seq — attained-age index encoded in `SEQ`.

### 4. REASONING

- Attained-age factors (SEQ axis) match typical UL **COI table grain** (age × gender × UW × band).
- No `COI` literal TYPE_CODE exists anywhere in either extract.
- NC is the **only** ISWL-attained-age TYPE with per-thousand-scale values alongside U6 decimal factors on same plans → NC = current charge, U6 = guaranteed charge is **plausible** but **not documented**.

### 5. CONFIDENCE

**Medium — structure only:**

- Data is from LifePRO PAAGERAT extract ✓
- Dimensions consistent ✓
- TYPE label `NC` **not confirmed** in LifePRO dictionary ✗
- QUIKCOI schema **not in repo** ✗
- Incomplete plan coverage (3 of 8 plans) ✗

### 6. ASSUMPTIONS

- **INFERENCE ONLY — NOT VERIFIED:** `NC` = Net Cost / Cost of Insurance.
- **INFERENCE ONLY — NOT VERIFIED:** `SEQ` = attained age (supported by filename `AttainedAge_Rates` and PAAGERAT loader design for PR).
- **INFERENCE ONLY — NOT VERIFIED:** NC maps to QUIKCOI (table never referenced in Python converter).

### 7. CROSS REFERENCES

- `plan_analysis/phase_r5_rate_loader/emit_summary.json` — `"NC": {"rows": 690, "distinct_coverage_ids": 3}` under excluded types
- `plan_analysis/phase_r2_rate_physical_structure/rate_loader_implementation_plan.md` — lists PAAGERAT TYPE vocabulary including NC

### 8. SOURCE PROVENANCE

LifePRO extract dated **2026-04-28**; consolidated in `plan_analysis/source_data/rates/`.

### 9. NEGATIVE SEARCHES

| Search | Result |
|--------|--------|
| `TYPE_CODE=COI` in Rate_Table | **Not in unique set** `{CV,DB,DV,NF,NN,NP,PN,PR,RV,SL,TP,TX,UF}` |
| `TYPE_CODE=COI` in PAAGERAT | **Not in unique set** |
| NC on `659 SR GD`, `669 SR GD` | **0 rows** |

### Converter usage

| Status | Evidence |
|--------|----------|
| **Never referenced for NC** | `TYPE_TO_TABLE` has no NC entry (`rate_dbf_schema.py` line 22–23) |
| **Excluded at load** | `rate_factor_loader.py` line 96–98: unmapped → EXCLUDED |
| **PAAGERAT loader** | `paagerat_pr_loader.py` line 52: filters **`PR` only**, not NC |

---

## Finding 4 — QUIKGCOI ← PAAGERAT TYPE_CODE = U6

### Final classification: **SUPPORTED** (data on 2 plans) / **INFERRED** (U6 = guaranteed COI)

### 3. SHOW THE EVIDENCE

**ISWL U6 counts:**

| COVERAGE_ID | U6 rows |
|-------------|---------|
| 658 CEN I | 400 |
| 659 CEN II | 400 |
| All other ISWL | **0** |

**Sample — `658 CEN I`, U6:**

| SEX | UWCLS | SEQ | VALUE_INFO |
|-----|-------|-----|------------|
| F | P | 1 | .1504100 |
| F | P | 2 | .0672800 |
| F | P | 3 | .0639600 |

**Related TYPE on `659 CEN II` only:** `U5` = 200 rows (meaning **unknown**).

### 4–6. REASONING / CONFIDENCE / ASSUMPTIONS

Same structure as NC but smaller decimal magnitudes → **candidate guaranteed COI**.

- **INFERENCE ONLY — NOT VERIFIED:** U6 = guaranteed COI.
- **Unable to verify from available source data:** QUIKGCOI target schema.
- **PROVEN gap:** six of eight ISWL plans have **zero** U6 rows.

### Converter usage: **Never referenced** (same exclusion path as NC).

---

## Finding 5 — QUIKGPS ← PAAGERAT BP and/or PFSA iswl-prem.csv

### Final classification: **UNKNOWN for authoritative source** — multiple partial candidates

### 5A. LifePRO Rate_Table PR

**Evidence (PROVEN ABSENCE for ISWL):**

```
Rate_Table global PR rows: 10,134
Rate_Table ISWL PR rows: 0
```

Python forensic script `iswl_pr_rows: 0`.

### 5B. PAAGERAT BP

**Evidence (data exists, mapping inferred):**

ISWL BP rows total **1,164** across six coverages; **zero** on `659 SR GD`, `669 SR GD`.

Sample `658 CEN I` BP:

```
SEX=F, BAND=1, UWCLS=P, SEQ=2, VALUE_INFO=1.7400000
SEX=F, BAND=1, UWCLS=P, SEQ=3, VALUE_INFO=1.7500000
```

**Converter:** BP is **not** in `TYPE_TO_TABLE`; R5 `emit_summary.json` lists BP under excluded types (1336 rows).

### 5C. PFSA iswl-prem.csv

| Attribute | Value |
|-----------|-------|
| **Path** | `PFSA Rates/iswl-prem.csv` |
| **Origin** | **PFSA artifact** (not LifePRO monthly extract) |

**Evidence:**

- Data rows: **1,951**
- Segments: 16 (`MSP B2`×121, `MRN B1`×122, …)
- Header ages: `-2` through `99`
- Sample row 2 (truncated): `MSP B2 1,1,0,0,...,5.18,5.33,...,10.76,...`

**Exclusion proof (`PFSA Rates/reconciliation/plan_csv_mapping_DRAFT.csv` line 31):**

```
iswl-prem.csv,EXCLUDE,,user: skip
```

**Column legend note (`column_legend_DRAFT.csv` line 30):**

```
MSP B2 n (iswl/spul row prefix), iswl,spul, ..., note: iswl/spul are duration x age matrices - confirm these are PREMIUM not cash value
```

### ASSUMPTIONS

- **INFERENCE ONLY — NOT VERIFIED:** BP = base/gross premium.
- **INFERENCE ONLY — NOT VERIFIED:** `iswl-prem.csv` applies to all eight MPLAN codes (no MPLAN column in file).

### Converter usage

| Source | Status |
|--------|--------|
| Rate_Table PR→QuikGps | Used for **non-ISWL** products; ISWL has 0 PR rows |
| PAAGERAT PR | `paagerat_pr_loader.py` — **PR only**; ISWL has 0 PR rows in PAAGERAT |
| iswl-prem.csv | **Never referenced** in `qla_core/` or `app.py` (grep confirms only PFSA/archive paths) |

---

## Finding 6 — QUIKUINT ← CSO crosswalk / PPBEN

### Final classification: **PROVEN** plan rate 4.50% in CSO; **SUPPORTED** PPBEN `FV_GUAR_RATE`; **DISPROVEN** PPBEN `UV_*` as credited rate in May 2026 extract

### 6A. CSO crosswalk (plan-level)

See Finding 1 evidence — all eight plans: `nfo_interest_source=4.50%`, `nfo_interest_code=A`.

**Converter usage:** `load_cso_mortality_crosswalk()` → `quikplan.NFOINT` in `app.py` (~line 5161). This is **not** QUIKUINT table load — **no code reference to QUIKUINT found in `qla_core/` or `app.py` grep**.

### 6B. PPBEN (policy-level) — **corrected 2026-06-28**

Prior research stated PPBEN was absent locally. **Re-validation shows `QLA_Migration/Source/` contains May 2026 extracts** (12 files including `PPBEN_PolicyBenefit_Extract_20260530.csv`).

**Discovery path:**

1. List `QLA_Migration/Source/` → 12 files present.
2. Initial Python failed: column name is `PLAN_CODE ` (**trailing space**).
3. Re-run with stripped headers.

**Evidence:**

```
PPBEN total rows: 11,699
ISWL PLAN_CODE rows: 4,550
Unique policies with FV_GUAR_RATE=4.50: 2,159
```

**FV_GUAR_RATE distribution on ISWL rows:**

| Value | Row count |
|-------|-----------|
| `.00` | 2,391 |
| `4.50` | 2,159 |

**UV_GUAR_COI_RATE on ISWL rows:** `.00000` → **4,550 rows (100%)**  
**UV_CURR_COI_RATE on ISWL rows:** `.00000` → **4,550 rows (100%)**

**Sample rows:**

```
PLAN_CODE=659 CEN II, POLICY=9010713704, BENEFIT_SEQ=1, FV_GUAR_RATE=.00
PLAN_CODE=659 CEN II, POLICY=9010713704, BENEFIT_SEQ=3, FV_GUAR_RATE=4.50
```

Pattern: base benefit seq often `.00`; fund/UV benefit seq carries `4.50`.

**ISWL PPBEN rows by plan:**

```
659 CEN II: 3422
659 CEN SR: 645
658 CEN I: 438
659 CEN SD: 15
658 CEN SD: 13
659 SR GD: 13
669 SR GD: 2
679 CEN SD: 2
```

### REASONING for QUIKUINT

- Data governance line 157 requires UL plans to have **QUIKUINT** record — documentation only.
- CSO + PPBEN both show **4.50%** guaranteed on authoritative rows — aligns with Issue #21D client rule.
- **Unable to verify from available source data:** which field populates which QUIKUINT column (schema missing).

### ASSUMPTIONS

- **INFERENCE ONLY — NOT VERIFIED:** `FV_GUAR_RATE` maps to QUIKUINT guaranteed rate (field exists; mapping not in converter).
- **DISPROVEN in May 2026 extract:** `UV_CURR_COI_RATE` as current credited rate (all zero for ISWL).

### Governance reference (`QLA_Migration/Data_Goverence.txt` line 157):

```
IF THE PLAN CODE IS A UL (TRANSFORATION NOTE) THERE MUST BE A RECORD IN QUIKUINT.
```

---

## Finding 7 — QUIKISSC: Not Found

### Final classification: **UNKNOWN** (proven absent in searched rate extracts)

### 9. NEGATIVE SEARCHES (full workpaper)

**Files searched:**

1. `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv`
2. `plan_analysis/source_data/rates/PAAGERAT_AttainedAge_Rates_Extract_20260428.csv`
3. `plan_analysis/source_data/coverage/PCOVR.csv` (column name scan)
4. Grep entire `plan_analysis/source_data/rates/` for `,SC,`, `,SUR,`, `,ISSC,` → **zero matches**

**Terms searched:** `SC`, `SUR`, `ISSC`, `SURRENDER`, `surrender`, `COI`, `GCOI`, `EXP`

**Rate_Table complete TYPE_CODE set:**

```
CV, DB, DV, NF, NN, NP, PN, PR, RV, SL, TP, TX, UF
```

No SC/SUR/ISSC globally or on ISWL filter.

**PAAGERAT complete TYPE_CODE set:**

```
BP, CV, DB, NC, NF, NP, PR, PU, RD, RV, U5, U6, YP
```

**TP/TX on ISWL (`659 CEN II` only):** 19,780 rows each — classified **out-of-scope** in `EXCLUDED_TYPE_CODES` and R3 excluded inventory (`excluded_type_code_inventory.csv`: TP, TX listed as not converted). **Not treated as surrender charge without dictionary proof.**

**What is missing:** Any LifePRO table whose TYPE_CODE or column name explicitly identifies surrender charge schedules for ISWL.

---

## Finding 8 — Expenses: Not Found

### Final classification: **UNKNOWN**

**Files searched:** Same rate extracts + PCOVR column scan.

**PCOVR interest/expense-like columns (Python header scan):**

```
INT_CR_RULE, MDV_MATURE_EXPIRE, PREM_CEASE_POINT, BEN_CEASE_POINT, EXPANSION_FLG
```

`EXPANSION_FLG` is not an expense charge field.

**QUIKAEXP reference:** `Data_Goverence.txt` line 155 — applies to plans **beginning with A** (annuity), not ISWL MPLAN `1658C1` etc.

**No EXP TYPE_CODE** in Rate_Table or PAAGERAT unique sets.

---

## 12. Evidence matrix

See **`ISWL_Forensic_Evidence_Matrix.csv`** in this folder (importable).

---

## 13. Final classification summary

| Conclusion | Classification |
|------------|----------------|
| Eight MPLAN ↔ LifePRO coverage IDs | **PROVEN** |
| 2,268 ISWL policy fleet (8 MPLAN) | **PROVEN** (Issue #21D inventory) |
| QUIKCVS ← Rate_Table CV | **PROVEN** (source + converter); value match **UNKNOWN** |
| QUIKGPS ← Rate_Table PR for ISWL | **UNKNOWN** — **0 rows PROVEN** |
| QUIKGPS ← PAAGERAT BP | **SUPPORTED** data / **INFERRED** mapping |
| QUIKGPS ← iswl-prem.csv | **INFERRED** — PFSA artifact, EXCLUDE in mapping |
| QUIKCOI ← PAAGERAT NC | **SUPPORTED** data / **INFERRED** NC=COI |
| QUIKGCOI ← PAAGERAT U6 | **SUPPORTED** on 2 plans / **INFERRED** U6=GCOI |
| QUIKUINT ← CSO 4.50% | **PROVEN** rate value / **UNKNOWN** QUIKUINT field mapping |
| QUIKUINT ← PPBEN FV_GUAR_RATE | **SUPPORTED** — 2159 rows at 4.50 |
| QUIKUINT ← PPBEN UV_CURR_COI_RATE | **DISPROVEN** in May 2026 extract (all .00000) |
| QUIKISSC | **UNKNOWN** — proven absent in rate extracts searched |
| Expenses | **UNKNOWN** — proven absent in rate extracts searched |

---

## Reproduction checklist for another engineer

```powershell
cd c:\Users\warren\Documents\GitHub\Warrenhughes1974

# 1. Regenerate machine evidence
python tools/research/iswl_forensic_evidence.py

# 2. TYPE_CODE inventories
python -c "import csv; from collections import Counter; ..."

# 3. PPBEN ISWL profile (note PLAN_CODE trailing space in DictReader — use strip)
python -c "... see Section 6B commands in this repo's chat log ..."

# 4. Confirm converter maps
rg "TYPE_TO_TABLE|EXCLUDED_TYPE" qla_core/rate_dbf_schema.py
rg "is_iswl_mplan" app.py

# 5. Confirm PFSA exclusion
type "PFSA Rates\reconciliation\plan_csv_mapping_DRAFT.csv" | findstr iswl
```

---

*End of forensic audit trail*
