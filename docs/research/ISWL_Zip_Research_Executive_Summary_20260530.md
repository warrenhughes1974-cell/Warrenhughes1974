# ISWL ZIP Research Executive Summary — 20260530

**Update 2026-06-30:** PSEGT, PDINT, and PDINTTBL were **not in the May ZIP** but are now delivered separately (`20260629` extracts in `QLA_Migration/Source/`). See `Issue_31_PSEGT_PDINT_Followup_Report.md`.

**ZIP:** `C:\Users\warren\Downloads\LifePRO_Extracts_20260530 (1).zip`  
**Analyzed:** 2026-06-28 (streamed via `tools/research/iswl_zip_source_analysis_20260530.py`)  
**Method:** Python `zipfile` — no full archive extract (~1.49 GB compressed / 50.24 GB uncompressed, 125 files)

---

## 1. Was this ZIP already used in prior ISWL research?

**Partially — the complete ZIP was not previously analyzed.**

| Prior use | Detail |
|-----------|--------|
| **April rate extracts** | `Rate_Table_Extract_20260427.csv` and `PAAGERAT_Extract_20260428.csv` in `plan_analysis/source_data/rates/` drove QUIKCVS/COI research — **not from this ZIP** |
| **May policy subset** | ~12 files copied to `QLA_Migration/Source/` (PPBEN, PCOVR, PPOLC, etc.) used in Issue #21D forensic work |
| **This ZIP as a whole** | **First full inventory and ISWL-target analysis** |

---

## 2. What new files were found?

**113 of 125 ZIP files are not in the repo** (see `iswl_zip_vs_repo_source_comparison_20260530.csv`).

### Critical absence
- **`Rate_Table_Extract` is NOT in the May ZIP.** QUIKCVS research still depends on the separate April repo extract.

### Highest-value new sources (not in prior rate analysis)

| File | Size | ISWL relevance |
|------|------|----------------|
| `PDAGE_AgeDuration_Rates_Extract_20260530.csv` | 203 MB | **41,083 ISWL rows**; CV=12,084; TP/TX=2,128 each |
| `PDDIC_DataDictionary_Extract_20260530.csv` | 112 MB | Schema/metadata; COI/GCOI text but no TYPE_CODE lookup |
| `PDDICFLD_DataDictionaryField_Extract_20260530.csv` | 55 MB | Field definitions |
| `PRBEN_BenefitRates_Extract_20260530.csv` | 47 MB | Benefit-level rates |
| `PRBENINT_BenefitRatesINT_Extract_20260530.csv` | 5 MB | Interest rate candidate for QUIKUINT |
| `PAAGE_AttainedAge_Rates_Extract_20260530.csv` | 796 KB | Attained-age rate headers (41 ISWL rows) |
| `PPRDF_ProductInformation_Extract_20260530.csv` | 65 KB | Product-level setup |

May **`PAAGERAT_AttainedAge_Rates_Extract_20260530.csv`** matches April row counts (24,425 total; 3,287 ISWL) — confirms prior PAAGERAT findings on fresher extract date.

---

## 3. What findings changed?

| Prior finding | After ZIP analysis |
|---------------|-------------------|
| QUIKCVS from Rate_Table CV | **Strengthened** — PDAGE provides May-dated CV tables for all ISWL coverages despite Rate_Table absence |
| Rate_Table PR zero ISWL | **Confirmed** on both PAAGERAT and PDAGE |
| PAAGERAT NC/U6/BP meanings | **Still unknown** — PDDIC does not contain provable TYPE_CODE definitions |
| PPBEN FV_GUAR_RATE 4.50 | **Confirmed** (2,159 rows) |
| UV_CURR/UV_GUAR COI rates | **Confirmed unusable** (all zero) |
| QUIKISSC | **New candidate** — PDAGE TP/TX (inference only) |
| Senior plan rate gaps | **Strengthened** — PDAGE covers senior coverages where PAAGERAT is thin |
| Expenses | **Still unknown** |

---

## 4. QLAdmin target summary

| Target | Candidate ZIP source | ISWL evidence | Confidence |
|--------|---------------------|---------------|------------|
| **QUIKCVS** | PDAGE `TYPE_CODE=CV`; repo Rate_Table (April) | 12,084 ISWL CV rows in PDAGE | **High** for CV data existence; **Medium** for converter routing |
| **QUIKCOI** | PAAGERAT `TYPE_CODE=NC` | 690 ISWL rows; VALUE_INFO ~1.46–1.51 | **Medium** (inference — NC=COI unproven) |
| **QUIKGCOI** | PAAGERAT `TYPE_CODE=U6` | 800 ISWL rows (658 CEN I, 659 CEN II only) | **Medium** (inference) |
| **QUIKGPS** | PAAGERAT `TYPE_CODE=BP` | 1,164 ISWL rows; PR=0 | **Medium** (inference); PR disproven |
| **QUIKUINT** | PPBEN `FV_GUAR_RATE`; PRBENINT; CSO 4.50% | 2,159 rows @ 4.50% | **Supported** for guarantee; QUIKUINT field mapping **unknown** |
| **QUIKISSC** | PDAGE `TP`/`TX` | 2,128 ISWL rows each | **Low** — inference only |
| **Expenses** | PCOVR `POLICY_FEE`; PCOMP | No expense rate tables | **Unknown** |

Sample PDAGE CV row (`658 CEN I`, duration 2): VALUE1=11.0, VALUE2=14.0 … (per-$1,000 cash values by band).

Sample PAAGERAT NC row (`658 CEN I`): VALUE_INFO=1.4640000 (attained-age COI factor candidate).

---

## 5. What is still missing?

1. **Authoritative TYPE_CODE dictionary** — NC, U6, BP, TP, TX meanings not provable from PDDIC extracts.
2. **Rate_Table in May extract** — must reconcile April Rate_Table vs May PDAGE for QUIKCVS production cutover.
3. **QUIKISSC authoritative source** — TP/TX are candidates only.
4. **Expense charge tables** — monthly fee, % premium, per-thousand components not located.
5. **QUIKUINT schema mapping** — which LifePRO fields map to guaranteed vs credited vs loan rates in QLAdmin.
6. **User-requested MPLANs** (1668B1, 1669B2, 1678CS) and coverage IDs (668 CEN I, 678/679 CEN SEN) — **not present** in ISWL fleet data; only the eight proven coverage IDs appear.

---

## 6. What to request from client / SME

1. LifePRO **TYPE_CODE reference table** (what NC, U6, BP, TP, TX mean for UL/ISWL).
2. Confirmation whether **`PDAGE` CV** replaces **`Rate_Table` CV** for May 2026 production extracts.
3. Authoritative **surrender charge** source file or TYPE_CODE for ISWL.
4. **Expense/fee** setup location (policy fee, admin charge, % premium load).
5. **QUIKUINT** QLAdmin field spec for ISWL (guaranteed vs current credited vs loan rate).
6. Clarification why **`Rate_Table`** was omitted from the May ZIP bundle.

---

## 7. Implementation recommendation

**Remain blocked** for new UL table loaders (QUIKCOI, QUIKGCOI, QUIKGPS, QUIKUINT, QUIKISSC, Expenses) until TYPE_CODE meanings are confirmed by SME or a dictionary outside PDDIC is provided.

**May proceed** (with SME sign-off) on:
- QUIKCVS using existing Rate_Table path **or** PDAGE CV after parity validation against April Rate_Table values.
- QUIKUINT guaranteed rate using PPBEN `FV_GUAR_RATE=4.50` + CSO crosswalk — pending QUIKUINT column mapping.

---

## 8. Follow-up — 20260629 extracts (Issue #31)

**Update:** Client supplied `PSEGT`, `PDINT`, and `PDINTTBL` in `QLA_Migration/Source/` (not in May ZIP).

| Extract | Rows | Impact |
|---------|------|--------|
| PSEGT | 696 | Authoritative `SEGT_TYPE` mapping for all 8 ISWL coverages (U5/U6/BP/CV/A1/G1/LN/SR/SL/UF) |
| PDINT | 10 | Declared interest rules (8 IDENTs) |
| PDINTTBL | 37 | Rate schedules; `CENII` A1 = 4.50% from 2002 |

**Revised status:** Primary **source dependency resolved**; implementation gaps remain (PAAGERAT senior plans, QUIKISSC rate pointer, expense U1–U3). See `ISWL_Segment_Trace_Addendum_20260629.md`.

---

## Deliverables

All outputs under `docs/research/`:

| Task | Files |
|------|-------|
| Inventory | `iswl_zip_inventory_20260530.md`, `.csv` |
| Repo comparison | `iswl_zip_vs_repo_source_comparison_20260530.csv` |
| ISWL hits | `iswl_zip_relevant_file_hits_20260530.md`, `.csv` |
| Table profiles | `iswl_zip_table_profile_20260530.md`, `.csv` |
| Target analysis | `iswl_zip_target_source_analysis_20260530.md`, `.csv` |
| TYPE_CODE dictionary | `iswl_zip_type_code_dictionary_search_20260530.md` |
| Revalidation | `iswl_zip_prior_finding_revalidation_20260530.md` |
| Machine bundle | `iswl_zip_analysis_bundle_20260530.json` |

Reproducible script: `tools/research/iswl_zip_source_analysis_20260530.py`
