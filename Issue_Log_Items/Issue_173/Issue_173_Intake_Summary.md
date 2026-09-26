# Issue 173 — Intake summary

**Issue:** 173 — ISWL negative fund balances  
**Framework stage:** Intake  
**Generated:** 2026-09-25  
**Status after intake:** Planning

## Issue ID and title

173 — ISWL negative fund balances

## Client symptom

Warren, 2026-09-25: reverse the 2026-09-24 decision and bring in the negative fund.

Normalized: when LifePRO’s fund is below zero, QLAdmin’s ISWL account is 0.00. Load the negative amount instead.

## Example policies

| Policy | LifePRO fund (6/30 PFNDR) | QLAdmin account now |
|---|---:|---:|
| 9010779727C | −172,395.45 | 0.00 |
| 9010737619C | −718,363.35 | 0.00 |
| 9010735781C | −121,065.25 | 0.00 |
| 9010713704C | 45,551.94 | 45,551.94 (must stay) |

## Domain

Policy fund history. Table QuikIswl, fields MACCTBAL and MCASHVAL. Not reserves, not premiums, not plan setup.

## In scope / out of scope

| In | Out |
|---|---|
| Last QuikIswl account and cash value equal the signed LifePRO fund when that fund is negative | Issue 171 reserve (units times Tvs factor) |
| Update the #155 balance check that currently requires max(fund, 0) and 9010779727C at 0.00 | Rewriting QuikValf (QLAdmin writes that at valuation) |
| | Removing the in-month floor on policies whose LifePRO fund ends at zero or above (187 policies). That path already ties. |
| | OPEN_BALANCE_UNTIED (24) and NO_PFNDR (24), including 9010801730C |
| | Plan, rates, MPOLICY padding, premium fields |

## Related issues

- **#155** Ready for Client UAT, not Closed. The 9/24 floor is part of that load. This issue reverses only the ending zero. The #155 smoke fails if the check is not updated in the same change.
- **#124** Closed month-0 seed stays removed.
- **#171** stays open and separate.
- **#25 / #26** not touched.

## Artifacts

| Have | Missing |
|---|---|
| Warren’s 9/25 instruction to reverse the 9/24 floor | None for this rule |
| 6/30 PFNDR extract and current QuikIswl.csv | |
| Exception list: 15,976 NEGATIVE_FLOORED_ZERO events, 434 policies | |
| Read-only count script `Issue_173/tools/_count_negative_funds.py` | |

## Owner and priority

Owner Warren. Assigned Warren. Priority Go-No Go. Conversion work. Severity: 247 in-force-or-other ISWL policies show a zero account where LifePRO is negative.

## Blockers visible at intake

None that stop Planning. QuikValf on the 6/30 test will still show 0.00 until valuation is run again after the history reload.

## Gate G0

- [x] Issue folder exists
- [x] Intake summary written
- [x] Example policies listed
- [x] Owner and priority assigned
- [x] No code or rulebook changes
