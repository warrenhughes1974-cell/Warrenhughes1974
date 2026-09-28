# Issue 176 — Discovery Notes

**Issue:** 176 — ISWL Projected CV Blank
**Date:** 2026-09-28
**Framework stage:** Discovery
**Code:** None

---

## Client ask

Policy `9010715467C` has no data for the 5/14/2026 and 5/14/2027 Cash Values fields. LifePRO shows gross withdrawals of $27,096. The values in QLAdmin match Fund Value in LifePRO, while most other policies match Net Fund Value. Raised 2026-09-28 by Eric. No Go. Owner Eric. Assigned Warren.

## Verdict

The screen Eric means is Policy Display, Cash Values. On the 8/31 policy Warren opened, those three boxes are 0.00 after a cash value run:

| Date on the screen | What it is | Amount |
|---|---|---:|
| 05/14/2026 | Last anniversary | 0.00 |
| 10/14/2026 | Current | 0.00 |
| 05/14/2027 | Next anniversary | 0.00 |

QLAdmin Help calls these the cash surrender values for the last anniversary, the current anniversary, and the next anniversary. They are not the ISWL fund history. QuikIswl does have a 5/14/2026 fund cash value of 10,341.98. This screen does not show that number.

The cash value table for plan 1659C2, male, preferred, issue age 46, duration 42, is 761.00 per unit. Times 50 units that is 38,050.00. LifePRO's gross account on the 6/30 valuation is 38,104.17. The net fund after the 28,346.44 surrender charge is 9,757.73. A calculation that found the table would show about 38,050 here, which is the gross value, not the net fund. The first run showed 0.00 because the region did not have the Preferred rate.

## Region confirmation

Warren reloaded the latest rate tables into the CSO test region on 2026-09-28 and reran cash values. Policy Display now shows:

| Date | Cash value |
|---|---:|
| 05/14/2026 | 38,050.00 |
| 10/14/2026 | 38,320.83 |
| 05/14/2027 | 38,700.00 |

No conversion code changed. The zero was the September 22 cash value file, which had no Preferred key for 1659C2.

## Policy

| Item | Value |
|---|---|
| Policy | 9010715467C |
| Plan | 1659C2 (LifePRO 659 CEN II) |
| Issue / anniversary | 5/14/1984 |
| Status | Active (22) |
| Units | 50 |
| Package | 6/30/2026 Output |

## LifePRO at 6/30/2026

VALX life row, benefit 1:

| Field | Amount | Meaning used in the valuation compare |
|---|---:|---|
| SURR_VALUE | 38,104.17 | Gross account |
| SURR_CHARGE | -28,346.44 | Surrender charge |
| FUND_VALUE | 9,757.73 | Net of the charge. 38,104.17 − 28,346.44 |

PFNDR fund summary for the same policy:

| Field | 6/30 extract | 8/31 extract |
|---|---:|---:|
| Fund date | 20260614 | 20260814 |
| FUND_BALANCE | 9,757.73 | 8,555.04 |
| GROSS_WITHDRAWALS | 27,096.00 | 27,096.00 |

27,096.00 is 24 anniversary withdrawals of 1,129.00. That 1,129.00 is also the annual premium on the VALX row. The PPBEN fund fields on this benefit are zero. The live fund is PFNDR, not FV_BALANCE2.

## What QLAdmin has now

`quikridr` phase 1: `MCV0` = 9,757.73000. `MCV1` and `MCV2` are blank. Those two slots are blank on all 5,083 phase-1 rows in this package, not only this policy.

`QuikIswl` has 279 history rows, from 4/30/2003 through 6/14/2026.

| Anniversary | Account and cash value | Withdrawal on the row |
|---|---:|---:|
| 5/14/2026 | 10,341.98 | 1,129.00 |
| 6/14/2026 (last row) | 9,757.73 | 0.00 |
| 5/14/2027 | no row | — |

The 6/14/2026 cash value equals PFNDR `FUND_BALANCE` and VALX `FUND_VALUE`. It does not equal the gross account of 38,104.17.

Sum of `MSURR` on this policy is 27,096.00. The documented withdrawals are in the history.

`MSURRCHG` is 0.00 and `MGTDCSV` is 0.00 on every row of this policy, and guaranteed cash value is 0.00 on every QuikIswl row in the package. Cash value is set equal to the account balance. The loader does not project dates after the fund valuation date, so 5/14/2027 is not created.

## Fund versus net fund

Last `QuikIswl` account balance was compared to VALX for the ISWL policies present in both files:

| Result | Policies |
|---|---:|
| Account equals FUND_VALUE (the net) | 1,120 |
| Account equals SURR_VALUE (the gross) | 0 |
| Of those 1,120, surrender charge makes gross and net differ by more than $1 | 507 |
| Of those 1,120, gross and net are the same | 613 |

`9010715467C` is in the 507. Its loaded cash value is the net fund, 9,757.73, the same basis as the other ISWL policies. It is not the gross account.

## What this leaves open

Eric's screen may be labeling Fund Value and Net Fund Value differently from the VALX names above. On the extract, the number QLAdmin is showing is the net (FUND_VALUE / FUND_BALANCE), not the gross account.

If the blank fields he means are a projection of the next two policy anniversaries, the conversion never fills `MCV1` or `MCV2` for any policy, and it never writes a 5/14/2027 history row. The 5/14/2026 history row is present at 10,341.98.

No code in this stage. Do not fold this into Issue 163.
