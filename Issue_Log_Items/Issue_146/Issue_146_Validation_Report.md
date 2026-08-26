# Issue #146 — Validation Report

**Issue:** #146 — Non-VB Unit Reductions (PC / former-vanish 0561 exclude)  
**Framework stage:** Validation Agent  
**Engine version:** v59.03  
**Validation script:** `tools/validators/validate_issue146_pc_isrr.py`  
**Output directory:** `QLA_Migration/Output/`  
**Before snapshot:** apply summary (205 → 101 QuikIsrr)  
**Generated:** 2026-08-26  
**Verdict:** **PASS**

---

## Commands Run

```text
python Issue_Log_Items/Issue_146/tools/apply_issue146_pc_isrr_exclude.py
python tools/validators/validate_issue146_pc_isrr.py
python tools/validators/validate_issue145b_vb_isrr_exclude.py
python Issue_Log_Items/Issue_34/tools/quikisrr_pr7_emit.py --dry-run
python tools/publish_test_validation.py --issue Issue_146 quikisrr quikclms quikclmp quikbenh
```

---

## 1. Trace Policy Results

| Policy | Field | Expected | Actual | Result |
|--------|-------|----------|--------|--------|
| 9011077629C | QuikIsrr | 0 | 0 | PASS |
| 9010817956C | QuikIsrr | 0 | 0 | PASS |
| 9010808831C | QuikIsrr | 0 | 0 | PASS |
| 9011077629C | MUNIT | 5.00000 | 5.00000 | PASS |
| 9010817956C | MUNIT | 5.00000 | 5.00000 | PASS |
| 9010808831C | MUNIT | 25.00000 | 25.00000 | PASS |
| 9010761639C | QuikIsrr | 1 / $271.00 | 1 / $271.00 | PASS |
| 9010760840C | QuikIsrr | 2 / $716.40 | 2 / $716.40 | PASS |
| 20 allowlist | PS- clms / phase-0 clmp / type-8 benh | 0 | 0 | PASS |

---

## 2. Acceptance Criteria (from Risk checklist)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Allowlist golds have 0 QuikIsrr | PASS |
| 2 | Same three have 0 companions | PASS |
| 3 | 9010761639C still 1 / $271; 9010760840C still 2 / $716.40 | PASS |
| 4 | QuikIsrr leftover = 101 / 30 on 6/30 | PASS (101 rows; dry-run 30 policies) |
| 5 | Gold MUNIT unchanged | PASS |
| 6 | #145B smoke still PASS | PASS |
| 7 | quikbenh 10/11/12 floors unchanged | PASS (4118 / 14156 / 19135) |

---

## 3. Source Alignment

| Check | Result |
|-------|--------|
| Allowlist 0561s excluded from emit | PASS — dry-run `issue146_excluded_rows=104`, leak=[] |
| VB exclude still 3,452 | PASS |
| Leftover candidates 101 / 30 | PASS |
| PACTG / VANISH / MUNIT not rewritten | PASS |

---

## 4. Untouched Fields Confirmed

| Field / table | Check | Result |
|---------------|-------|--------|
| quikridr.MUNIT on golds | validator | PASS |
| quikspec.VANISH | #145B validator | PASS |
| quikbenh 10/11/12 | #145B floors | PASS |
| Keep-gold 0561s | exact row/amount | PASS |

---

## 5. Row Counts

| Table | Before | After | Delta |
|-------|-------:|------:|------:|
| QuikIsrr | 205 | 101 | −104 |
| quikclms | 2592 | 2488 | −104 |
| quikclmp | 3084 | 2980 | −104 |
| quikbenh | 41560 | 41456 | −104 |

---

## 6. Test_Validation

Published: `quikisrr.csv`, `quikclms.csv`, `quikclmp.csv`, `quikbenh.csv` for Issue_146.

---

## Verdict

**PASS.** Stop for Validation readout. Regression / Closure not run in this step.
