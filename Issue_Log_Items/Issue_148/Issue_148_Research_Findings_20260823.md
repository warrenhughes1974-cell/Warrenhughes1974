# Issue #148 — Research Findings (2026-08-23)

**Issue:** L10 Units (0777L) — policy 9011284087 shows "not applicable" in the valuation comparison.

## Bottom line

Nothing is wrong with the conversion. The policy is loaded correctly everywhere on our side.
The policy is simply **absent from the QLAdmin valuation extract** — the only policy out of
5,083 in the load that the valuation file does not contain. This is a QLAdmin-side question
for Robert, not a conversion fix.

## Evidence chain (all verified 2026-08-23)

| Step | Source | Result |
|---|---|---|
| LifePRO source | `PPBEN_PolicyBenefit_Extract_20260630.csv` | Active (A), plan L10 LP95, 100.00000 units, $1,000.00 VPU, mode prem $176.24 |
| Conversion output | `QLA_Migration/Output/quikmstr.csv` / `quikridr.csv` | Present, status 22, plan 1L1095, MUNIT 100.00000, MVPU 1000.00, group 07777L |
| Delivered DBF package | `Archive/Q_CSO_Test_6_30_2026_pre_highwater_deploy_20260805T144726Z/quikmstr.dbf` + `quikridr.dbf` (snapshot of the deployed UAT load) | Present with identical values — the package we handed off contains the policy |
| QLAdmin valuation file | `docs/QuikValf.dbf` (latest run, 2026-08-23) | **Zero rows for the policy** |

## Census check

- Load: 5,083 policies. Valuation file: 5,082 real policies + 1 premium-suspense stub
  (MPOLICY `9010412641` without the C suffix, MEXTCODE Z, no units/plan — QLAdmin artifact).
- Exactly **one** load policy is missing from the valuation file: **9011284087C**.
- All 377 other plan 1L1095 policies and all 9 other group 07777L policies pulled in fine.
- Field-by-field diff against sibling 9011284029C (same plan, same group, pulled in fine)
  shows no structural difference — only dates, premium, and client IDs differ. Client row
  exists in quikclnt (MATTHEW B KIZER, ID 712108).

## Why the comparison says "not applicable"

The comparison workbook shows N/A because there is no QLAdmin valuation record at all
for the policy — not because units disagree. LifePRO and our load both say 100 units /
$100,000; there is nothing to remap.

## Question for Robert

1. Is policy 9011284087C in the QLAdmin policy master after loading the 6/30 package?
   (Our delivered DBF contains it, row 2453 of 5,083.)
2. If it is in the master, why does the valuation extract skip this one policy?
3. If it is not in the master, what rejected it on import?

Note: an older QLAdmin master snapshot in the repo (`docs/Policy/QUIKMSTR.dbf`,
2026-07-14, 42,001 records) also lacks the policy — so it has never made it into
QLAdmin, across at least two loads.

## No conversion action

Do not remap units. Any change on our side would break a correct load. Hold for
Robert's answer; once the policy appears in the valuation file it should match
LifePRO exactly (100 units / $1,000 VPU).
