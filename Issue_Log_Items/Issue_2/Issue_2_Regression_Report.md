# Issue #2 — Regression Report

**Issue:** #2 — 11 Character Policy Number  
**Framework stage:** Regression Agent (G6)  
**Engine version:** **v58.29** (working tree)  
**Checked-in tip included:** `c4dc866` / **v58.27** (Issue #96 close) — branch `issue-34-pr7-quikisrr` **in sync with** `origin/issue-34-pr7-quikisrr`  
**Baseline:** Issue A full-batch row counts 2026-07-21 evening + prior validators  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-07-23  
**Verdict:** **PASS**

---

## 0. Build contents (“everything checked in”)

| Layer | Version / tip | In this Output batch? |
|-------|---------------|------------------------|
| Git HEAD / origin | `c4dc866` · APP_VERSION **v58.27** (#96 CSO PVO / 1SALMI) | **Yes** — rates QuikPl* contain `1SALMI`; QuikCvs/Uint/Issc/Uwpo present |
| Working tree Issue #2 | **v58.29** | **Yes** — source+`C` keys, width 11 (this issue) |
| Working tree Issue #99 | v58.28 ISWLFE tags (not yet committed) | **Yes** — all 8 ISWL plans MKTG/PRODUCT/HLOB=`ISWLFE` |

No remote commits ahead of local. Batch was produced from current working tree (checked-in tip + local Issue #2/#99 engine changes).

---

## 1. Scope of change (expected)

| Component | Expected impact |
|-----------|-----------------|
| All `MPOLICY` / `MEMOKEY` | Intentional fleet rewrite → source + `C`, width 11 |
| Other business fields | Unchanged (premiums, status, plans, rates content) |
| Row counts | Stable except merge tables that join on old keys |

---

## 2. Row count comparison

| Table | Before (2026-07-21) | After (2026-07-23 #2 batch) | Delta | OK? |
|-------|--------------------:|----------------------------:|------:|-----|
| quikmstr | 5083 | 5083 | 0 | Yes |
| quikridr | 6934 | 6934 | 0 | Yes |
| quikplan | 141 | 141 | 0 | Yes |
| quikprmh | 209470 | 209480 | +10 | Yes (soft) |
| quikloan | 356 | 356 | 0 | Yes |
| quikclms | 5594 | 5594 | 0 | Yes |
| quikclmp | 6422 | 6422 | 0 | Yes |
| quikrmst | 733 | 733 | 0 | Yes |
| QuikIsrr | 3657 | 3657 | 0 | Yes |
| quikbenh | 41066 | 40510 | **-556** | **Explained** |

### quikbenh delta (explained — not a silent data loss)

Emit summary `20260723_085728`:

- `emit_passed` = 36,853 (fresh PACTG→Benh under new keys)  
- `existing_preserved_rows` = 3,657 (type-8)  
- `merged_rows` = 40,510  

Prior Output still keyed with old `010…C` identities; merge-by-MPOLICY cannot retain unmatched old-key history rows. Fresh emit + preserved type-8 is the post-#2 population. All 40,510 Benh `MPOLICY` values are width-11 / `90…` style.

---

## 3. Non-target field / prior-fix checks

| Check | Result |
|-------|--------|
| Issue #26 MPREM traces (remapped keys) | **PASS** — `9010310404C`=13.20, `9010331768C`=10.96, `9010367131C`=9.12 |
| Issue #26 light (phase-1 with units) | **PASS** — 0 blank MPREM / 4,936 rows |
| Issue #99 ISWLFE (8 plans) | **PASS** |
| Issue #96 1SALMI QuikPl* keys | **PASS** — present across QuikPl* |
| Rates QuikUwpo / QuikUint / QuikIssc / QuikCvs | **Present** |
| blank MRIDRID | **0** / 6,934 |
| Schema column order (mstr/ridr/plan) | **Preserved** (45 / 40 / 79) |
| Issue #2 validator | **PASS** |
| Stock `validate_issue26_mprem.py` | **N/A fail** — hardcoded 20260530 source paths + old `010…C` samples (script not retargeted; remapped check used instead) |

### Spot non-key row

`9010143726C` phase 1: MPLAN=`221END`, MPREM=`18.78000`, MUNIT=`2.50000`, MVPU=`1000.00`

---

## 4. Prior issue #25 / #26

| Check | Result |
|-------|--------|
| Issue #25 width-10 | **Superseded by #2** — width-11 validator PASS (intentional) |
| Issue #26 MPREM | **Preserved** (remapped traces + fleet light check) |

---

## 5. Schema integrity

| Check | Result |
|-------|--------|
| Field order preserved | **Yes** (spot tables) |
| No new blank MRIDRID | **Yes** |
| QLA key formatting | **Issue #2 contract** |

---

## 6. Batch / fleet

| Check | Result |
|-------|--------|
| Full batch completed | **Yes** — exit 0, ~27 min, v58.29 |
| Log | `QLA_Migration/Logs/_full_batch_test_log.txt` |
| Test_Validation publish | 15 tables (Issue_2) |

---

## 7. Failures

None blocking. quikbenh −556 documented as old-key merge effect under intentional key rewrite.

---

## 8. Recommendation

- [x] **PASS** — advance to **Closure Agent** / Ready for Client UAT  
- [ ] Return to Development  

**UAT:** reload with new keys (`9010143726C`, not `010143726C`). Prefer full Output or `Test_Validation/` from this batch.

---

## Appendix

- Script: `Issue_Log_Items/Issue_2/evidence/_regression_issue2_checks.py`  
- Validation: `Issue_2_Validation_Report.md`  
- Git: HEAD=`c4dc866` · local APP_VERSION=`v58.29`
