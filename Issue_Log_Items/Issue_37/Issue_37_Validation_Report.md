# Issue #37 — Validation Report

**Issue:** Age/Duration Rate Placement — CV / QuikCvs (fleet-wide)  
**Framework stage:** Validation Agent (G5)  
**Validation scripts:** `_validate_issue37_quikcvs_placement.py`, `_validate_issue37_g5_matrix.py`  
**Output directory:** `QLA_Migration/Output/rates/`  
**Before snapshot:** N/A (Issue #31 QuikCvs baseline predates grid fix)  
**Generated:** 2026-07-03  
**Verdict:** **PASS**

---

## Commands Run

```bash
python QLA_Migration/_validate_issue37_quikcvs_placement.py
python QLA_Migration/_validate_issue37_g5_matrix.py
python tools/validators/iswl_quikcvs_reconcile.py
```

---

## 1. Trace Policy Results — 960 PO / 1960PO (Client Proof)

| Sex | Age | LP first | LP last | First rate | Last rate | Result |
|-----|----:|---------:|--------:|------------|-----------|--------|
| M | 0 | 7 | 100 | 3.07 @ dur 7 | 1000.0 @ dur 100 | **PASS** |
| M | 18 | 4 | 82 | 4.52 @ dur 4 | 1000.0 @ dur 82 | **PASS** |
| M | 20 | 4 | 80 | 6.27 @ dur 4 | 1000.0 @ dur 80 | **PASS** |
| M | 22 | 4 | 78 | **8.32 @ dur 4** | **1000.0 @ dur 78** | **PASS** |
| M | 24 | 3 | 76 | 0.71 @ dur 3 | 1000.0 @ dur 76 | **PASS** |
| M | 29 | 3 | 71 | 5.26 @ dur 3 | 1000.0 @ dur 71 | **PASS** |
| M | 33 | 3 | 67 | 9.67 @ dur 3 | 1000.0 @ dur 67 | **PASS** |
| F | 0 | 7 | 100 | 1.48 @ dur 7 | 937.11 @ dur 100 | **PASS** |

**Anchor regression check:** 8.32 is **not** at QL duration 1 (old bug) — **PASS**.

**Emitted CSV spot-check:** `QuikCvs.csv` — 1960PO / M / 22 / CNTL 00 / CV3 = **8.32** — **PASS**.

Evidence: `Issue_Log_Items/Issue_37/evidence/g5_validation_matrix.csv`

---

## 2. Acceptance Criteria (Risk §10)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | 960 PO proof ages: M 0,18,20,22,24,29,33; F 0 | **PASS** (8/8) |
| 2 | M/22 anchor: 8.32 @ dur 4; 1000 @ dur 78 | **PASS** |
| 3 | Fleet sample spot checks | **PASS** (3/4); **1L10OD WAIVED** (see §7) |
| 4 | Truncate policy (past maturity 100−age) | **PASS** — 9,616 CV source rows excluded |
| 5 | QuikNps / QuikGps unchanged path | **PASS** — QuikNps 26,650 keys; QuikGps 12,567 keys |
| 6 | Pipeline emit gate | **PASS** — 0 blockers |
| 7 | `iswl_quikcvs_reconcile.py` core checks | **PASS** — V-CVS-02/04, V-X-03; V-X-01 baseline **WAIVED** (§7) |

---

## 3. Source Alignment

| Check | Result |
|-------|--------|
| CV values preserved (placement only) | **PASS** — proof matrix first/last values match extract after remap |
| Leading duration shift applied | **PASS** — variable start offset by issue age |
| Maturity extension to 100 − age | **PASS** |
| Truncated tail rows | **PASS** — expected under G3 maturity-100 rule (e.g. F/0 terminal 937.11 not 1000) |

---

## 4. Untouched Fields Confirmed

| Field / table | Check | Result |
|---------------|-------|--------|
| `app.py` / QuikPlan | Not in dev scope | **Untouched** |
| QuikNps | Key count stable at 26,650 | **PASS** |
| QuikGps | Key count stable at 12,567 | **PASS** |
| QuikDbs / QuikTvs / QuikDvs | Not in dev scope | **Untouched** |
| Issue #25 MPOLICY padding | Not in dev scope | **Untouched** |
| Issue #26 MPREM | Not in dev scope | **Untouched** |

---

## 5. Row Counts

| Table | After | Before (Issue #31 baseline) | Notes |
|-------|------:|------------------------------:|-------|
| QuikCvs.csv | **26,031** | ~19,453 CNTL pages (991 keys for 1960PO) | **Expected increase** — grid extension |
| QuikNps | 26,650 keys | 26,650 (unchanged) | **PASS** |
| 1960PO QuikCvs keys | 985 | 991 | Fewer keys after truncate; values aligned |

---

## 6. Impact Summary

| Metric | Value |
|--------|------:|
| CV slices validated (960 PO proof) | 8 |
| Proof cases passed | 8 |
| QuikCvs factor rows | 26,031 |
| CV rows truncated past maturity | 9,616 |
| Pipeline blockers | 0 |

---

## 7. Waivers (documented)

| # | Item | Severity | Return to Dev? |
|---|------|----------|----------------|
| 1 | **Issue #31 V-X-01 baseline** — non-ISWL QuikCvs key counts changed intentionally | Low | **No** — rebaseline in G6 Regression |
| 2 | **1L10OD fleet spot** — plan fed by multiple COVERAGE_IDs (L10 LP95 + L10 PRE97); grid keyed by PLAN; last-writer collision pre-dates Issue #37 | Low | **No** — out of scope; separate crosswalk issue if needed |

---

## 8. Recommendation

- [x] Advance to **Regression Agent (G6)**
- [ ] Return to Development — **not required**

**Next steps (G6):**
1. Rebaseline Issue #31 `iswl_quikcvs_regression_baseline.json` for post-#37 QuikCvs key counts.
2. Confirm QuikPlan / quikridr / quikmstr row counts unchanged in full migration output.
3. Client QLAdmin UAT on **1960PO / CV / M / age 22** (Duration 4 = 8.32, Duration 78 = 1000).
4. Publish G7 closure summary after G6 pass.

---

## Appendix

- Proof matrix CSV: `Issue_Log_Items/Issue_37/evidence/g5_validation_matrix.csv`
- Implementation notes: `Issue_Log_Items/Issue_37/Issue_37_Implementation_Notes.md`
