# Issue #136 — Regression Report

**Issue:** #136 — QuikPlan PVO Flags (Real Variation Only)  
**Framework stage:** Regression  
**Engine version:** v58.62  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-08-02  
**Verdict:** **PASS**

---

## 1. Scope of change (expected)

| Component | Expected impact |
|-----------|-----------------|
| `quikplan` VARY / PLANVALOPT | Band/State/DV/DB false positives cleared; Gender/UW retained where real |
| Rate factor/key CSVs | Unchanged this close (flags-only re-enrich) |
| Claims / policy tables | Unchanged |

---

## 2. Candidate vs non-candidate

| Check | Result |
|-------|--------|
| 1658C1 Band/State/DV/DB | **PASS** — all N; GDVARYGP/UWVARYGP Y |
| Fleet Band Y | **PASS** — 0 plans |
| Fleet State Y | **PASS** — 0 plans |
| DV flags without QuikDvs | **PASS** — 0 (validator) |
| DB flags without QuikDbs | **PASS** — 0 (validator) |
| GP Gender/UW on 1658C1 / 1659C2 class | **PASS** — retained where multi-value keys + factors |

---

## 3. Prior issue fence

| Check | Result |
|-------|--------|
| Issue #70 LOANINTX | Not modified by #136 |
| Issue #135 claims | Not modified by #136 |
| A3 default-only PUA clear | Still applied after enrichment |
| A8e annuity PVO clear | Still applied |

---

## 4. Schema integrity

QuikPlan schema / field order unchanged — only flag cell values updated.

---

## 5. Unit tests

`tests/test_a11h_real_rate_only_flags.py` + `tests/test_gp_variation_regression.py` + A11 A3 rules — **PASS**
