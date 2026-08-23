# Issue #145B — Validation Report

**Issue:** #145B — Vanish 0561s Out of ISRR  
**Framework stage:** Validation Agent  
**Engine version:** v59.01  
**Validation script:** `tools/validators/validate_issue145b_vb_isrr_exclude.py`  
**Output directory:** `QLA_Migration/Output/`  
**Before snapshot:** apply audit `Issue_145B/evidence/issue145b_apply_summary.json`  
**Generated:** 2026-08-23  
**Verdict:** **PASS**

---

## Commands Run

```bash
python Issue_Log_Items/Issue_145B/tools/apply_issue145b_vb_isrr_exclude.py
python tools/validators/validate_issue145b_vb_isrr_exclude.py
python Issue_Log_Items/Issue_34/tools/quikisrr_pr7_emit.py --dry-run
python tools/publish_test_validation.py --clean --issue Issue_145B quikisrr quikclms quikclmp quikbenh
```

---

## 1. Trace Policy Results

| Policy | Field | Expected | Actual | Result |
|--------|-------|----------|--------|--------|
| 9010815236C | QuikIsrr rows | 0 | 0 | PASS |
| 9011050114C | QuikIsrr rows | 0 | 0 | PASS |
| 9011069610C | QuikIsrr rows | 0 | 0 | PASS |
| 9010815236C | MUNIT | 25 | 25.00000 | PASS |
| 9011050114C | MUNIT | 25 | 25.00000 | PASS |
| 9011069610C | MUNIT | 50 | 50.00000 | PASS |
| 9010761639C | QuikIsrr | 1 / $271.00 | 1 / $271.00 | PASS |
| 9010760840C | QuikIsrr | 2 / $716.40 | 2 / $716.40 | PASS |

---

## 2. Acceptance Criteria (from Risk checklist)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | VB golds have 0 QuikIsrr | PASS |
| 2 | Same three have 0 PS- clms / phase-0 clmp / type-8 benh | PASS |
| 3 | #146 leftovers unchanged | PASS |
| 4 | QuikIsrr leftover 205 / 50 on 6/30 | PASS |
| 5 | VANISH T on VB golds, F on #146 | PASS |
| 6 | Gold MUNIT unchanged | PASS |
| 7 | quikbenh types 10/11/12 floors held | PASS |
| 8 | Emit dry-run: 3452 VB excluded, 0 leak | PASS |

---

## 3. Source Alignment

| Check | Result |
|-------|--------|
| PPOLC BILLING_REASON=VB → no QuikIsrr | PASS (0 VB rows remain) |
| Non-VB 0561s still emitted | PASS (205 leftover) |
| PACTG not modified | PASS |

---

## 4. Untouched Fields Confirmed

| Field / table | Check | Result |
|---------------|-------|--------|
| quikridr.MUNIT golds | 25 / 25 / 50 / 25 / 35 | PASS |
| quikspec.VANISH | T on VB golds | PASS |
| quikbenh 10/11/12 | 4118 / 14156 / 19135 | PASS |
| #146 QuikIsrr | kept | PASS |

---

## 5. Row Counts

| Table | Before | After | Match? |
|-------|-------:|------:|--------|
| QuikIsrr | 3657 | 205 | Yes (−3452) |
| quikclms | 6044 | 2592 | Yes (−3452) |
| quikclmp | 6536 | 3084 | Yes (−3452) |
| quikbenh | 45012 | 41560 | Yes (−3452) |

---

## 6. Impact Summary

| Metric | Value |
|--------|------:|
| VB 0561 rows removed (each of 4 tables) | 3,452 |
| Leftover QuikIsrr rows | 205 |
| Leftover QuikIsrr policies | 50 |

---

## 7. Failures (if any)

None.

---

## 8. Recommendation

- [x] Advance to **Regression Agent** when Warren says to continue
- [ ] Return to **Development Agent**

---

## Appendix

- Apply audit: `Issue_Log_Items/Issue_145B/evidence/issue145b_apply_summary.json`
- Test_Validation: `quikisrr.csv`, `quikclms.csv`, `quikclmp.csv`, `quikbenh.csv`
