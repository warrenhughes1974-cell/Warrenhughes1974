# Issue #80 — Planning Report

**Issue:** #80 — CSO Valuation Setup → exact QuikPlCv / QuikPlTv (plan + rate keys)  
**Framework stage:** Planning Agent  
**Status:** Ready for Risk Review (G2 PASSED)  
**Generated:** 2026-07-17  
**Updated:** 2026-07-17 (user answers locked; PUA → #81/#82)  
**Model:** Cursor Grok 4.5 (locked)  
**Authority file:** `docs/Valuation_Setup.xlsx`  
**Scope:** `Issue_80_Scope_Decisions.md` (51 non-PUA plans)  
**Evidence:** `evidence/cso_valuation_setup_as_delivered.csv`, `evidence/cso_valuation_setup_code_map.md`, `evidence/cso_valuation_setup_coded_expected.csv`  
**Open questions:** answered — see `Issue_80_Open_Business_Questions.md`

---

## 1. Executive Finding

CSO’s `Valuation_Setup.xlsx` is the authoritative specification for Cash Value and Reserve assumption fields on **QuikPlCv** and **QuikPlTv** (and the matching `quikplan` NFOINT/INTMETHCV path). Current emit leaves most QuikPlTv assumption cells blank, and the older `CSO_Mortiality_Crosswalk.csv` disagrees with this workbook on NFOINT for many plans (e.g. CSI 5.75%→4.50%, L10/L14/L17 5.00%→4.50%).  

**Direction:** Build (or extend) a CSO valuation-setup loader that writes **only** workbook-backed values into QuikPlCv / QuikPlTv / quikplan — exact match, blanks stay blank.  

**Go/no-go for Risk:** Planning complete; Dependency Gate expected **BLOCKED** until CSO confirms QLAdmin short-code mappings and fills missing QLA Plan rows. No Development until G2 + G3.

**Scope boundary:** CSO / QLA Migration plan+rate path only. **Not** `Citizens_Product_Rate_Conversion/`.

---

## 2. Confirmed Source (CSO deliverable)

| Source | File | In repo? | Rows |
|--------|------|----------|-----:|
| CSO Valuation Setup | `docs/Valuation_Setup.xlsx` (Sheet1) | Yes | 65 |
| Normalized as-delivered | `Issue_80/evidence/cso_valuation_setup_as_delivered.csv` | Yes | 65 |
| Prior CSO mortality crosswalk (supersede on conflict) | `plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv` | Yes | 51 |

### Workbook fields (verbatim headers)

| Field | Meaning |
|-------|---------|
| LifePRO Plan | LifePRO coverage / form id |
| QLA Plan | QLAdmin `PLAN` |
| Description | Product description |
| QuikPlCv MORT | Mortality table code (e.g. A1, O1, N1) |
| QuikPlCv ETIMORT | ETI mortality (e.g. C1, Q1, or prose `1941 CET 2.5% NLP`) |
| QuikPlCv NFOINT | NFO interest as **decimal rate** (e.g. 0.045 = 4.50%) |
| QuikPlCv INTMETHCV | Interest method label (`Curtate` on all 65 rows) |
| QuikPlTv (all 5 fields) | Single prose string encoding reserve assumptions |

### Parsed QuikPlTv prose pattern (all rows)

```
Rsv Int: {pct}%, Rsv Mthd: {CRVM|NLP}, Curtate, Store Means: Default (Terminal), Calc Mids: Default (Mean)
```

One row (`647 FLP`) inserts a `Missing:` token before Store Means — treat as still Default Terminal/Mean unless CSO says otherwise.

---

## 3. Confirmed QLAdmin Target Structure

From `qla_core/rate_dbf_schema.py`:

| Table | Field | Type | Len | Workbook source |
|-------|-------|------|----:|-----------------|
| QuikPlCv | MORT | C | 2 | Col D |
| QuikPlCv | ETIMORT | C | 2 | Col E (needs code when prose) |
| QuikPlCv | NFOINT | C | 1 | Col F decimal → **1-char code** |
| QuikPlCv | INTMETHCV | C | 1 | Col G `Curtate` → code (existing: `0`) |
| QuikPlTv | MORT | C | 2 | Col D (same as CV) |
| QuikPlTv | RSVINT | C | 1 | Col H “Rsv Int” → **1-char code** |
| QuikPlTv | RSVMETH | C | 1 | Col H “Rsv Mthd” CRVM/NLP → code |
| QuikPlTv | INTMETHTV | C | 1 | Col H “Curtate” → code |
| QuikPlTv | STOREMEANS | L | 1 | Col H “Store Means: Default (Terminal)” |
| QuikPlTv | CALCMIDS | L | 1 | Col H “Calc Mids: Default (Mean)” |
| quikplan | NFOINT | (schema) | | Same as QuikPlCv NFOINT code |
| quikplan | INTMETHCV | (schema) | | Same as QuikPlCv INTMETHCV |

**“All 5 fields” interpretation (Planning lock pending CSO confirm):**  
`RSVINT`, `RSVMETH`, `INTMETHTV`, `STOREMEANS`, `CALCMIDS` — not including MORT (MORT is column D on both key tables).

### Repo population paths (read-only)

| Location | Role today |
|----------|------------|
| `qla_core/cso_mortality_crosswalk.py` | Loads old CSV; applies quikplan NFOINT/INTMETHCV; CV fields only |
| `qla_core/rate_key_setup.CSOAssumptionProvider` | Feeds QuikPlCv MORT/ETIMORT/NFOINT/INTMETHCV; **leaves QuikPlTv reserve fields blank** |
| `QLA_Migration/Output/rates/QuikPlCv.csv` / `QuikPlTv.csv` | Current emit — many assumption blanks |
| `Citizens_Product_Rate_Conversion/` | **Do not touch** |

---

## 4. Required Source-to-Target Field Mapping

| CSO Valuation_Setup | QLAdmin target | Transformation | Change? |
|---------------------|----------------|----------------|---------|
| QLA Plan | QuikPlCv/Tv `PLAN` | Exact plan key match | Join key |
| QuikPlCv MORT | QuikPlCv.MORT + QuikPlTv.MORT | As written when ≤2 chars | Yes |
| QuikPlCv ETIMORT | QuikPlCv.ETIMORT | As written when ≤2 chars; prose → CSO code | Yes |
| QuikPlCv NFOINT (decimal) | QuikPlCv.NFOINT + quikplan.NFOINT | Rate → C1 interest code | Yes |
| QuikPlCv INTMETHCV | QuikPlCv.INTMETHCV + quikplan.INTMETHCV | `Curtate` → loadable code | Yes |
| QuikPlTv Rsv Int | QuikPlTv.RSVINT | Rate% → C1 code | Yes |
| QuikPlTv Rsv Mthd | QuikPlTv.RSVMETH | CRVM/NLP → C1 code | Yes |
| QuikPlTv Curtate | QuikPlTv.INTMETHTV | Curtate → C1 code | Yes |
| QuikPlTv Store Means | QuikPlTv.STOREMEANS | Default (Terminal) → L1 | Yes |
| QuikPlTv Calc Mids | QuikPlTv.CALCMIDS | Default (Mean) → L1 | Yes |
| Blank workbook cell | Same target field | Remain blank — **never invent** | Yes |

### Fields that must remain unchanged

| Target | Touch this issue? |
|--------|-------------------|
| Factor grids QuikCvs / QuikTvs / QuikNps / QuikGps / … | **No** (assumptions on keys only) |
| `quikridr` PUA phase rules (#60 Track A) | **No** |
| MPOLICY padding (#25) / MPREM (#26) | **No** |
| Citizens / CFIC rate packages | **No** |
| Plans **not** listed in Valuation_Setup | **No** (leave current behavior) |

### Conflict rule (Planning recommendation)

For any PLAN present in Valuation_Setup, **Valuation_Setup wins** over `CSO_Mortiality_Crosswalk.csv`. Old crosswalk remains only for plans not in the new file (currently: none — all 51 old plans appear in the new file when QLA codes exist).

### Material NFOINT conflicts (old crosswalk → Valuation_Setup)

| QLA Plan | Old source | New (decimal) |
|----------|------------|---------------|
| 17CSI3/5/7, 1CSIMN | 5.75% | 0.045 (4.50%) |
| 1L1095, 1L10*, 1L14SC, L15/L16/L17 family | 5.00% | 0.045 (4.50%) |
| 1668SP | 6.00% | 0.055 (5.50%) |
| 1960PO | (computed / blank code) | 0.035 (3.50%) |

---

## 5. Open Client Questions

**Blank rule (locked):** If Valuation_Setup leaves a cell blank, that assumption does not apply. Emit blank.

**Codes locked from QLAdmin Help** (see `evidence/cso_valuation_setup_code_map.md`):

| Topic | Mapping |
|-------|---------|
| NFOINT / RSVINT | Help §6.10 Reserve Interest Rate Chart (e.g. 3.50%→`6`, 4.50%→`A`, 5.50%→`E`) |
| INTMETHCV / INTMETHTV | Curtate→`0`, Continuous→`1` |
| RSVMETH | NLP→`1`, CRVM→`3` |
| STOREMEANS | Default (Terminal)→`False` |
| CALCMIDS | Default (Mean)→`False` |
| MORT / ETIMORT when already A1/C1/N1/O1/Q1 | Load as written |

**Answered 2026-07-17:**

1. `221END` / `222END` ETIMORT = **`N1`** (1941 CSO).  
2. Four missing-QLA PUA rows → **Issue #81** (out of #80).  
3. PUA QuikPl keys vs #60 → **Issue #82** (out of #80).

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Authority | `docs/Valuation_Setup.xlsx` only for listed plans |
| Blanks | Workbook blank → emit blank; do not copy old crosswalk |
| Codes | Never invent; require OBQ-80-1…4 answers or a CSO code dictionary |
| INTMETH label | Treat `Curtate` as the method name; emit schema code once confirmed |
| NFOINT input | Treat Excel decimals as rates (0.045 = 4.50%), not already-coded letters |
| Citizens | Zero changes under `Citizens_Product_Rate_Conversion/` |

---

## 7. Policy Key Handling

- Plan join key = workbook **QLA Plan** ↔ rate-key / quikplan `PLAN`.
- No MPOLICY / crosswalk policy-number changes (#25 preserved).
- No MPREM changes (#26 preserved).

---

## 8. Estimated Record Counts

| Surface | Estimate |
|---------|----------:|
| Authority plans with QLA code | 61 |
| Authority plans missing QLA | 4 (hold) |
| QuikPlCv key rows touched | All key rows for those 61 PLANs (segmentation × EFFDATE) |
| QuikPlTv key rows touched | Same PLAN set |
| quikplan rows touched | Plans in quikplan matching the 61 codes |
| Factor table rows | 0 |

---

## 9. Sample Trace (before-state)

| PLAN | Workbook NFOINT | Workbook QuikPlTv Rsv Int / Mthd | Current QuikPlCv NFOINT (Output) | Current QuikPlTv RSVINT/RSVMETH |
|------|-----------------|----------------------------------|----------------------------------|--------------------------------|
| 1960PO | 0.035 | 3.50% / CRVM / Curtate | Blank / incomplete vs need | Blank |
| 1658C1 | 0.045 | 4.50% / CRVM / Curtate | May have old crosswalk code `A` if applied | Blank reserve fields |
| 17CSI3 | 0.045 | 4.50% / CRVM / Curtate | Old crosswalk implied 5.75%/`F` | Blank reserve fields |
| 1L1095 | 0.045 | 4.50% / CRVM / Curtate | Old 5.00%/`C` | Blank reserve fields |
| 221END | 0.025 | 2.50% / CRVM / Curtate | ETIMORT prose unresolved | Blank reserve fields |

(Exact before CSV cells to be captured in Risk with a read-only audit script.)

---

## 10. Risks and Unknowns

| Risk | Impact |
|------|--------|
| Wrong interest letter code | Silent wrong CV/reserve calc in QLAdmin |
| Filling PUA plan keys contrary to #60 | Reopens withdrawn #56 complexity |
| Overwriting plans not in workbook | Regression vs #77 fleet defaults |
| Treating decimal 0.045 as literal NFOINT char | Schema/load failure or garbage |
| Citizens/CFIC accidental edits | Out-of-scope contamination |

---

## 11. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue #80.

Read AI_Agents/Risk_Agent.md and Issue_80 Planning + Dependency Gate.
Model: Cursor Grok 4.5. Do not code.

Quantify: plans/rows touched in QuikPlCv, QuikPlTv, quikplan; conflicts vs
CSO_Mortiality_Crosswalk.csv; impact on #60 Track B (1960PO) and #77 assumptions.
Go/No-Go only after OBQ-80-1…4 code legends are answered (or Conditional Go with
explicit freeze on unmapped rates).
```

---

## 12. Recommended Development Task (do not implement)

1. Add CSO Valuation Setup machine-readable config derived **exactly** from `docs/Valuation_Setup.xlsx` (plus locked code map from CSO answers).
2. Extend assumption provider so QuikPlTv reserve five fields populate; keep factor grids untouched.
3. Align quikplan NFOINT/INTMETHCV apply path to the same authority (Valuation_Setup wins).
4. Validator: for every workbook PLAN with QLA code, assert QuikPlCv/Tv (/quikplan) fields equal mapped expected values; blank==blank.
5. Version-bump `app.py` when engine path changes; publish modified rate/plan CSVs to `Output/Test_Validation/`.
6. Do not modify `Citizens_Product_Rate_Conversion/`.

---

## Gate Criteria (G1 — Planning Complete)

- [x] Source/target mapping documented
- [x] Open questions listed (OBQ-80-1…8)
- [x] Unrelated fields / Citizens exclusion listed
- [x] No code or rulebook changes
