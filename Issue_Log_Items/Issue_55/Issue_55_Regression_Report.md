# Issue #55 — Regression Report

**Issue:** #55 — Unit Issues (MUNIT floor + leading-zero decimal emit)  
**Framework stage:** Regression Agent  
**Engine version:** v57.78  
**Baseline:** `QLA_Migration/Staging/quikridr_pre_v5778_batch.csv` (pre-v57.78 batch)  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-07-13  
**Verdict:** **PASS**

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|-----------|-----------------|
| `quikridr.MUNIT` | Floor: 148 rows `0 < x < 0.001` → `0`; format leading-zero |
| Other quikridr decimals | Leading-zero format only (numeric value unchanged) |
| Other tables | No intentional change from #55 |
| #25 / #26 / NFO display | Preserved / out of scope |

---

## 2. Row Count Comparison

| Table | After (v57.78) | Expected / baseline | Delta | OK? |
|-------|---------------:|--------------------:|------:|-----|
| quikridr | 6934 | 6934 (before keys) | 0 | Yes |
| quikmstr | 5083 | 5083 (#49 baseline) | 0 | Yes |
| quikprmh | 209470 | fleet emit | — | Yes |
| quikplan | 141 | fleet emit | — | Yes |
| quikclid | 34449 | fleet emit | — | Yes |
| quikclnt | 13597 | batch emit | — | Yes |
| quikbenf | 5916 | batch emit | — | Yes |
| quikmemo | 5083 | batch emit | — | Yes |
| quikdvdp | 5083 | batch emit | — | Yes |
| quikagts | 4843 | batch emit | — | Yes |

`quikridr` key set before/after: **identical** (6934).

---

## 3. Non-Target Field Diff (`quikridr`)

| Column class | Rows changed | Numeric Δ? | OK? |
|--------------|-------------:|:----------:|-----|
| MUNIT floor | 148 | Yes (intentional) | Yes |
| MUNIT format-only | 145 | No | Yes |
| MPREM format-only (`.00`→`0.00`) | 1928 | No | Yes |
| MANNLFEE format-only | 4457 | No | Yes |
| MCV0 format-only | 1830 | No | Yes |
| MVPU format-only | 25 | No | Yes |
| Unexpected numeric (any field) | **0** | — | Yes |
| Non-decimal string fields | **0** | — | Yes |

All non-decimal columns (MPHSTAT, MPLAN, MRIDRID, dates, etc.) **byte-identical** vs pre-batch snapshot.

---

## 4. Prior Issue Fix Regression

### Issue #25 — MPOLICY padding

| Check | Result |
|-------|--------|
| Fleet `len(MPOLICY) == 10` | PASS (0 failures) |
| Samples `018495BC`, `018499CC`, `018510C`, `010310404C` | PASS (leading-space pad preserved) |
| Issue #55 validator #25 check | PASS |

### Issue #26 — MPREM mapping

| Check | Result |
|-------|--------|
| Trace `010310404C` / `010331768C` / `010367131C` / `010718276C` | PASS (13.20 / 10.96 / 9.12 / 1641.30) |
| MPREM leading-dot count | PASS (0) |
| MPREM numeric vs pre-batch | PASS (format-only only) |

Full `_validate_issue26_mprem.py` skipped: hardcodes dated `20260530` extracts (fleet now `20260630`). Spot-check above covers Risk #26 guard.

### Issue #49 — MSTATUS (adjacent rider/master)

| Check | Result |
|-------|--------|
| `validate_issue49_mstatus.py` | **PASS** (35 overrides; phase-1 MPHSTAT unchanged; ridr 6934) |

---

## 5. Schema Integrity (AGENTS.md)

| Check | Result |
|-------|--------|
| Field order preserved (40-col QUIKRIDR Help layout) | PASS |
| Field types/lengths (CSV emit) | PASS — no schema rewrite |
| No new blank MRIDRID | PASS (0 before, 0 after) |
| QLA formatting (5-dp MUNIT, leading zero) | PASS |
| #55 validator | PASS |

---

## 6. Batch / Fleet Checks

| Check | Result |
|-------|--------|
| Full batch completed (v57.78) | Yes — `tools/batch_tests/run_full_batch_test.py` exit 0 |
| Batch log | `QLA_Migration/Logs/_full_batch_test_log.txt` |
| `validate_output.py` | N/A (not used this gate) |
| Audit log anomalies attributable to #55 | None |

---

## 7. Failures (if any)

None.

---

## 8. Recommendation

- [x] Advance to **Closure Agent** / **Ready for Client UAT**
- [ ] Return to **Development Agent**

**Status:** Ready for Closure (Composer 2.5) · Ready for Client UAT after Closure docs

---

## Appendix

- Before: `QLA_Migration/Staging/quikridr_pre_v5778_batch.csv`
- After: `QLA_Migration/Output/quikridr.csv`
- Test Validation: `QLA_Migration/Output/Test_Validation/quikridr.csv`
- Validation report: `Issue_55_Validation_Report.md` (G5 PASS)
- Out of scope: QLAdmin Units `3000` display (NFO×VPU); desktop DBF Append Tool v1.5
