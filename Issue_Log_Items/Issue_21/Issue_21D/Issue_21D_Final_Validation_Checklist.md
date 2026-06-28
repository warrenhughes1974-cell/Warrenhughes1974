# Issue #21D — Final Validation Checklist

**Date:** 2026-06-27  
**Converter version:** v57.36  
**Validation Agent:** Complete

---

## Full batch

| # | Check | Status |
|---|-------|--------|
| 1 | v57.36 full batch output used (not v57.35) | ✅ |
| 2 | Batch completed without conversion error | ✅ |

---

## Track A — MDEPINT

| # | Check | Expected | Actual | Status |
|---|-------|----------|--------|--------|
| A1 | Eight ISWL MPLAN codes in batch | 8 | 8 | ✅ |
| A2 | ISWL policies @ 4.50% | 2,268 | 2,268 | ✅ |
| A3 | Non-ISWL policies @ 4.00% | 2,815 | 2,815 | ✅ |
| A4 | No non-ISWL MDEPINT change | 0 changes | 0 | ✅ |
| A5 | Sample 010713704C @ 4.50 | 4.50 | 4.50 | ✅ |
| A6 | `validate_issue21d_mdepint.py` | PASS | PASS | ✅ |
| A7 | NFOINT unchanged (ISWL) | A | A | ✅ |

---

## Track B1 — quikclnt

| # | Check | Expected | Actual | Status |
|---|-------|----------|--------|--------|
| B1 | Seven B1-target policies corrected | 7/7 | 7/7 | ✅ |
| B2 | quikclnt row delta | +12 | +12 | ✅ |
| B3 | Both-blank population | 9 | 9 | ✅ |
| B4 | Remaining blank = RNA deficiency only | Yes | Yes (9 policies) | ✅ |
| B5 | MPRIMID='I' leak | 0 | 0 | ✅ |
| B6 | quikclid IDs missing from quikclnt | 0 (excl. 598766) | 0 | ✅ |
| B7 | `validate_issue21d_blank_names.py` | PASS | PASS | ✅ |
| B8 | Golden harness (B1 scope) | No I-leak | PASS | ✅ |

---

## Track B2 — excluded

| # | Check | Status |
|---|-------|--------|
| C1 | Track B2 not in acceptance criteria | ✅ Excluded |
| C2 | 9 RNA-deficient policies documented | ✅ |
| C3 | 010713704C blank names not counted as fail | ✅ |

---

## Protected regressions

| # | Issue | Status |
|---|-------|--------|
| R1 | #25 MPOLICY | ✅ PASS |
| R2 | #26 MPREM | ✅ PASS |
| R3 | #28 Plan mapping | ✅ PASS |
| R4 | #21M QUIKMEMO | ✅ PASS |
| R5 | #21M-FU DBF | ✅ PASS |
| R6 | #21K fleet/MUNIT | ⚠️ N/A (DBF artifact) |
| R7 | v57.28 MPRIMID | ✅ PASS |

---

## Output delta

| # | Check | Status |
|---|-------|--------|
| D1 | Only quikdvdp MDEPINT + quikclnt rows changed | ✅ |
| D2 | No unexpected table row-count changes | ✅ |

---

## Validation decision

```text
PASS WITH OBSERVATIONS
```

**Observations (non-blocking):**
1. Track B2 — 9 policies remain both-blank pending client RNA (EXT-B1)
2. Golden validator flags 010713704C — expected B2 scope
3. #21K validators not run — missing DBF reload artifact

---

*Checklist complete.*
