# Issue 173 — Risk Review Report

**Issue:** 173 — ISWL negative fund balances  
**Framework stage:** Risk Agent  
**Status:** Conditional Go  
**Fallback simulated:** Ending-balance-only change. In-month floor left in place.  
**Generated:** 2026-09-25  
**Agent/script:** `Issue_173/tools/_count_negative_funds.py` against current Output and the 6/30 PFNDR extract

**Status note:** Risk analysis only. No production code changes.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Load the signed LifePRO fund on the last QuikIswl row for the 247 policies that are negative today. Leave the in-month floor in place so the 1,997 policies that already tie do not move.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|---|---|---|---|
| QuikIswl last MACCTBAL when FUND_BALANCE < 0 | 0.00 | signed FUND_BALANCE | Yes |
| QuikIswl last MCASHVAL on those rows | 0.00 | same signed amount | Yes |
| QuikIswl last account when FUND_BALANCE >= 0 | equals the fund | unchanged | No |
| Intermediate months that dip below zero | stored as 0.00 | unchanged | No |
| QuikValf | whatever QLAdmin wrote on the 6/30 test | unchanged until the next valuation | No |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|---|---|---|
| quikridr.MPREM | #26 | **No** |
| quikmstr.MMODPREM | mode premium | **No** |
| MPOLICY | #25 padding | **No** |
| quikprmh.MISWL / QuikIsrr.MISWL | #155 stamp | **No** |
| QuikIswl MINT, MCOI, MEXP, MPREMIUMS, MLOANBAL, MDB | existing history | **No** |
| quikplan and rates | older-cut rule | **No** |
| QuikValf MRESERVE | #171, not this issue | **No** |

---

## 3. Repo References

| Location | Role |
|---|---|
| `qla_core/quikiswl_loader.py` | Floor and last-row force to 0.00 |
| `tools/validators/validate_issue155_iswl_seed.py` | Fail-closed tie to max(fund, 0); gold 9010779727C = 0.00 |
| `QLA_Migration/Reports/issue155_iswl_seed_exceptions_20260630.csv` | 15,976 floor events, 24 untied, 24 no PFNDR |

---

## 4. Population Analysis

| Metric | Count |
|---|---:|
| QuikIswl rows | 545,150 |
| QuikIswl policies | 2,244 |
| PFNDR policies on the 6/30 extract | 2,325 |
| Last account would change | 247 |
| Last account unchanged (already tied) | 1,997 |
| Both sides already 0.00 | 558 |
| Ending-negative policies currently stored as a negative | 0 |

### Breakdown

| Dimension | Policies | Would change |
|---|---:|---:|
| LifePRO fund negative, QL account 0.00 | 247 | 247 |
| Floor event during history, LifePRO ending fund not negative | 187 | 0, if the in-month floor stays |
| OPEN_BALANCE_UNTIED | 24 | 0 |
| NO_PFNDR | 24 | 0 |

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|---|---:|---|
| A. Last row only, signed fund, in-month floor stays | 247 policies, one row each | Recommended |
| B. Also remove the in-month floor | Up to 434 policies, 15,976 events, and the 187 that currently tie could miss LifePRO | Reject for this issue |

**Recommended fallback:** Option A.

---

## 6. Trace Policies

| Policy | Before | Proposed | Pass? |
|---|---:|---:|---|
| 9010779727C | 0.00 | −172,395.45 | Yes, if the last row is the signed fund |
| 9010737619C | 0.00 | −718,363.35 | Yes |
| 9010735781C | 0.00 | −121,065.25 | Yes |
| 9010713704C | 45,551.94 | 45,551.94 | Must not move |
| 9010713705C | 26,251.74 | 26,251.74 | Must not move |
| 9010713707C | 8,146.88 | 8,146.88 | Must not move |

---

## 7. Top 5 Largest Changes

| Policy | Before | After | Delta |
|---|---:|---:|---:|
| 9010737619C | 0.00 | −718,363.35 | −718,363.35 |
| 9010779727C | 0.00 | −172,395.45 | −172,395.45 |
| 9010735781C | 0.00 | −121,065.25 | −121,065.25 |
| 9010842282C | 0.00 | −79,300.74 | −79,300.74 |
| 9010766062C | 0.00 | −78,705.99 | −78,705.99 |

---

## 8. Material Calculation Impact

The change is the stored account on policies LifePRO already carries as negative. Interest, mortality, expense, and premium components on those history rows are not recalculated. Policies that already match a zero or positive fund do not move under Option A.

QuikValf on the 6/30 company will still show 0.00 until anniversary and valuation are run again. This issue does not edit that file.

---

## 9. Prior Fix Preservation

| Check | Result |
|---|---|
| Issue #25 MPOLICY padding | Preserved. No key change. |
| Issue #26 MPREM / MMODPREM | Preserved. No premium mapping change. |
| Issue #124 month-0 removed | Preserved. No month-0 row is added back. |
| Issue #155 history tie for non-negative funds | Preserved only if the validator’s floor rule is updated and the in-month floor stays. 155 is not a Closed guide row. |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] 9010779727C last MACCTBAL and MCASHVAL = −172,395.45
- [ ] 9010737619C last MACCTBAL = −718,363.35
- [ ] 9010713704C, 9010713705C, 9010713707C unchanged
- [ ] 1,997 non-negative policies still tie to PFNDR
- [ ] Row count stays 545,150 policies 2,244 unless a later batch says otherwise
- [ ] #155 validator updated and PASS on full Output
- [ ] quikplan and rates hashes unchanged
- [ ] MRESERVE not part of this check

---

## 11. Recommended Development Agent Task

1. In `qla_core/quikiswl_loader.py`, write the signed PFNDR fund to the last MACCTBAL and MCASHVAL when that fund is negative, instead of 0.00. Tie to the signed fund.
2. Do not remove the in-month floor.
3. Update `tools/validators/validate_issue155_iswl_seed.py` so a negative fund matches, and set the 20260630 gold for 9010779727C to −172,395.45.
4. Do not change app.py, quikplan, rates, MISWL, or QuikValf.
5. Re-emit QuikIswl for QLA_VALUATION_DATE=20260630 and run the #155 validator.

---

## Appendix

- Simulation script: `Issue_Log_Items/Issue_173/tools/_count_negative_funds.py`
- Exception file: `QLA_Migration/Reports/issue155_iswl_seed_exceptions_20260630.csv`
