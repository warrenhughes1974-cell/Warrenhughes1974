# Issue #42 — Regression Report

**Issue:** #42 — Missing Rate Extract Rows (L01/L10)  
**Framework stage:** Regression Agent  
**Engine version:** v57.79  
**Baseline:** Pipeline with `issue42_pdage_missfill.enabled=false` vs current ON; Output rates mtime (untouched families @ 2026-07-13 19:18; QuikNps/Tvs/PlTv @ 19:50)  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-07-13  
**Model:** Cursor Grok 4.5 (locked Regression stage)  
**Verdict:** **PASS**

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|-----------|-----------------|
| `Output/rates/QuikNps.csv` | Intentional — new/expanded plans from PDAGE miss-fill |
| `Output/rates/QuikTvs.csv` | Intentional — same |
| `Output/rates/QuikPlTv.csv` | Intentional — key rows for new NP/RV plans |
| Other rate families (QuikCvs, QuikGps, …) | **No change** |
| Policy `quik*.csv` tables | **No change** |
| #25 / #26 | Preserved |

---

## 2. Row Count Comparison

| Table | Rows | Expected delta | OK? |
|-------|-----:|----------------|-----|
| quikmstr | 5,083 | 0 (untouched) | **Yes** |
| quikridr | 6,934 | 0 | **Yes** |
| quikprmh | 209,470 | 0 | **Yes** |
| quikplan | 141 | 0 | **Yes** |
| quikclid | 34,449 | 0 | **Yes** |
| quikclnt | 13,597 | 0 | **Yes** |
| quikmemo | 337,882 | 0 | **Yes** |
| quikdvdp | 5,083 | 0 | **Yes** |
| rates/QuikCvs | 38,047 | 0 | **Yes** |
| rates/QuikGps | 17,137 | 0 | **Yes** |
| rates/QuikDbs | 2,513 | 0 | **Yes** |
| rates/QuikDvs | 6,452 | 0 | **Yes** |
| rates/QuikNps | 52,647 | **intentional +** | **Yes** |
| rates/QuikTvs | 53,818 | **intentional +** | **Yes** |
| rates/QuikPlTv | 220 | **intentional +** | **Yes** |

Evidence: `evidence/issue42_regression_row_counts.csv`

---

## 3. Non-Target Field Diff (rate grids)

Pipeline compare: miss-fill **ON** vs **OFF** (same Rate_Table / PAAGERAT otherwise).

| Table | Non-candidate plans changed | Unchanged non-candidates | OK? |
|-------|----------------------------:|-------------------------:|-----|
| QuikNps | **0** | 54 | **Yes** |
| QuikTvs | **0** | 58 | **Yes** |

### Candidate plans that changed (expected)

| Plan | QuikNps off→on | Notes |
|------|----------------|-------|
| `5L0110` | 0 → 424 | L01 10Y — **core Issue #42** |
| `5L0510` / `5L075Y` | 0 → n | Peer term segments from same PDAGE drop |
| `196085` | 0 → 284 | 960 LP85-8 NP/RV |
| `1L17SP` | 0 → 38 | L17 NP/RV (CV still absent) |
| ADB/WP plans | 0 → n | Resolvable PDAGE miss-fill segments |

### L10 LP9595 note

| Plan | Delta ON vs OFF | Interpretation |
|------|-----------------|----------------|
| `1L1095` / `1L10OD` / `1L10PR` | **SAME** (3000 NP keys) | Parent `L10 LP95` already filled these grids via inheritance; `L10 LP9595` is staged for gap-fill but first-wins after LP95 → no cell overwrite |
| Staging merge | Contains `L10 LP9595` NP/RV rows | Source gap closed; available if/when LP95 cells are incomplete |

Evidence: `evidence/issue42_regression_QuikNps_plan_delta.csv`, `…_QuikTvs_plan_delta.csv`

---

## 4. Prior Issue Fix Regression

### Issue #25 — MPOLICY padding

| Check | Result |
|-------|--------|
| `tools/validators/validate_mpolicy_width.py` | **PASS** — all MPOLICY fields exactly 10 characters |
| Spot sample (2k rows) | **PASS** — bad=0 |

### Issue #26 — MPREM mapping

| Check | Result |
|-------|--------|
| `validate_issue26_mprem.py` | **N/A environment** — hard-codes Source extracts dated **20260530** (missing; same waiver as Issue #51) |
| Spot-check `quikridr.MPREM` column populated | **PASS** — 502/501+ sample rows |

### Issue #40 / #41 CV

| Check | Result |
|-------|--------|
| QuikCvs / QuikPlCv mtime / not rewritten by #42 emit | **PASS** |

---

## 5. Schema Integrity (AGENTS.md)

| Check | Result |
|-------|--------|
| QuikNps header prefix PLAN/AGE/CNTL | **PASS** |
| NP0–NP9 factor columns present | **PASS** |
| Policy table schemas | Untouched |
| No new blank MRIDRID | N/A (no ridr emit) |
| Test_Validation MD5 = Output rates for emitted trio | **PASS** |

---

## 6. Batch / Fleet Checks

| Check | Result |
|-------|--------|
| Full policy batch re-run | **Not required** — rate-only surgical emit |
| Issue #42 validator | **PASS** (G5) |
| Regression script | **PASS** — `Issue_42/_regression_issue42.py` |
| Untouched rate family mtimes | **PASS** (all older than QuikNps emit) |
| Test_Validation publish | **PASS** (`QuikNps`, `QuikTvs`, `QuikPlTv`) |

---

## 7. Failures

None.

---

## 8. Recommendation

- [x] Advance to **Closure Agent** / **Ready for Client UAT**
- [ ] Return to **Development Agent**

**Client UAT reload:** `Output/Test_Validation/QuikNps.csv`, `QuikTvs.csv`, `QuikPlTv.csv`  
Confirm L01 plan `5L0110` NP/RV and residual CSO CV gaps still open (`L17` CV, `960 LP85-8` CV).

---

## Appendix

- Stdout: `evidence/issue42_regression_stdout.txt`
- Checks: `evidence/issue42_regression_checks.csv`
- Row counts: `evidence/issue42_regression_row_counts.csv`
- Plan deltas: `evidence/issue42_regression_QuikNps_plan_delta.csv`, `issue42_regression_QuikTvs_plan_delta.csv`
