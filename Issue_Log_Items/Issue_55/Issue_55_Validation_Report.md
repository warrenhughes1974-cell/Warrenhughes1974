# Issue #55 — Validation Report

**Issue:** #55 — Unit Issues (MUNIT floor + leading-zero decimal emit)  
**Framework stage:** Validation Agent  
**Engine version:** v57.78  
**Validation script:** `QLA_Migration/_validate_issue55_munit_floor.py` (tools v1.0)  
**Output directory:** `QLA_Migration/Output/`  
**Before snapshot:** `QLA_Migration/Staging/quikridr_pre_v5778_batch.csv`  
**Generated:** 2026-07-13  
**Verdict:** **PASS**

---

## Commands Run

```bash
python QLA_Migration/_validate_issue55_munit_floor.py
# Pre/post diff vs Staging/quikridr_pre_v5778_batch.csv (keys, floor, format-only, untouched fields)
```

Full UAT batch already completed at v57.78 (`tools/batch_tests/run_full_batch_test.py`, exit 0).

---

## 1. Trace Policy Results

| Policy | Phase | Field | Expected | Actual | Result |
|--------|------:|-------|----------|--------|--------|
| `018495BC` | 1 | MUNIT | 0 | `0.00000` | PASS |
| `018495BC` | 2 | MUNIT | 0.53 | `0.53000` | PASS |
| `018499CC` | 1 | MUNIT | 0 | `0.00000` | PASS |
| `018499CC` | 2 | MUNIT | 1.05 | `1.05000` | PASS |
| `018510C` | 1 | MUNIT | 0 | `0.00000` | PASS |
| `018510C` | 2 | MUNIT | 0.647 | `0.64700` | PASS |
| `010434419C` | 2 | MUNIT (PUA) | 0 | `0.00000` | PASS |

Leading-zero: no `.53000`-style strings on any of the above.

---

## 2. Acceptance Criteria (from Risk checklist)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | `0 < float(MUNIT) < 0.001` count = **0** | PASS (0) |
| 2 | Trace three policies: Ph1 = 0; Ph2 unchanged numerically | PASS |
| 3 | Spot-check `010434419C` PUA → 0 | PASS |
| 4 | Diff: MUNIT floor on 148 keys; row counts unchanged | PASS (148 floor; 6934 keys match) |
| 5 | Publish `quikridr` to `Output/Test_Validation/` on PASS | PASS (published earlier this run) |
| 6 | No leading-dot decimals in quikridr numeric fields | PASS (0 hits) |
| 7 | #25 MPOLICY width 10 on fleet | PASS (6934/6934) |
| 8 | #26 MPREM numeric preserved (leading-dot only) | PASS (0 leading-dot; non-MUNIT numeric Δ = 0) |

---

## 3. Source Alignment

| Check | Result |
|-------|--------|
| `NUMBER_OF_UNITS` → MUNIT map preserved | PASS — floor applied post-map only |
| Values `≥ 0.001` numerically unchanged | PASS — 0 unexpected MUNIT numeric changes |
| Leading-zero format on non-floor decimals | PASS — 145 format-only MUNIT string fixes |
| Orphan / row-key integrity | PASS — 6934 keys identical before/after |

---

## 4. Untouched Fields Confirmed

| Field / table | Check | Result |
|---------------|-------|--------|
| MVPU, MPREM, fees, MCV*, MSAVE*, MCOMMPREM | Pre vs post numeric | PASS (0 non-MUNIT numeric changes) |
| MPLAN / MPHSTAT | Pre vs post | PASS (included in non-MUNIT check) |
| MPOLICY width (#25) | `len == 10` all rows | PASS |
| MPREM (#26) | Leading-dot cleared; numeric value unchanged | PASS |
| QLAdmin NFO / display logic | Out of scope — not modified | N/A |

---

## 5. Row Counts

| Table | Count | Before | Match? |
|-------|------:|-------:|--------|
| quikridr | 6934 | 6934 | Yes |
| quikmstr | 5083 | (batch emit) | Yes (expected fleet) |
| quikprmh | 209470 | (batch emit) | Yes |

---

## 6. Impact Summary

| Metric | Value |
|--------|------:|
| MUNIT floor rows (`0 < x < 0.001` → 0) | 148 |
| MUNIT format-only (leading zero) | 145 |
| Unexpected MUNIT numeric changes | 0 |
| Non-MUNIT numeric changes | 0 |
| Rows unchanged (keys) | 6934 |

---

## 7. Failures (if any)

None.

---

## 8. Recommendation

- [x] Advance to **Regression Agent**
- [ ] Return to **Development Agent** with fixes: —

**Status:** Ready for Regression

---

## Appendix

### Validator stdout (excerpt)

```
Issue #55 validator v1.0
Row count: 6934 (expected 6934)
Sub-floor MUNIT (0 < x < 0.001): 0
Leading-dot decimal fields (total field hits): 0
Trace policies: all PASS
PUA 010434419C P2: MUNIT=0.00000 [PASS]
Issue #25 MPOLICY width (trace policies): PASS
MPREM leading-dot count: 0
RESULT: PASS
```

### Pre/post diff

- Before: `QLA_Migration/Staging/quikridr_pre_v5778_batch.csv`
- After: `QLA_Migration/Output/quikridr.csv`
- Test Validation copy: `QLA_Migration/Output/Test_Validation/quikridr.csv`

### Out of scope (documented)

- QLAdmin Edit Phase Units `3000` display (NFO×VPU / plan INITVAL)
- DBF Append Tool packing (desktop v1.5 — separate)
