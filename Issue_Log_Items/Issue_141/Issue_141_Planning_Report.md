# Issue #141 — Planning Report

**Issue:** #141 — Reserve Category  
**Framework stage:** Planning Agent  
**Status:** Planning  
**Generated:** 2026-08-19  
**Agent/script:** Cursor Grok 4.5 · `QLA_Migration/_risk_review_issue141_resrvcat.py`

---

## 1. Executive Finding

QuikSpec has no reserve category today. LifePRO stores it as **`PCOVR.PRODUCT_TYPE`** (plan LOB on the screenshot: `A96DAR` = `03`). Issue #99 overwrote that same code on eight ISWL plans to `ISWLFE`, so Development must **not** copy current `quikplan.PRODUCT`. Join **PPBEN BENEFIT_SEQ=1 PLAN_CODE → PCOVR.PRODUCT_TYPE** (5,083 / 5,083, zero misses). Target `quikspec.RESRVCAT` char 2. Ready for Dependency Gate.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|--------------|--------------|---------------------|----------:|
| PCOVR | `PCOVR_Coverage_Extract*.csv` | Yes (20260630) | 141 coverages |
| PPBEN | `PPBEN_PolicyBenefit_Extract*.csv` | Yes (20260630) | 11,699 (5,083 seq-1) |

### Available source fields

| Field | Column / source | Populated % | Notes |
|-------|-----------------|------------:|-------|
| Policy | PPBEN.POLICY_NUMBER | 100% seq-1 | Crosswalk + `format_qladmin_mpolicy` |
| Base coverage | PPBEN.PLAN_CODE where BENEFIT_SEQ=1 | 100% | BA traditional; BF ISWL |
| Reserve category | PCOVR.PRODUCT_TYPE | 100% of coverages | Codes 03, 05, 06, 07, 08, 09, 11, 12, 13, 16, 19, 70, L |

`PCOVR.VAL_CODE` is not the source (blank on `896 DAR`).

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source |
|-------|-------|------|--------|--------|
| quikspec | MPOLICY | C | 10/11 emit | Existing |
| quikspec | VANISH | L | 1 | Existing — do not change |
| quikspec | VANISHDT | D | 8 | Existing — do not change |
| quikspec | RESSTATE | C | 2 | Existing — do not change |
| quikspec | RESRVCAT | C | **2** | Client-added User Defined; Help §7.209 stock list is MPOLICY only |

**Repo references**

| Location | Role |
|----------|------|
| `QLA_Migration/Configs/Sync_Rulebook_quikspec.csv` | Current RESSTATE / VANISH defaults |
| `app.py` + `QLA_Migration/app.py` TABLE_SCHEMAS `quikspec` | Four columns today |
| `validation_config/schema_manifest.json` | Same four columns |
| `tools/validators/validate_quikspec_resident_state.py` | Full-batch smoke |
| `qla_core/quikplan_converter.py` `apply_iswl_product_tags` | #99 ISWLFE — do not touch |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PPBEN | POLICY_NUMBER | quikspec.MPOLICY | Existing #2/#25 key | No |
| PPBEN seq=1 | PLAN_CODE | (join key) | Normalize; lookup PCOVR | Join only |
| PCOVR | PRODUCT_TYPE | quikspec.RESRVCAT | Trim; emit as-is; char 2 | **Yes** |
| PPOLC | RES_STATE | quikspec.RESSTATE | Existing | No |
| — | — | quikspec.VANISH / VANISHDT | Existing defaults / #145 | No |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| quikmstr.MMODPREM | PPOLC.MODE_PREMIUM | **No** |
| quikridr.MPREM | ANN_PREM_PER_UNIT + fallback (#26) | **No** |
| MPOLICY padding | format_qladmin_mpolicy (#25 / #2) | **No** |
| quikplan.MKTG / PRODUCT / HLOB | #99 ISWLFE overlay | **No** |
| quikplan.MNAICLOB | NAPLAN | **No** |
| quikiswl.MLOB | #124 literal I | **No** |

---

## 5. Open Client Questions

Locked at Planning (Warren 2026-08-19):

1. Field width — **char 2** on working DBF and Append Tool template.
2. Source — **`PCOVR.PRODUCT_TYPE`** (A96DAR LOB=03).
3. Grain — **PPBEN BENEFIT_SEQ=1 only** (not rider phases).
4. Odd codes (`L`, blank) — **emit as-is**.

No remaining client questions that block Risk.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Existing crosswalk + `format_qladmin_mpolicy()` |
| RESRVCAT | Trim LifePRO PRODUCT_TYPE; do not left-pad; `L` stays `L` |
| Blanks | Blank if seq-1 PLAN_CODE has no PCOVR row (sim: 0) |
| Dates / money | N/A |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → existing QuikSpec row (same as RESSTATE emit).
2. Join seq-1 on stripped LifePRO number (drop trailing `C` on QLA key).
3. Orphan: log + blank RESRVCAT; do not drop the QuikSpec row.

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| quikspec rows | 5,083 | Current Output |
| Rows that gain RESRVCAT | 5,083 | New column |
| Join misses | 0 | Risk sim |
| Policies where value ≠ current quikplan.PRODUCT | 2,301 | Mostly ISWLFE vs 05/06/16 |

Proposed RESRVCAT: 05=1,162; 13=832; 03=677; 16=656; 12=521; 06=454; 08=245; 07=202; 70=163; 11=80; 19=38; L=33; 09=20.

---

## 10. Sample Trace (3 policies)

| Policy (QLA) | LifePRO coverage | Before | After (proposed) | Status |
|--------------|------------------|--------|------------------|--------|
| 9010143726C | 621 END85 | (no field) | 03 | Traditional |
| 9010148272C | 621 END85 | (no field) | 03 | Traditional |
| 9010713704C | 659 CEN II | (no field) | 05 | ISWL; plan HLOB stays ISWLFE |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Copying quikplan.PRODUCT | High | 2,268 ISWL get ISWLFE | Join PCOVR only |
| BA-only filter | High | Drops all 2,348 ISWL BF seq-1 | Use BENEFIT_SEQ=1 |
| #145 VANISH later | Low | Add column at end of schema | Do not rewrite VANISH |
| Reverse catalog join | Medium | 166 QLA plans miss PCOVR | Do not use MPLAN reverse lookup |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | Yes |
| Field definitions confirmed | Yes — char 2 RESRVCAT |
| Client scope clear | Yes |
| Example policies available | Yes |

---

## 13. Recommended Risk Agent Prompt

```
Risk Agent — Issue 141 Reserve Category.
Read-only sim already at QLA_Migration/_risk_review_issue141_resrvcat.py.
Confirm GO/NO-GO. Do not code.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. Add `RESRVCAT` to `TABLE_SCHEMAS["quikspec"]` in **both** `app.py` and `QLA_Migration/app.py`.
2. Add the column to `schema_manifest.json` and `Sync_Rulebook_quikspec.csv` (enrichment note: not a PPOLC column).
3. After existing QuikSpec emit, set `RESRVCAT` from PPBEN seq-1 `PLAN_CODE` → PCOVR `PRODUCT_TYPE`.
4. Bump `APP_VERSION` in both app.py files to **v58.97**.
5. Extend `tools/validators/validate_quikspec_resident_state.py` (or add `validate_issue141_resrvcat.py`): schema has RESRVCAT; traces 03 / 05; no ISWLFE on RESRVCAT; quikplan ISWLFE unchanged.
6. Do **not** change `apply_iswl_product_tags` or QuikPlan.

## Appendix

- Sim: `QLA_Migration/_risk_review_issue141_resrvcat.py`
- Evidence: `Issue_Log_Items/Issue_141/evidence/issue141_risk_impact_summary.json`
- Related: #99, #124, #132, #145
