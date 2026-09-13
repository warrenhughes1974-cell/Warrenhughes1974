# Issue #166 — Validation Report

**Issue:** #166 — Div Accumulation Crediting
**Framework stage:** Validation Agent
**Engine version:** v59.13
**Validation script:** `tools/validators/validate_issue166_mdepint.py` v1.0
**Output directory:** `QLA_Migration/Output/`
**Before snapshot:** `Issue_Log_Items/Issue_166/evidence/quikdvdp_pre_issue166.csv`
**Generated:** 2026-09-13
**Verdict:** **PASS**

---

## Commands Run

```bash
python -m unittest qla_core.tests.test_mdepint_issue166 -v
python Issue_Log_Items/Issue_166/scripts/rebatch_quikdvdp.py
set QLA_VALUATION_DATE=20260831
python tools/validators/validate_issue166_mdepint.py
python tools/validators/validate_issue21d_mdepint.py
python tools/validators/validate_issue95_quikuint_pdinttbl.py
python Issue_Log_Items/Issue_116/scripts/validate_issue116.py
python tools/publish_test_validation.py --clean --issue Issue_166 quikdvdp
```

---

## 1. Trace Policy Results

| Policy | Field | Expected | Actual | Result |
|---|---|---|---|---|
| 9010728947C | MDEPINT | 3.50 | 3.50 | PASS |
| 9010728947C | MINTDATE | 20250904 | 20250904 | PASS |
| 9010728947C | MDEPOSIT | 1875.38 | 1875.38 | PASS |
| 9010713704C | MDEPINT | 4.50 | 4.50 | PASS |
| 9010824098C | MDEPINT | 4.50 | 4.50 | PASS |
| 901122D991C | MDEPINT | 2.00 | 2.00 | PASS |
| 9010380808C | MDEPINT / MINTDATE | 3.50 / 20251201 | 3.50 / 20251201 | PASS |

---

## 2. Acceptance Criteria (from Risk checklist)

| # | Criterion | Result |
|---|---|---|
| 1 | Gold 3.50 / 20250904 / 1875.38 / MINTYTD 0.00 | PASS |
| 2 | ISWL control 4.50 | PASS |
| 3 | 1668SP 4.50 | PASS |
| 4 | SAL 2.00 | PASS |
| 5 | #116 gold paid-to ≤ valuation; deposit 9220.33 | PASS |
| 6 | MDEPINT only 2.00 / 3.50 / 4.50 | PASS |
| 7 | Row count 5,083 | PASS |
| 8 | #95 QuikUint smoke | PASS |
| 9 | #116 no future paid-to on deposit rows | PASS (0) |
| 10 | Revised #21D validator | PASS |
| 11 | Publish Test_Validation quikdvdp | PASS |

`validate_issue38_mdeposit.py` still points at a missing `PPBENTYP_…_20260530.csv`. That is a pre-existing path pin, not an #166 field fail. Gold deposit matches current 8/31 source.

---

## 3. Source Alignment

| Check | Result |
|---|---|
| Residual / SAL / SP MDEPINT vs #95 buckets | 0 mismatches |
| Year-end leftover on deposit rows | 0 |
| Overlay uses MEFFDATE vs 20260831 | Gold 19840904 → 20250904 |

---

## 4. Untouched Fields Confirmed

| Field / table | Check | Result |
|---|---|---|
| rates/QuikUint | #95 validator | PASS (107 / 83) |
| ISWL MDEPINT | 2,268 still 4.50 | PASS |
| quikdvdp row count | 5,083 | PASS |
| Gold MDEPOSIT | 1875.38 vs pre | PASS |
| MPOLICY / MPREM | not in this emit | N/A |

Six non-gold deposits moved on the 8/31 re-emit (PPBENTYP/641 refresh). Gold did not.

---

## 5. Row Counts

| Table | Count | Before | Match? |
|---|---:|---:|---|
| quikdvdp | 5,083 | 5,083 | Yes |

---

## 6. Impact Summary

| Metric | Value |
|---|---:|
| MDEPINT rows changed | 2,815 |
| MINTDATE overlays | 21 |
| ISWL unchanged | 2,268 |
| QuikUint rows changed | 0 |

---

## 7. Failures

None on the #166 script. #38 source-path FAIL is environmental (20260530 extract absent).

---

## 8. Recommendation

- [x] Validation **PASS** — stop for readout (do not auto-run Regression/Closure)
- [ ] Advance to Regression when Warren says to continue

---

## Appendix

- Pre snapshot: `Issue_Log_Items/Issue_166/evidence/quikdvdp_pre_issue166.csv`
- Rebatch log: `QLA_Migration/Logs/_issue166_quikdvdp_rebatch_log.txt`
- Test_Validation: `QLA_Migration/Output/Test_Validation/quikdvdp.csv`
