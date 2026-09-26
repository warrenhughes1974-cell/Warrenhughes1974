# Issue 173 — Discovery notes

**Date:** 2026-09-25  
**Status:** Discovery complete. Stop. Awaiting “Proceed to Intake”.

## Issue ID and title

173 — ISWL negative fund balances

## Client ask

Warren, 2026-09-25: reverse the 2026-09-24 decision that stored a negative LifePRO fund as 0.00. Bring the negative fund into QLAdmin.

## Source

LifePRO fund summary: `QLA_Migration/Source/PFNDR_FundHistory_Extract_<QLA_VALUATION_DATE>.csv`, field `FUND_BALANCE`.

Monthly history: `QLA_Migration/Source/PFNDRDET_FundHistoryDET_ISWL_Extract_20260831.csv`.

On the 6/30 comparison, 247 policies have a negative LifePRO fund and were loaded as 0.00. Example: 9010779727C, LifePRO fund −172,395.45, QLAdmin account 0.00. At the 8/31 discovery cut the largest was 9010737619, −754,705.97.

## Current behavior

`qla_core/quikiswl_loader.py` floors the running account at 0.00 whenever a month would go negative, and forces the last `MACCTBAL` and `MCASHVAL` to 0.00 when LifePRO’s fund is negative. `MCASHVAL` is set equal to the account. The #155 validator requires the last account to equal `max(FUND_BALANCE, 0)` and expects 9010779727C at 0.00.

## Desired behavior

Store the negative fund. The last QuikIswl account should equal LifePRO `FUND_BALANCE`, including when that amount is negative. A month that goes negative should stay negative so later months are not restarted from zero.

## Target

QuikIswl `MACCTBAL` and `MCASHVAL`. QLAdmin writes QuikValf at valuation. Loading the negative into history does not change the QuikValf already produced on the 6/30 test until valuation is run again.

## Related issues

- **#155 (Ready for Client UAT, not Closed).** The 9/24 floor is part of that load. This issue reverses only that floor. The #155 smoke will fail on 9010779727C and on the floored tie until that check is updated in the same change. Do not Close #155 on the zero-balance rule.
- **#171** stays the reserve question (units times the Tvs factor). Do not change `MRESERVE` here.
- Policies whose LifePRO fund is already 0.00 and were forced to 0.00 because the history would not tie (`OPEN_BALANCE_UNTIED`) are not this issue.
- **#124** month-0 seed stays removed.

## Proposed work (no code in Discovery)

1. Stop flooring the opening balance, each history month, and the last row.
2. Tie the last account to the signed LifePRO fund.
3. Update the #155 balance check so a negative fund is a match, and change the 9010779727C example from 0.00 to the signed fund.
4. Leave positive funds, reserves, plan, and rates unchanged.

## Open point

Whether QLAdmin will keep a negative account when it next runs valuation is a test question, not a conversion rule. The conversion target is the QuikIswl history.

## Stop

Awaiting “Proceed to Intake”.
