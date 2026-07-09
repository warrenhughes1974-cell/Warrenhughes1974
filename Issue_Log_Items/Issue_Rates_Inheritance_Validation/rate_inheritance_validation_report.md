# Rate Inheritance Validation Report

**Date:** 2026-07-07  
**Scope:** LifePRO product rate conversion to QLAdmin rate tables, with emphasis on inherited/shared rate sources and segment resolution  
**Mode:** Analysis only — no conversion code changed during this validation pass

---

## Summary

This validation pass confirms the current rate loader is reliable for direct `Rate_Table` conversion and for the Issue #40 inherited **cash value** scope, but it does **not** prove that all inherited/shared non-CV rates are complete.

Key results:

| Area | Result |
|------|--------|
| Direct `Rate_Table` cells | **770,524 / 770,524 matched** emitted QLAdmin CSV formatting |
| Issue #40 inherited CV cells | **101,793 / 101,793 matched** emitted `QuikCvs.csv` |
| LifePRO screenshot anchors | **8 / 8 matched** converted output |
| PCOVRSGT inherited/shared CV candidates | **10 / 10 resolved** by Issue #40 manifest |
| PCOVRSGT inherited/shared non-CV candidates | **35 candidate gaps** found |
| Pipeline blockers | 1 unrelated blocker: `V-UINT-PDINT` / `QuikUint` missing `PDINTTBL` |

Conclusion: inherited **CV** rates appear resolved for the approved Issue #40 fleet. Inherited/shared rates for **NP, RV, DV, DB, and PR** are not fully resolved by current code and require business/actuarial review before implementation.

---

## Scope Reviewed

Reviewed rate families:

- `CV` → `QuikCvs` / `QuikPlCv`
- `DB` → `QuikDbs` / `QuikPlDb`
- `NP` → `QuikNps` / `QuikPlTv`
- `RV` → `QuikTvs` / `QuikPlTv`
- `DV` → `QuikDvs` / `QuikPlDv`
- `PR` → `QuikGps` / `QuikPlGp`
- PAAGERAT-derived `BP`, `U5`, `U6` → `QuikGps`, `QuikGcoi`, `QuikCoi`

Reviewed screenshot documents:

- `docs/659 CEN II - LifePRO Product Rate Informaiton.docx`
- `docs/670 GL85-8 - LifePRO Product Rate Informaiton.docx`

The Word files contain embedded images only. The screenshots were extracted to `extracted_screenshots/`. Local OCR was not available, so the validation matrix captures manually read anchor rows and marks remaining screenshots as manual review pending.

---

## Source Files Reviewed

| Source | Purpose |
|--------|---------|
| `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv` | Primary LifePRO product rate extract for CV/DB/NP/DV/RV/PR |
| `plan_analysis/source_data/rates/PAAGERAT_AttainedAge_Rates_Extract_20260428.csv` | Segment-rate source for PAAGERAT PR/BP/U5/U6 derived loaders |
| `plan_analysis/source_data/coverage/PCOVRSGT.csv` | Active coverage-to-segment relationship table |
| `plan_analysis/source_data/coverage/PCOVR.csv` | Coverage metadata used by segment resolver |
| `plan_analysis/source_data/crosswalk/Policy Form Crosswalk 5.22.26.xlsx` | Coverage ID to QLAdmin `PLAN` crosswalk |
| `plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv` | CV rate-key assumptions |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | Rate loader configuration and source paths |
| `Issue_Log_Items/Issue_40/Issue_40_Fleet_CV_Inheritance_Audit.csv` | Approved Issue #40 inherited CV manifest source |

---

## Conversion Scripts Reviewed

| File | Role |
|------|------|
| `qla_core/rate_pipeline.py` | Orchestrates source transforms, inherited CV stream, factor grids, key rows, member rows, validation |
| `qla_core/rate_factor_loader.py` | Direct `Rate_Table` transform, CV duration remap, factor-grid pivot |
| `qla_core/cv_inheritance_loader.py` | Issue #40 CV-only inherited rate emit |
| `qla_core/rate_segment_resolution.py` | PAAGERAT segment-to-parent coverage resolver |
| `qla_core/paagerat_pr_loader.py` | PAAGERAT PR loader |
| `qla_core/paagerat_bp_loader.py` | PAAGERAT BP gross premium loader |
| `qla_core/paagerat_ul_coi_loader.py` | PAAGERAT U5/U6 COI loaders |
| `qla_core/rate_dbf_schema.py` | QLAdmin table routing, segmentation mapping, duration paging, formatting |
| `qla_core/rate_key_setup.py` | QuikPlxx key-row generation |
| `qla_core/rate_member_setup.py` | QuikPlGd/Uw/Bd/St/Nb member generation |
| `qla_core/rate_emit.py` | App-integrated rate emit and Issue #40 package verification |

---

## Output Tables Reviewed

Reviewed generated tables under `QLA_Migration/Output/rates/`:

| Output | Rows in pipeline result |
|--------|------------------------:|
| `QuikCvs.csv` | 38,047 |
| `QuikDbs.csv` | 1,380 |
| `QuikNps.csv` | 26,650 |
| `QuikTvs.csv` | 26,097 |
| `QuikDvs.csv` | 3,978 |
| `QuikGps.csv` | 12,567 |
| `QuikCoi.csv` | 792 |
| `QuikGcoi.csv` | 198 |
| `QuikPlCv.csv` | 94 |
| `QuikPlDb.csv` | 12 |
| `QuikPlTv.csv` | 112 |
| `QuikPlDv.csv` | 20 |
| `QuikPlGp.csv` | 205 |
| `QuikPlGd.csv` | 184 |
| `QuikPlUw.csv` | 151 |
| `QuikPlBd.csv` | 134 |
| `QuikPlSt.csv` | 115 |
| `QuikPlNb.csv` | 115 |

---

## How Inherited Rates Are Currently Resolved

Current behavior is split by source:

- Direct `Rate_Table` rows resolve through `Coverage_ID -> PLAN` using the Policy Form Crosswalk.
- PAAGERAT rows resolve through `PAAGERAT.COVERAGE_ID -> PCOVRSGT.SEGT_ID -> parent COVERAGE_ID -> PLAN`.
- Issue #40 adds a **CV-only** inheritance stream: approved PCOVRSGT rate-owner coverages emit `CV` rows under the issuing plan.

Important limitation:

The Issue #40 inheritance loader only emits `CV` rows. It does not generalize inheritance to `NP`, `RV`, `DV`, `DB`, or `PR`.

---

## Screenshot Validation Results

Screenshot anchors are in `screenshot_validation_matrix.csv`.

| Document | Plan | Type | Anchors | Result |
|----------|------|------|--------:|--------|
| `659 CEN II - LifePRO Product Rate Informaiton.docx` | `1659C2` | `CV` | 4 | PASS |
| `670 GL85-8 - LifePRO Product Rate Informaiton.docx` | `170858` | `CV` | 2 | PASS |
| `670 GL85-8 - LifePRO Product Rate Informaiton.docx` | `170858` | `DV` | 2 | PASS |

Anchor examples:

| LifePRO screenshot | Converted output |
|--------------------|------------------|
| `659 CEN II`, `CV`, F / SM / Band 01 / Age 20 / Dur 004 = `3.00` | `QuikCvs.csv CV4 = 3.00` |
| `659 CEN II`, `CV`, F / SM / Band 01 / Age 57 / Dur 039 = `864.00` | `QuikCvs.csv CV9 = 864.00` |
| `670 GL85-8`, `CV`, F / UW 00 / Band 01 / Age 31 / Dur 003 = `10.39` | `QuikCvs.csv CV3 = 10.39` |
| `670 GL85-8`, `DV`, F / UW 00 / Band 01 / Age 39 / Dur 049 = `29.71` | `QuikDvs.csv DV8 = 29.71` |

Note: CV screenshots display LifePRO/QL duration after LifePRO’s internal first-duration offset. The raw extract duration can be lower than the displayed duration. The validation matrix compares against the QL duration displayed in the screenshot.

---

## Matching Results

### Direct Rate_Table

All direct mapped `Rate_Table` source cells matched the emitted QLAdmin CSV output after applying the converter’s own QLAdmin field formatting.

| Check | Count |
|-------|------:|
| Direct source cells checked | 770,524 |
| Direct source cells matched | 770,524 |
| Direct source mismatches | 0 |

### Issue #40 Inherited CV

All inherited CV source cells matched the issuing-plan `QuikCvs.csv` output.

| Check | Count |
|-------|------:|
| Inherited CV cells checked | 101,793 |
| Inherited CV cells matched | 101,793 |
| Inherited CV mismatches | 0 |

Issue #40 resolved plans:

`1666AI`, `1668SP`, `17085M`, `1L10SO`, `1L10SR`, `1SALMI`, `1SALML`, `261PUA`, `265PUA`, `280PUA`

### PAAGERAT Segment Loaders

PAAGERAT-derived loaders produced 14,556 in-scope source rows. 14,255 matched emitted output. 301 did not match the emitted CSV value because the same output key already had a different value from another source path. Current grid precedence keeps the first value in these cases.

Affected PAAGERAT mismatch plans/types:

| Plan | Count | Types |
|------|------:|-------|
| `1L10SO` | 175 | PR |
| `7687J3` | 62 | PR |
| `1L16GD` | 42 | PR |
| `1679CS` | 12 | U5/U6/BP |
| `5667AT` | 5 | PR |
| `1658CS` | 4 | U6/BP |
| `57ATCR` | 1 | PR |

These require review of source precedence: direct `Rate_Table` vs PAAGERAT segment value.

---

## Inherited / Shared Rate Gaps

The PCOVRSGT scan found 45 candidate inherited/shared relationships:

- 10 `CV` candidates resolved by Issue #40.
- 35 non-CV candidates currently not emitted under the issuing plan.

Representative gaps:

| Plan | Source plan(s) | Type(s) not emitted |
|------|----------------|---------------------|
| `17085M` | `170858` | NP, DV, RV |
| `170588` | `170858` | NP, DV, RV |
| `1668SP` | `1659C2` | NP, RV |
| `1669SR` | `1659C2`, `1659CR`, `1659SR`, `1L14SC` | DB, NP, RV |
| `1679CS` | `1659C2`, `1L14SC` | NP, RV |
| `1666AI` | `1666WL` | NP, RV |
| `265PUA` | `2665ST` | DB, NP, DV, RV, PR |
| `261PUA` | `2961ME` | NP, DV, RV |
| `280PUA` | `280END` | NP, DV, RV |
| `1L10SO` | `1L1095`, `1L10SR` | NP, RV |
| `1SALMI` / `1SALML` | `1SALOL` | RV |

Full list: `evidence/inherited_rate_candidate_summary.csv`.

These are not automatically defects. They are evidence that the current inheritance work is CV-only and that non-CV rate inheritance needs explicit business approval before implementation.

---

## Risk Assessment

| Risk | Severity | Evidence |
|------|----------|----------|
| CV inherited rates missing after Issue #40 | Low | 101,793 / 101,793 inherited CV cells matched |
| Direct Rate_Table conversion incorrect | Low | 770,524 / 770,524 direct cells matched |
| Non-CV inherited/shared rates absent | High | 35 PCOVRSGT candidate gaps not emitted |
| PAAGERAT vs direct Rate_Table precedence unclear | Medium | 301 PAAGERAT source rows differ from emitted output due duplicate-key precedence |
| Screenshot full extraction incomplete | Medium | 62 screenshots extracted, 8 anchors validated, remaining rows require OCR/manual review |
| Full guarded emit blocked | Medium | `V-UINT-PDINT` remains unrelated blocker |

---

## Recommended Next Steps

1. Review `evidence/inherited_rate_candidate_summary.csv` with actuarial/business owners.
2. Decide whether non-CV inherited/shared rate segments should emit under issuing plans.
3. Decide source precedence for PAAGERAT conflicts: direct `Rate_Table` first vs PAAGERAT segment first vs explicit tier rules.
4. If approved, implement a manifest-driven inherited-rate loader generalized beyond CV.
5. Add an app-level validation gate that reports unresolved PCOVRSGT inherited/shared rate candidates before client UAT.
6. Perform manual OCR or manual transcription for all 62 screenshot images if full screenshot-row validation is required.

---

## Whether Code Changes Are Required

Code changes are **not required** for direct `Rate_Table` conversion or for approved inherited CV rows.

Code changes are likely required if the client expects inherited/shared **NP, RV, DV, DB, or PR** rows to behave like inherited CV. Those changes should not be made until the 35 candidate gaps are reviewed and approved.

No code was changed during this validation pass.

