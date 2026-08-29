# Issue 142 — Intake Summary

**Issue:** SL Policies — Bring in the SL Rider on Active Policies. The rider can be provided its own code (9SUBLF). Units will need to be removed so that insured amounts are not duplicated.
**Date raised:** 2026-08-12 · **Priority:** No Go · **Owner:** Eric · **Assigned:** Warren
**Intake date:** 2026-08-29 · **Source package:** 2026-06-30 extracts (`PPBEN_PolicyBenefit_Extract_20260630.csv`)
**Client inputs:** `docs/SL_Riders/SL Policy Information.xlsx` (Eric's 22-policy spreadsheet, 8 red-font), `docs/SL_Riders/SL_Rider_Notes.txt` (meeting notes)

## Background

SL (`BENEFIT_TYPE = SL`) is LifePRO substandard-rating metadata carrying the same units and
$1,000 value-per-unit as the coverage it rates. Emitting it as-is would duplicate the insured
amount. Issue #27 (Closed) therefore suppresses **all** SL rows from quikridr
(`qla_core/sl_benefit_governance.py`). Consequence: the substandard extra premium on active
policies is invisible in QLAdmin.

## Population (verified against 06/30 source)

- PPBEN has **68** SL rows total: **22 Active** (on 22 Active policies) + 46 Terminated.
- The 22 active rows match Eric's spreadsheet exactly, one-for-one.
- The **8 red-font** policies are the subset with `ANN_PREM_PER_UNIT > 0` (real rating premium):
  9010469666, 9010497264, 9010886099, 9010987095, 9011185537, 9011193243, 9011201237, 9011203457.
- The other 14 active SL rows have zero premium (informational only).
- Outlier 9010782078: SL row has `MODE_PREMIUM = 8.05` but **0 units and 0 ANN_PREM_PER_UNIT**.
- 9010987095: its SL row rates the **waiver rider** (plan `1576 659`), not the base coverage.
- None of the 22 policies currently has any SL-derived row in Output (`quikridr`/`quikmstr` verified).

## Key mechanical finding (Discovery)

QLAdmin computes premium as **units × Prem/Unit (MPREM)** — proven by the Issue #88 fix history.
A literal zero-unit row would zero the premium too. The book already contains the correct
pattern: **25 existing quikridr rows (9FTRWP / 9CTRWP) carry MUNIT > 0, MVPU = 0, MPREM > 0** —
insured amount 0, premium preserved. Issue 142 follows that precedent: keep units, zero the
value-per-unit.

## Decisions locked (Warren, 2026-08-29 in chat)

| # | Question | Decision |
|---|---|---|
| 1 | Emit 8 red only or all 22 active SL rows? | **All 22** — visibility everywhere |
| 2 | 9010782078 $8.05 mode-premium outlier | **Leave it** — emits with 0 premium (0 units / 0 APU carries nothing) |
| 3 | 9010987095 SL-on-waiver double-bill risk | **Assume it does not bill** — Eric has already stated these riders are not billing |
| 4 | Single 9SUBLF plan = one modal factor set (LifePRO factors vary 0.0833–0.088 monthly, 0.25/0.27 quarterly) | **Accept the rounding** |
| 5 | Conflict with Closed Issue #27 (blanket SL suppression) | **Override approved in writing** — narrow suppression to non-active SL rows |

## Scope

- **In:** quikplan (+1 seeded plan `9SUBLF`), quikridr (+22 phases), product catalog crosswalk
  (+1 routing entry), quikuwpo (9SUBLF × UW classes 0/S/B/P per A11), Issue #27 suppression
  narrowed to non-active SL rows, fail-closed Issue 142 smoke validator.
- **Out:** terminated SL rows (46 — stay suppressed with Issue #27 audit), any premium
  billing change, rate tables (A3 default key stubs auto-cover 9SUBLF), quikmstr.

## Success criteria

1. All 22 active SL rows emit to quikridr as MPLAN=9SUBLF, MVPU=0, MUNIT=source units,
   MPREM=source ANN_PREM_PER_UNIT, MPHSTAT from benefit status (A→22).
2. No insured-amount duplication: every 9SUBLF row has MVPU = 0.
3. The 8 red policies show their rating premium per unit (e.g. 9010886099: 100 units × 26.34).
4. Non-SL rows across all tables unchanged (regression).
5. Fail-closed smoke registered in `SMOKE_JOBS` at Closure.
