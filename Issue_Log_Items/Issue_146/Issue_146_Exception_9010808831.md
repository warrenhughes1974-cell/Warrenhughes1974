# Issue #146 — Exception: remove 0561s on 9010808831

**Date:** 2026-08-24  
**Authority:** Warren — treat this policy like the vanish book (#145B). Pull the 0561 / QuikIsrr history so units stay at LifePRO.

## Rule

Do **not** load the eight $138.25 0561 / surrender rows for **9010808831C**. They are annual premium taken from the fund on the anniversary, not face reductions. After they are omitted from `quikisrr` (and the matching claim-payment / QuikBenh type-8 rows), QLAdmin units should stay at **25.00000** and match PPBEN / current death benefit **$25,000**.

## Evidence

| Source | Units / amount |
|---|---|
| PPBEN seq 1 (BF) | 25.00000 units, $1,000 VPU, current DB $25,000 |
| Conversion `quikridr` | 25.00000 (already correct) |
| Latest valuation file | 23.894 — cut by the 0561 history |
| LifePRO annual / mode premium | $138.25 |
| QuikIsrr (8 rows) | $138.25 each, anniversary 8/26/2018 through 8/26/2025 |

8 × $138.25 = $1,106 = 1.106 units. 25.000 − 1.106 = **23.894**.

Billing reason is blank (not VB). Same vanish-premium fingerprint as the other #146 exceptions.

## Keep (not 0561)

Loan and other history stay. Do not drop the loan (`quikloan` $426.10) or non-0561 benefit history.
