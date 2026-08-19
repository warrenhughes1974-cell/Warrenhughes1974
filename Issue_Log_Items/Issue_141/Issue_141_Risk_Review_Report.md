# Issue #141 — Risk Review Report

**Issue:** #141 — Reserve Category  
**Framework stage:** Risk Agent  
**Status:** **GO — Ready for Development** (after user approval)  
**Generated:** 2026-08-19  
**Agent/script:** Cursor Grok 4.5 · `QLA_Migration/_risk_review_issue141_resrvcat.py`

**Status note:** Risk analysis only — no production code changes.

---

## Go / No-Go Recommendation

**GO** — Add `quikspec.RESRVCAT` from LifePRO `PCOVR.PRODUCT_TYPE` via PPBEN BENEFIT_SEQ=1. New column on all 5,083 QuikSpec rows; zero join misses; QuikPlan ISWLFE tags unchanged.

**Conditions:**

1. Do **not** copy current `quikplan.PRODUCT` (2,301 policies would get the wrong code, mostly `ISWLFE`).  
2. Do **not** filter `BENEFIT_TYPE=BA` only (drops 2,348 ISWL `BF` seq-1 rows).  
3. Do **not** change `apply_iswl_product_tags` / QuikPlan / QuikIswl.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| quikspec.RESRVCAT | column absent | PCOVR.PRODUCT_TYPE via seq-1 PLAN_CODE | **Yes** |
| quikspec.RESSTATE | PPOLC.RES_STATE | unchanged | **No** |
| quikspec.VANISH / VANISHDT | defaults / #145 | unchanged | **No** |
| quikplan.PRODUCT / HLOB / MKTG | #99 ISWLFE on 8 plans | unchanged | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| quikridr.MPREM | #26 / #88 / #137 | **No** |
| quikmstr.MMODEPREM | PPOLC | **No** |
| MPOLICY padding | #2 / #25 | **No** |
| quikiswl.MLOB | #124 | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `Sync_Rulebook_quikspec.csv` | Current spec emit |
| `app.py` / `QLA_Migration/app.py` TABLE_SCHEMAS | Add RESRVCAT |
| `qla_core/quikplan_converter.py` `apply_iswl_product_tags` | Do not touch |
| `tools/validators/validate_quikspec_resident_state.py` | Extend or companion validator |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| quikspec rows | 5,083 |
| Rows that would gain RESRVCAT | 5,083 |
| Join misses | 0 |
| Value equals current quikplan.PRODUCT | 2,782 |
| Value differs from current quikplan.PRODUCT | 2,301 |

### Proposed RESRVCAT

| Code | Policies |
|------|--------:|
| 05 | 1,162 |
| 13 | 832 |
| 03 | 677 |
| 16 | 656 |
| 12 | 521 |
| 06 | 454 |
| 08 | 245 |
| 07 | 202 |
| 70 | 163 |
| 11 | 80 |
| 19 | 38 |
| L | 33 |
| 09 | 20 |

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| A — PPBEN seq-1 → PCOVR.PRODUCT_TYPE | 5,083 new values | **Recommended** |
| B — Copy quikplan.PRODUCT | 5,083 (2,301 wrong) | **Reject** — ISWLFE on policy |
| C — BA-only join | 2,735 | **Reject** — misses ISWL BF |
| D — Reverse QLA MPLAN → PCOVR | 4,917 | **Reject** — 166 orphans |

**Recommended fallback:** None. Option A is complete.

---

## 6. Trace Policies

| Policy | Before | Proposed | Plan HLOB | Pass? |
|--------|--------|----------|-----------|-------|
| 9010143726C | (absent) | 03 | blank | Yes |
| 9010148272C | (absent) | 03 | blank | Yes |
| 9010713704C | (absent) | 05 | ISWLFE | Yes |

---

## 7. Top Changes

Not numeric. Largest semantic delta is ISWL: plan stays `ISWLFE`, policy gets `05` / `06` / `16`.

---

## 8. Material Calculation Impact

None. User-defined code only. No premium, reserve factor, or status math.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 / #2 MPOLICY padding | Preserved — same spec key path |
| Issue #26 MPREM / MMODPREM | Untouched |
| Issue #99 ISWLFE on plan | Untouched |
| Issue #132 RESSTATE | Untouched |
| Issue #145 VANISH | Untouched (still F on current Output) |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] Schema: `quikspec` includes `RESRVCAT` after `RESSTATE`
- [ ] 9010143726C / 9010148272C = `03`
- [ ] 9010713704C = `05` (not `ISWLFE`)
- [ ] No `RESRVCAT=ISWLFE`
- [ ] quikplan 1659C2 / 1658C1 HLOB+PRODUCT+MKTG still `ISWLFE`
- [ ] RESSTATE and VANISH unchanged vs pre-change Output
- [ ] Row count 5,083 (or current full-batch count)
- [ ] `L` codes emit as `L` (33 policies)

---

## 11. Recommended Development Agent Task

1. Add `RESRVCAT` to both `app.py` `TABLE_SCHEMAS["quikspec"]` and `schema_manifest.json`.
2. After current QuikSpec write, enrich from PPBEN BENEFIT_SEQ=1 `PLAN_CODE` → PCOVR `PRODUCT_TYPE`.
3. Do **not** change `apply_iswl_product_tags`, QuikPlan, QuikIswl, VANISH, RESSTATE mapping.
4. Version bump **v58.97** in both `app.py` files.
5. Validator: traces above + no ISWLFE on RESRVCAT + ISWL plan tags intact.

---

## Appendix

- Simulation: `QLA_Migration/_risk_review_issue141_resrvcat.py`
- Summary: `Issue_Log_Items/Issue_141/evidence/issue141_risk_impact_summary.json`
