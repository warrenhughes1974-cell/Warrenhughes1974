# Issue #51 — Regression Report

**Issue:** #51 — Missing Interest Table (A60MIR / A96DAR)  
**Framework stage:** Regression Agent  
**Engine version:** v57.76  
**Baseline:** Pre-#51 Output rates package (QuikAint absent); policy CSVs unchanged by this issue  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-07-11  
**Model:** Cursor Grok 4.5 (locked Regression stage)  
**Verdict:** **PASS**

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|-----------|-----------------|
| `Output/rates/QuikAint.csv` | **New** — 2 stub rows |
| `rate_csv_manifest.csv` | +1 QuikAint line |
| Policy `quik*.csv` tables | No change |
| QuikUint / factor / key tables | No MIR/DAR pollution; other rates unchanged |
| #25 / #26 / #21D | Preserved |

---

## 2. Row Count Comparison

| Table | After | Expected delta vs pre-#51 | OK? |
|-------|------:|--------------------------:|-----|
| quikmstr | 5083 | 0 | **Yes** |
| quikridr | 6934 | 0 | **Yes** |
| quikplan | 141 | 0 | **Yes** |
| quikprmh | 209470 | 0 | **Yes** |
| quikclid | 34449 | 0 | **Yes** |
| quikclnt | 13597 | 0 | **Yes** |
| quikdvdp | 5083 | 0 | **Yes** |
| quikmemo | 337882 | 0 | **Yes** |
| rates/QuikAint | 2 | **+2** (intentional) | **Yes** |
| rates/QuikUint | 0 | 0 | **Yes** |
| rates/QuikCvs | 38047 | 0 | **Yes** |
| rates/QuikGps | 17137 | 0 | **Yes** |

Evidence: `evidence/issue51_regression_row_counts.csv`

---

## 3. Non-Target Field Diff

| Table | Column | Rows changed | OK? |
|-------|--------|-------------:|-----|
| quikridr | all | 0 (code path untouched) | **Yes** |
| QuikUint | MPLAN | 0 MIR/DAR | **Yes** |
| quikplan A60MIR/A96DAR | DEPINT/NFOINT/etc. | 0 | **Yes** |

---

## 4. Prior Issue Fix Regression

### Issue #25 — MPOLICY padding

| Check | Result |
|-------|--------|
| `tools/validators/validate_mpolicy_width.py` | **PASS** — all MPOLICY fields exactly 10 characters |
| Sample `010348734C` | len=10 |

### Issue #26 — MPREM mapping

| Check | Result |
|-------|--------|
| `validate_issue26_mprem.py` | Script hard-codes Source extract dated **20260530** (missing in current package) — **N/A environment**, not #51 regression |
| Spot-check A60MIR MPREM | Still populated (e.g. 010335095C = 9.20000) — **PASS** |

### Issue #21D / #32

| Check | Result |
|-------|--------|
| QuikUint not expanded to MIR/DAR | **PASS** |
| No MDEPINT code path touched | **PASS** (diff scope) |

---

## 5. Schema Integrity (AGENTS.md)

| Check | Result |
|-------|--------|
| QuikAint field order Help §7.31 | **PASS** |
| Policy table schemas | Untouched |
| No new blank MRIDRID | N/A (no ridr emit change) |
| QLA formatting | Rates N(7.4) as `0.0000` |

---

## 6. Batch / Fleet Checks

| Check | Result |
|-------|--------|
| Full policy batch re-run | **Not required** — rate-only surgical emit |
| Issue #51 validator | **PASS** |
| Rate package includes QuikAint | **PASS** (manifest + file) |
| Test_Validation publish | **PASS** (`Output/Test_Validation/rates/QuikAint.csv`) |

---

## 7. Verdict

**PASS** — Ready for Closure / Client UAT.

**Client UAT instruction:** Load updated `QuikAint.csv` (or DBF) with the rate package; open Projected Values on `010348734C` (A60MIR) and an A96DAR sample. Expect no “Interest table not found” endless loop. If loop persists after QuikAint is confirmed loaded, escalate QuikAing/QuikAinf stubs per Risk Conditional Go fallback E.
