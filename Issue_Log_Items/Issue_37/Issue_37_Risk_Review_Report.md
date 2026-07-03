# Issue #37 — Risk Review Report

**Issue:** Age/Duration Rate Placement — CV / QuikCvs (fleet-wide)  
**Framework stage:** Risk Agent (G3)  
**Status:** **Conditional Go — APPROVED**  
**Approved:** 2026-07-03 (project lead)  
**Generated:** 2026-07-03  
**Mode:** Risk analysis only — no production code in this stage

---

## Go / No-Go Recommendation

**CONDITIONAL GO — APPROVED**

Fleet-wide **QuikCvs** duration placement fix in Phase R5 is authorized under documented conditions. Rate **values** remain unchanged; only grid structure (leading zeros, LifePRO duration numbering, maturity extension) changes.

---

## 1. Current vs Proposed Mapping

| Aspect | Current | Proposed | Change? |
|--------|---------|----------|---------|
| Extract → QL slot | `ql_duration = source_duration − 1` | LifePRO-style CV grid builder | **Yes (CV only)** |
| Leading zero durations | Not inserted | Insert before first non-zero rate | **Yes** |
| Grid end | Extract max duration | **`100 − issue_age`** | **Yes** |
| Rate numeric values | Correct | Unchanged | **No** |
| Other rate families (NP, GP, DB, …) | `duration − 1` | Unchanged | **No** |

**Proof anchor — 960 PO / 1960PO / M / age 22:**

| | LifePRO | QLAdmin today | Proposed |
|--|--------:|-------------:|---------:|
| First rate (8.32) | Duration 4 | Duration 1 | Duration 4 |
| Last rate (1000) | Duration 78 | Duration 75 | Duration 78 |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| `app.py` / QuikPlan | Plan converter | **No** |
| `quikridr.MPREM` | Issue #26 | **No** |
| MPOLICY padding | Issue #25 | **No** |
| QuikNps, QuikGps, QuikDbs, QuikTvs, QuikDvs | Phase R5 (non-CV) | **No** |
| QuikPlCv keys | Plan crosswalk | **No** (same tuples) |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `qla_core/rate_factor_loader.py` | `transform_source()` — primary change surface |
| `qla_core/rate_dbf_schema.py` | `source_duration_to_ql()`, CNTL paging |
| `qla_core/rate_pipeline.py` | Rate emit orchestration |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | Loader config |
| `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv` | Authoritative CV source |
| `tools/validators/iswl_quikcvs_reconcile.py` | Post-fix validation |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| CV products (coverages) | 36 |
| CV age/sex slices | 3,405 |
| Slices with placement change | 3,405 |
| Current CNTL pages (approx.) | 19,453 |
| Proposed CNTL pages (maturity 100) | 21,754 |
| Delta CNTL pages | +2,301 |

### Start shift (960 PO male proof rule, fleet CV)

| Issue ages | LifePRO first rate column | Shift vs QLAdmin today |
|-----------:|--------------------------:|----------------------:|
| 0 | 7 | +6 |
| 18–22 | 4 | +3 |
| 24+ | 3 | +2 |

**Do not hardcode +3 fleet-wide.**

### End shift (maturity age **100** — G3 assumption)

| Category | Slices |
|----------|-------:|
| Tail extension (zero-fill) | 3,287 |
| Extract longer than `100 − age` (truncate policy needed) | 98 |
| Already aligned | 20 |

---

## 5. Maturity Age 100 vs 103

| Source | Finding |
|--------|---------|
| 960 PO male proof ages | `last_duration = 100 − issue_age` |
| LifePRO F/0 screenshot | Duration **103** column |
| PCOVR | Only **960 PO** has `MAX_BENEFIT_AGE = 103` |
| **G3 decision (approved)** | Fleet rule = **100 − issue_age**; 103 treated as outlier / ENDOW103F artifact |

---

## 6. PCOVR Override (12 products, MAX_BEN ≠ 100)

| MAX_BEN | Products | Slices | G3 note |
|--------:|----------|-------:|---------|
| 116 | CSI3/5/7, MN5K, 970 JEB, 991 PWL | 571 | Override to 100 unless SME reverses |
| 103 | 960 PO | 142 | Override to 100 (approved) |
| 95 | 665 STME95 | 51 | Override to 100 |
| 65 | 1578 SPSPU, 896 DAR | 93 | Override to 100 |
| 1 | L15, L16 | 124 | Validate separately |

---

## 7. Fallback Recommendation

| Option | Assessment |
|--------|------------|
| A — 1960PO-only patch | Rejected — leaves ~35 products incorrect |
| **B — Fleet CV grid builder + maturity 100** | **Approved** |
| C — Per-product PCOVR maturity | Deferred unless SME requires |

**Rollback:** Restore pre-fix `QuikCvs.csv` from baseline/archive; no `app.py` rollback.

---

## 8. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserved** |
| Issue #26 MPREM / MMODPREM | **Preserved** |
| Issue #31 QuikCvs emit scope | Re-baseline validators after fix |

---

## 9. Regression Testing Checklist (Validation Agent)

- [ ] 960 PO proof ages: M 0, 18, 20, 22, 24, 29, 33; F 0
- [ ] M/22 anchor: 8.32 at duration 4; 1000 at duration 78
- [ ] Fleet sample: 659 CEN II, 960 OL, 991 PWL, L10 LP95 (spot check)
- [ ] Truncate policy verified on 98 over-length slices
- [ ] QuikNps / QuikGps / QuikDbs unchanged (row-count spot check)
- [ ] `iswl_quikcvs_reconcile.py` pass with updated baseline
- [ ] No new blank MRIDRID / QuikPlan drift

---

## 10. Recommended Development Agent Task

1. Add **CV-only** LifePRO grid builder in `rate_factor_loader` (or wrapper invoked only for `QuikCvs`).
2. Per slice: insert leading zero durations; map values to LifePRO duration index; extend grid to **`100 − issue_age`**.
3. Apply **variable start offset** from proof matrix — not constant +3.
4. Document and implement **truncate policy** for 98 over-length slices.
5. Re-emit `QuikCvs.csv` only; run proof matrix + fleet spot checks.
6. Do **not** change `source_duration_to_ql` behavior for non-CV type codes.
7. Version bump per project convention if `app.py` or pipeline version touched.

---

## 11. Approval

| Field | Value |
|-------|-------|
| Recommendation | **Conditional Go** |
| Approved | **Yes — 2026-07-03** |
| Approver | Project lead |
| Development authorized | **Pending explicit authorization** |
