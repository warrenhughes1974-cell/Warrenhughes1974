# Issue #146 — Regression Report

**Issue:** #146 — Non-VB Unit Reductions (PC / former-vanish 0561 exclude)  
**Framework stage:** Regression Agent  
**Engine version:** v59.03  
**Baseline:** leftover Output after #145B (205 QuikIsrr / 50 policies)  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-08-26  
**Verdict:** **PASS**

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|-----------|-----------------|
| QuikIsrr + PS- clms + phase-0 clmp + type-8 benh | Remove 104 allowlist rows |
| Other leftover 0561s | Unchanged (101 rows / 30 policies) |
| quikmstr / quikridr / quikspec / PACTG | No change |
| #145B VB exclude | Still 0 VB QuikIsrr |

---

## 2. Row Count Comparison

| Table | Before | After | Delta | OK? |
|-------|-------:|------:|------:|-----|
| QuikIsrr | 205 | 101 | −104 | Yes |
| quikclms | 2592 | 2488 | −104 | Yes |
| quikclmp | 3084 | 2980 | −104 | Yes |
| quikbenh | 41560 | 41456 | −104 | Yes |
| quikridr MUNIT (golds) | 5 / 5 / 25 | 5 / 5 / 25 | 0 | Yes |
| quikbenh 10/11/12 | 4118 / 14156 / 19135 | same | 0 | Yes |

---

## 3. Non-Target Field Diff (affected tables)

| Table | Column | Rows changed | OK? |
|-------|--------|-------------:|-----|
| QuikIsrr | allowlist policies | 104 removed | Yes |
| QuikIsrr | keep golds / other leftover | 0 | Yes |
| quikridr | MUNIT / MPREM | 0 | Yes |
| quikspec | VANISH / SOR_POL | 0 | Yes |

---

## 4. Prior Issue Fix Regression

| Check | Result |
|-------|--------|
| #25 / #2 MPOLICY | Not rewritten |
| #26 MPREM | Not touched |
| #145 VANISH | #145B validator PASS (VB golds T) |
| #145B VB 0561 exclude | PASS — 0 VB QuikIsrr; keep golds $271 / $716.40 |
| #54 loan benh | Floors intact |
| #156 SOR_POL | Schema / table not in this change |

Dry-run PR-7: VB excluded 3,452; #146 excluded 104; leak=[]; leftover candidates 101 / 30.

---

## 5. Fleet Impact

Intentional remove of 20 former-vanish policies only. 30 leftover 0561 policies remain, including the two real-surrender golds.

---

## Verdict

**PASS.** Safe to Close.
