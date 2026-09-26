# Issue 173 — Implementation notes

**Date:** 2026-09-25  
**Approved:** Warren, Approved for Development, and remove the #155 always-on smoke.

## Change

`qla_core/quikiswl_loader.py`: when LifePRO `FUND_BALANCE` is negative, the last QuikIswl `MACCTBAL` and `MCASHVAL` are the signed fund. The in-month floor is unchanged. A non-negative fund still ties as before, including the force to 0.00 on the 24 untied policies whose LifePRO fund is already zero.

`tools/validators/validate_issue155_iswl_seed.py` v2.1: the last-row check uses the signed fund. Gold 9010779727C is −172,395.45. This script is no longer in `SMOKE_JOBS`.

`app.py` was not changed.

## Emit

`QLA_VALUATION_DATE=20260630`. QuikIswl only. Plan, rates, and MISWL were not rewritten.

Result: 545,150 rows, 2,244 policies. Exception counts: NEGATIVE_SIGNED 247, NEGATIVE_FLOORED_ZERO 15,961, OPEN_BALANCE_UNTIED 24, NO_PFNDR 24.
