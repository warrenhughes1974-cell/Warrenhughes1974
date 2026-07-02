# ISWL Source Data Discovery Report

**Analysis date:** 2026-06-28  
**Scope:** Research / discovery only — no converter, rulebook, crosswalk, or DBF changes  
**Analyst:** Automated discovery against in-repo LifePRO extracts + existing Issue #21D / rate-pipeline artifacts

---

## 1. Executive summary

ISWL (Interest-Sensitive Whole Life) is identified in LifePRO by **eight coverage IDs** and **eight QLA MPLAN codes** (Issue #21D fleet: **2,268 policies**). The string `ISWL` does not appear in LifePRO extracts; identification is via PCOVR description *Interest-Sensitive Whole Life*, CSO crosswalk rows, and `qla_core/cso_mortality_crosswalk.py`.

| QLAdmin target | LifePRO source found? | Confidence | Primary candidate |
|----------------|----------------------|------------|-------------------|
| **QUIKUINT** (interest) | Partial | Medium | CSO crosswalk (plan 4.50%); PPBEN policy fields (not local) |
| **Expenses** | No | N/A | — |
| **QUIKCOI** | Candidate | Medium | PAAGERAT `TYPE_CODE=NC` |
| **QUIKGCOI** | Candidate | Medium | PAAGERAT `TYPE_CODE=U6` |
| **QUIKISSC** | No | N/A | — |
| **QUIKGPS** | Partial | Low–Medium | PAAGERAT `BP` and/or `iswl-prem.csv`; no Rate_Table `PR` |
| **QUIKCVS** | Yes | **High** | Rate_Table `TYPE_CODE=CV` |

**Bottom line:** Cash values are present and mappable via the existing WL rate pipeline (`CV → QuikCvs`). UL-specific tables (QUIKUINT, QUIKCOI, QUIKGCOI, QUIKISSC) lack confirmed LifePRO TYPE_CODE labels and **QLAdmin physical schemas are not documented in this repo**. Gross premium and expense data require business clarification. PFSA `iswl-prem.csv` must **not** be assumed equivalent to LifePRO extracts without explicit confirmation.

---

## 2. ISWL plan identification

### 2.1 Authoritative MPLAN ↔ LifePRO mapping

| QLA MPLAN | LifePRO COVERAGE_ID | Description |
|-----------|---------------------|-------------|
| `1658C1` | `658 CEN I` | Interest-Sensitive Whole Life |
| `1658CS` | `658 CEN SD` | Interest-Sensitive Whole Life |
| `1659C2` | `659 CEN II` | Interest-Sensitive Whole Life |
| `1659CR` | `659 CEN SR` | Interest-Sensitive Whole Life |
| `1659CS` | `659 CEN SD` | Interest-Sensitive Whole Life |
| `1659SR` | `659 SR GD` | Interest-Sensitive Whole Life |
| `1669SR` | `669 SR GD` | Interest-Sensitive Whole Life |
| `1679CS` | `679 CEN SD` | Interest-Sensitive Whole Life |

**Sources:** `plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv`, `qla_core/cso_mortality_crosswalk.py`, Issue #21D population.

### 2.2 Related but distinct codes (not ISWL fleet MPLAN)

| Code | Context |
|------|---------|
| `1205IS`, `120ISW` | PFSA interest plans in QUIKAINT trace — **not** in ISWL fleet allowlist |
| `MSP B2`, `FJV B2`, etc. | Row prefixes in `PFSA Rates/iswl-prem.csv` — gender/UW/band matrix labels, **not** QLA MPLAN codes |

---

## 3. Source file inventory

### 3.1 In-repo LifePRO / rate data

| Location | Contents |
|----------|----------|
| `plan_analysis/source_data/rates/` | Rate_Table, PAAGERAT, CSO crosswalk |
| `plan_analysis/source_data/coverage/` | PCOVR, PCOVRSGT |
| `plan_analysis/source_data/crosswalk/` | Policy Form Crosswalk (xlsx) |
| `PFSA Rates/iswl-prem.csv` | Business premium matrix (PFSA lineage) |

### 3.2 Expected but absent locally

| Location | Contents |
|----------|----------|
| `QLA_Migration/Source/` | PPOLC, PPBEN, PPBENTYP, monthly LifePRO extracts (gitignored) |
| `plan_analysis/source_data/reference_dbf/` | QLAdmin template DBFs (documented, not populated) |

---

## 4. Findings by QLAdmin target table

### 4.1 Interest values → QUIKUINT

| Required value | Candidate LifePRO source | Candidate columns | Grain | Confidence | Missing information |
|----------------|-------------------------|-------------------|-------|------------|---------------------|
| Guaranteed interest rate | `CSO_Mortiality_Crosswalk.csv` | `nfo_interest_source` (4.50%), `nfo_interest_code` (A) | Plan-level, all 8 ISWL plans | **High** (for plan NFO rate) | QUIKUINT field layout; whether NFOINT authority satisfies QUIKUINT governance rule |
| Guaranteed interest rate | `PPBEN_PolicyBenefit_Extract*.csv` | `FV_GUAR_RATE` | Policy-level | **Low** (extract absent) | Field populated for ISWL? Same as 4.50% CSO? |
| Current credited interest rate | `PPBEN` | `UV_CURR_COI_RATE` | Policy-level | **Low** | Name suggests COI not crediting; semantics unverified |
| Loan credited rate | `PLOAN` / `PCOVR` / `QuikPlSt` | TBD | Unknown | **Low** | No ISWL loan rate column identified |

**Note:** Issue #21D established **CSO crosswalk 4.50%** as authoritative for ISWL dividend accumulation display (`quikplan.NFOINT` + `quikdvdp.MDEPINT`). That path is **separate from QUIKUINT** table loading. Data governance (`QLA_Migration/Data_Goverence.txt`) requires UL plans to have a QUIKUINT record — ISWL may be classified as UL-like for this rule.

**Do not assume PFSA QUIKAINT behavior** (`1205IS` / annuity interest history) applies to ISWL MPLAN codes `1658C1`–`1679CS`; those codes are absent from `quikaint_emit_trace.csv`.

---

### 4.2 Expenses

| Required value | Candidate source | Confidence |
|----------------|-----------------|------------|
| Monthly expense per policy | **NOT FOUND** | N/A |
| Percent of premium expense | **NOT FOUND** | N/A |
| Monthly expense per $1,000 | **NOT FOUND** | N/A |

No expense TYPE_CODE in Rate_Table or PAAGERAT. QUIKAEXP appears in governance for **annuity** plans (`A` prefix), not confirmed for ISWL.

---

### 4.3 COI factors → QUIKCOI

| Required value | Candidate source | Columns | Grain | Confidence | Missing information |
|----------------|-----------------|---------|-------|------------|---------------------|
| Cost of insurance | `PAAGERAT` | `VALUE_INFO`, `SEQ`, `SEX`, `BAND`, `UWCLS` | Attained age (SEQ 2–86) × F/M × Band 1 × P/S | **Medium** | TYPE_CODE `NC` not confirmed = COI; QUIKCOI schema unknown |

**Sample (`658 CEN I`, NC, F/S):** SEQ 11–13 → VALUE_INFO 1.464–1.480 (per-thousand scale plausible for COI).

**Coverage gaps:** NC present for `658 CEN I`, `659 CEN II`, `679 CEN SD` only — **absent** for `658 CEN SD`, `659 CEN SR`, `659 SR GD`, `669 SR GD`.

---

### 4.4 Guaranteed COI → QUIKGCOI

| Required value | Candidate source | Columns | Grain | Confidence | Missing information |
|----------------|-----------------|---------|-------|------------|---------------------|
| Guaranteed COI | `PAAGERAT` | `VALUE_INFO`, `SEQ`, `SEX`, `BAND`, `UWCLS` | Attained age (SEQ 1–100) × F/M × Band 1 × P/S | **Medium** | TYPE_CODE `U6` not confirmed = GCOI; `U5` on 659 CEN II unexplained |

**Sample (`658 CEN I`, U6, F/P):** VALUE_INFO 0.1504100, 0.0672800, 0.0639600 (small decimal factors).

**Coverage:** U6 only on `658 CEN I` and `659 CEN II`. No U6 for other six ISWL plans.

---

### 4.5 Surrender charges → QUIKISSC

| Required value | Candidate source | Confidence |
|----------------|-----------------|------------|
| Surrender charge schedule | **NOT FOUND** | N/A |

No `SC`, `SUR`, or `ISSC` TYPE_CODE in Rate_Table or PAAGERAT for ISWL coverages. TP/TX rows on `659 CEN II` are **excluded** from WL rate conversion (business out-of-scope).

---

### 4.6 Gross premiums → QUIKGPS

| Required value | Candidate source | Columns | Grain | Confidence | Missing information |
|----------------|-----------------|---------|-------|------------|---------------------|
| Gross premium factors | `Rate_Table` TYPE `PR` | — | — | **N/A** | **Zero PR rows** for all ISWL coverages |
| Base/gross premium (candidate) | `PAAGERAT` TYPE `BP` | `VALUE_INFO`, `SEQ`, segments | Attained age × segment | **Medium-Low** | BP excluded from WL loader; not confirmed = GP |
| Premium matrix | `PFSA Rates/iswl-prem.csv` | Age columns × duration rows | Duration × issue age × 10 segments | **Low** | EXCLUDE in PFSA reconciliation; no MPLAN mapping |

**iswl-prem.csv structure:** 1,952 data rows; segments `MSP B2`, `FJV B2`, `MRN B1`, etc.; ages -2 through 99; ~121 durations per segment.

---

### 4.7 Cash values → QUIKCVS

| Required value | Candidate source | Columns | Grain | Confidence | Missing information |
|----------------|-----------------|---------|-------|------------|---------------------|
| Cash value factors | `Rate_Table` TYPE `CV` | `VALUE`, `AGE`, `DURATION`, `SEX`, `BAND`, `UNDERWRITING_CLASS` | Issue age × duration (1–95) × F/M × Band 1 × P/S | **High** | EFFDATE default; value-level reconciliation blocked (R3 plan-universe mismatch) |

**ISWL CV row counts (Rate_Table):**

| Coverage | MPLAN | CV rows |
|----------|-------|---------|
| 658 CEN I | 1658C1 | 18,124 |
| 658 CEN SD | 1658CS | 9,113 |
| 659 CEN II | 1659C2 | 9,678 |
| 659 CEN SR | 1659CR | 9,678 |
| 659 CEN SD | 1659CS | 9,288 |
| 659 SR GD | 1659SR | 9,700 |
| 669 SR GD | 1669SR | 2,340 |
| 679 CEN SD | 1679CS | 4,350 |

R3 reconciliation validated routing `658 CEN I` / `1658C1` / CV → `QuikCvs` (mapping logic correct; target DBF plan universe mismatch prevented value compare).

---

## 5. TYPE_CODE reference (ISWL-relevant)

### Rate_Table (issue-age × duration)

| TYPE_CODE | ISWL rows | WL loader status | QLA target hypothesis |
|-----------|-----------|------------------|----------------------|
| CV | ~89,271 | **In scope → QuikCvs** | QUIKCVS |
| NP | ~89,982 | In scope → QuikNps | (reserve family) |
| RV | ~89,982 | In scope → QuikTvs | (reserve family) |
| PR | 0 | Would → QuikGps | QUIKGPS — **missing** |
| TP, TX | ~39,560 | Excluded | Not QLA input |
| DB | 100 | In scope → QuikDbs | Death benefit (not requested) |

### PAAGERAT (attained-age)

| TYPE_CODE | ISWL rows | Loader status | QLA target hypothesis |
|-----------|-----------|---------------|----------------------|
| NC | 690 | Excluded | **QUIKCOI candidate** |
| U6 | 800 | Excluded | **QUIKGCOI candidate** |
| U5 | 200 | Excluded | Unknown (659 CEN II only) |
| BP | 1,164 | Excluded | **QUIKGPS candidate** |
| NF | 432 | Excluded | Out of scope |
| PR | 0 for ISWL | — | — |

**Value column:** Use `VALUE_INFO` (populated). `VALUE_FLOAT` is 0.0 for all sampled ISWL rows.

---

## 6. QLAdmin target schema status

| Table | Schema in repo? | Known grain (if documented) |
|-------|-----------------|------------------------------|
| QUIKCVS (`QuikCvs`) | **Yes** — `qla_core/rate_dbf_schema.py` | PLAN + AGE + CNTL + GENDER + UWCLASS + BAND + ISSCNTRY + ISSUEST + EFFDATE; CV0–CV9 |
| QUIKGPS (`QuikGps`) | **Yes** — same family | Same grid; GP0–GP9 |
| QUIKUINT | **No** | Referenced in governance only |
| QUIKCOI | **No** | — |
| QUIKGCOI | **No** | — |
| QUIKISSC | **No** | — |

---

## 7. Recommended next steps (research — not implementation)

1. **Extract LifePRO monthly package** into `QLA_Migration/Source/` and profile PPBEN `FV_GUAR_RATE` / `UV_*` fields for ISWL policies.
2. **Obtain LifePRO TYPE_CODE dictionary** — confirm NC, U6, U5, BP meanings for ISWL.
3. **Obtain QUIKUINT / QUIKCOI / QUIKGCOI / QUIKISSC schemas** from QLAdmin Help or reference DBFs.
4. **Business decision:** Authoritative gross premium source — LifePRO BP, `iswl-prem.csv`, or other.
5. **Locate surrender charge and expense** tables (may be outside current extract set).
6. **Pilot value reconciliation** for `1658C1` CV once populated QLAdmin rate DBFs exist for crosswalk plans.

---

## 8. Artifacts produced

| File | Purpose |
|------|---------|
| `ISWL_Source_Candidate_Files.csv` | Candidate file catalog with row counts and columns |
| `ISWL_QLA_Target_Mapping_Draft.csv` | Source-to-target mapping with confidence |
| `ISWL_Data_Gaps_and_Questions.md` | Open gaps and stakeholder questions |
| `ISWL_Structure_Validation_Report.md` | Dimensional consistency across rate families |
| `tools/research/iswl_source_discovery.py` | Repeatable analysis script (research only) |

---

*End of report*
