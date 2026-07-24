# Issue #106 — Planning Report

**Issue:** #106 — RV Rates Off by One Duration (QuikTvs)  
**Framework stage:** Planning Agent  
**Status:** Planning complete — Dependency Gate next  
**Generated:** 2026-07-24  
**Agent:** Planning Agent (Cursor Grok 4.5) — research only, no code

---

## 1. Executive Finding

RV factors are emitted one duration early because every non-CV family still uses `source_duration_to_ql()` (= `source − 1`). Eric’s screens and Rate_Table proofs for `170858` / `1659C2` match that shift exactly. CV already uses a separate LifePRO grid remap (#37/#41/#98); that matrix must **not** be applied to RV.

**Recommended direction:** For `TYPE_CODE == "RV"` / table `QuikTvs` only, emit `ql_duration = source_duration` (identity). Leave NP/DV/DB/PR on `source − 1` until separately proven. Separately document that `1L1095` QuikTvs pulls from **`L10 LP95`**, not L10 LP9595 (absent from extracts).

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source | File | Notes |
|--------|------|-------|
| Rate_Table | `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv` | TYPE_CODE=RV; padded columns |
| PDAGE miss-fill (if used) | Staging / Rate_Audit merges | Same duration helper must stay consistent |
| Inheritance | rate_inheritance_loader + parity JSON | 17085M/170588 ← 170858; 1L1095 ← L10 LP95 |

### Available source fields (RV)

| Field | Column | Notes |
|-------|--------|-------|
| Coverage | `COVERAGE_ID` | e.g. `670 GL85-8` |
| Type | `TYPE_CODE` | `RV` |
| Age / Sex / Band / UW | AGE, SEX, BAND, UNDERWRITING_CLASS | Segmentation |
| Duration | `DURATION` | LifePRO 1-based year label |
| Value | `VALUE` | Factor |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field / role | Notes |
|-------|--------------|-------|
| QuikTvs | PLAN, AGE, CNTL, TV0–TV9, GENDER, UWCLASS, BAND, … | Factor pages; CNTL = duration // 10 |
| QuikPlTv | Rate keys | Shared with NP; keys unchanged by Dur remap |
| TYPE_TO_TABLE | RV → QuikTvs | `qla_core/rate_dbf_schema.py` |

Paging: `duration_to_cntl_col(ql_duration)` → CNTL page + TVn column. Identity Dur means LifePRO Dur 1 → CNTL 00 / TV1 (not TV0).

---

## 4. Required Source-to-Target Mapping Change

| LifePRO | Current QL | Proposed QL | Change? |
|---------|------------|-------------|---------|
| RV DURATION N | QuikTvs Dur N−1 | QuikTvs Dur **N** | **Yes** |
| RV VALUE | same factor text | unchanged | No |
| CV path | `cv_remap_ql_duration` | unchanged | **No** |
| NP/DV/DB/PR duration | source−1 | unchanged this issue | **No** |

### Code touch list (surgical)

| File | Change |
|------|--------|
| `qla_core/rate_dbf_schema.py` | Add `rv_source_duration_to_ql(d) -> int(d)` (or type-aware wrapper); keep `source_duration_to_ql` for other non-CV |
| `qla_core/rate_factor_loader.py` | RV branch → identity |
| `qla_core/rate_inheritance_loader.py` | RV inherited rows → identity |
| `qla_core/pdage_missfill.py` | RV miss-fill → identity |
| `qla_core/shared_rate_candidate_loader.py` | RV shared candidates → identity |
| root `app.py` + `QLA_Migration/app.py` | Bump `APP_VERSION` |

Do **not** change global `source_duration_to_ql` in place — that would shift NP/DV/DB/PR without proofs.

---

## 5. Open Client Questions

1. Confirm acceptance: QLAdmin Dur labels must match LifePRO Dur **1..N** for RV (not 0-based display).
2. `1L1095`: confirm research should compare to **L10 LP95** (not LP9595) unless client can supply LP9595 extract rows.
3. Scope: RV/QuikTvs only for this issue (yes/no on expanding to other non-CV families later).

None of these block Development if Warren accepts the LifePRO Dur-label convention already used for CV screens.

---

## 6. Implementation plan (post-approval)

1. Add RV identity helper; route all RV emit paths through it.
2. Re-emit rates (`QuikTvs` minimum; full rates batch if pipeline requires).
3. Validate Eric proofs + screenshot docx.
4. Publish `Output/Test_Validation/rates/QuikTvs.csv` (and QuikPlTv only if keys change — expected no).
5. Document `1L1095` ← `L10 LP95` for Eric reply.
6. G7 accountability on full Output before Closed.

---

## 7. Regression / blast radius

| Area | Impact |
|------|--------|
| QuikTvs all plans | Every non-blank TV cell moves to Dur+1 vs current Output |
| QuikCvs / CV remap | Must remain bit-identical |
| QuikNps / QuikDvs / QuikDbs / QuikGps | Untouched |
| QuikPlTv keys | Untouched (same PLAN/GENDER/UW/BAND) |
| Inherited GL85 / L10 children | Shift with parents (correct) |

---

## 8. Planning disposition

**Proceed to Dependency Gate.** Fix path is clear; evidence pack present; no SME option fork required for Dur identity.
