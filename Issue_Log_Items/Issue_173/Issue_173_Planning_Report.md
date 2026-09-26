# Issue 173 — Planning Report

**Issue:** 173 — ISWL negative fund balances  
**Framework stage:** Planning Agent  
**Status:** Planning  
**Generated:** 2026-09-25  
**Agent/script:** Intake-through-Risk session; counts from `Issue_173/tools/_count_negative_funds.py`

---

## 1. Executive Finding

On the 6/30 load, 247 ISWL policies have a negative LifePRO fund and a QLAdmin account of 0.00. That zero is the 9/24 floor in `qla_core/quikiswl_loader.py`. Warren reversed that decision on 9/25. The last history row should store the signed fund. Positive balances already tie (1,997 policies) and stay as they are. The in-month floor stays, because 187 policies dipped below zero during history and still end on a non-negative LifePRO fund.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|---|---|---|---:|
| PFNDR fund summary | `QLA_Migration/Source/PFNDR_FundHistory_Extract_20260630.csv` | Yes | 2,325 policies, 0 duplicate policy rows |
| PFNDRDET monthly detail | `QLA_Migration/Source/PFNDRDET_FundHistoryDET_ISWL_Extract_20260831.csv` | Yes (already used by the loader) | Not re-counted; history file is unchanged |

### Available source fields

| Field | Column / source | Populated % | Notes |
|---|---|---:|---|
| Policy number | PFNDR `POLICY_NUMBER` | 100 | Strip spaces; QL key adds C |
| Fund | PFNDR `FUND_BALANCE` | 100 | Signed. Example 9010779727C = −172,395.45 on 20260606 |
| As-of date | PFNDR `VALUATION_DATE` | 100 | Policy monthiversary, not always the cut date |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source (Help / schema) |
|---|---|---|---|---|
| QuikIswl | MACCTBAL | money, 2 decimals | CSV text; DBF width already in the Append template | Help §7.146. Loader writes both fields from the same running balance |
| QuikIswl | MCASHVAL | money, 2 decimals | same | Set equal to MACCTBAL in `_make_history_row` |

**Repo references**

| Location | Role |
|---|---|
| `qla_core/quikiswl_loader.py` | Builds history. Floors a negative running balance to 0.00. Forces the last MACCTBAL and MCASHVAL to 0.00 when the LifePRO fund is negative (`exp_final = max(fund, 0)`). |
| `tools/validators/validate_issue155_iswl_seed.py` | Requires last MACCTBAL = max(FUND_BALANCE, 0). Gold 9010779727C = 0.00. |
| QuikValf MACCTBAL | Written by QLAdmin at valuation, not by this loader |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|---|---|---|---|---|
| PFNDR | FUND_BALANCE | QuikIswl last MACCTBAL and MCASHVAL | When fund < 0, store the signed amount. When fund >= 0, keep the current tie. | Yes, negative endings only |
| PFNDRDET | monthly flows | intermediate MACCTBAL | Keep the current in-month floor | No |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|---|---|---|
| quikmstr.MMODPREM | PPOLC.MODE_PREMIUM | **No** |
| quikridr.MPREM | ANN_PREM_PER_UNIT + fallback (#26) | **No** |
| MPOLICY padding | format_qladmin_mpolicy (#25) | **No** |
| QuikIswl interest, COI, expense, premium, loan, units, death benefit | existing history math | **No** |
| quikplan / rates | newest package, older-cut rule | **No** |
| QuikValf MRESERVE | QLAdmin valuation / #171 | **No** |
| MISWL on quikprmh and QuikIsrr | #155 stamp | **No** |

---

## 5. Open Client Questions

1. None on the ending balance. Warren’s 9/25 instruction is the signed fund.
2. Held, not asked: QLAdmin’s next valuation may or may not keep a negative account in QuikValf. That is a test after reload, not a conversion rule.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|---|---|
| Policy key | Existing loader key. Do not re-pad. |
| Dates | Unchanged YYYYMMDD |
| Money | Existing `_fmt_money` (`-172395.45` style, two decimals) |
| Blanks / zeros | A true 0.00 LifePRO fund stays 0.00. Only a negative fund changes. |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

1. PFNDR `POLICY_NUMBER` is already matched in the loader (strip, C suffix).
2. No new crosswalk step.
3. Policies with no PFNDR row stay on the existing NO_PFNDR path. Do not invent a negative for them.

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|---|---:|---|
| QuikIswl rows | 545,150 | Current Output |
| QuikIswl policies | 2,244 | Current Output |
| Policies whose last account changes | 247 | LifePRO fund < 0 and current account 0.00 |
| Policies already tied at zero or above | 1,997 | Last MACCTBAL equals FUND_BALANCE |
| In-month floor events left alone | 15,976 events / 434 policies, of which 187 end non-negative | Exception file 20260630 |

---

## 10. Sample Trace (4 policies)

| Policy (QLA) | LifePRO fund | Before | After (proposed) | Status |
|---|---:|---:|---:|---|
| 9010779727C | −172,395.45 | 0.00 | −172,395.45 | Change last account and cash |
| 9010737619C | −718,363.35 | 0.00 | −718,363.35 | Change last account and cash |
| 9010735781C | −121,065.25 | 0.00 | −121,065.25 | Change last account and cash |
| 9010713704C | 45,551.94 | 45,551.94 | 45,551.94 | Unchanged |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|---|---|---|
| #155 smoke requires 0.00 and max(fund, 0) | High | Update that check in the same change. 155 is not Closed. |
| Unflooring every history month would move the 187 policies that currently tie | High | Do not remove the in-month floor in this issue |
| QuikValf on the finished 6/30 test stays 0.00 until valuation is rerun | Medium | Say that in the handoff. Do not hand-edit QuikValf |
| DBF numeric width for a value near −718,363.35 | Low | Confirm the Append template accepts the signed amount before the package is treated as loadable |

---

## 12. Dependency Gate Preview

| Check | Met? |
|---|---|
| Source file present | Yes |
| Field definitions confirmed | Yes (Help §7.146, field already populated) |
| Client scope clear | Yes (9/25 reverse the 9/24 floor) |
| Example policies available | Yes |

---

## 13. Recommended Risk Agent Prompt

```
Risk Agent — Issue 173. Quantify the 247 ending-negative policies versus the 1,997 already tied. Confirm the in-month floor stays. No code.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. In `qla_core/quikiswl_loader.py`, when the last row is forced because the LifePRO fund is negative, write the signed fund to MACCTBAL and MCASHVAL instead of 0.00. Compare the tie to the signed fund, not max(fund, 0).
2. Leave the in-month `raw_bal < 0 → 0.00` floor in place.
3. In `tools/validators/validate_issue155_iswl_seed.py`, expect the signed fund, and set the 9010779727C gold to −172,395.45 for valuation date 20260630.
4. Do not change `app.py` unless a version bump is otherwise required. Do not rebuild quikplan or rates.
5. Re-emit QuikIswl only, for `QLA_VALUATION_DATE=20260630`, then run the #155 validator.

---

## Appendix

- Diagnostic script: `Issue_Log_Items/Issue_173/tools/_count_negative_funds.py`
- Related issues: 155, 124, 171, 25, 26
- References: QLAdmin Help §7.146; Issue 155 discovery decision 2026-09-24 item 2, reversed 2026-09-25
