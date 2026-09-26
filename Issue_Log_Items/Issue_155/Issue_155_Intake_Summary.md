# Issue #155 — Intake Summary

**Issue:** #155 — Val File Value Per Unit Wrong (ISWL) → ISWL account value does not match LifePRO  
**Date:** 2026-09-24  
**Framework stage:** Intake complete (G0)  
**Owner:** Conversion (Warren) + QLAdmin (ISWL calculation behavior)  
**Raised by:** Eric (08/23/2026); expanded by Jill's 9/7 ISWL comparison (`QLvsLifeproISWL (1).xlsx`)  
**Priority:** Go-No Go  
**Related:** #124 (QuikIswl month-0 seed, Closed), #21F (pre-2018 CONV_ADJ premium, Closed), #32 (QuikUint, Closed), #88, #153 (reserve method, deferred)

---

## Client symptom

Verbatim (sheet): *QLAdmin valuation file shows an inflated value per unit — for example $2,522.74 instead of the $1,000 every policy carries … 152 policies affected. Example 9010902968.*

Jill 9/7: *the account value drives the differences on the first 3 policies* (9010713704, 9010713705, 9010713707).

## Normalized finding

The value per unit in the valuation file is derived from the QLAdmin ISWL account. The account is wrong because:

1. Conversion seeds the account at $0.00 at issue (#124) and QLAdmin rebuilds it from issue.
2. QLAdmin receives no premiums before 12/31/2017 except one lump (#21F), so 1984–2017 runs at −$5/month with no interest.
3. QLAdmin's ISWL monthly calculation on these plans credits **7%**, charges **no COI**, and charges **$5 + 5% of premium**. LifePRO credits **4.5%**, deducts monthly mortality (`MT`), and charges a $2.08 fee plus a ~3.8% load. QuikUint (4.5%), QuikCoi and QuikIsxp are not driving the QL result.

Warren direction (2026-09-24): Option A — load the LifePRO account balance as of the conversion date and let QLAdmin calculate forward.

## Example policies

| Policy | Plan | LifePRO 6/19/2026 | QL 6/19/2026 (9/23 run) | LifePRO 8/19/2026 |
|---|---|---:|---:|---:|
| 9010713704C | 1659C2 | 45,551.94 | 31,469.97 | 45,906.83 |
| 9010713705C | 1659C2 | 26,251.74 | 16,455.41 | 26,479.01 |
| 9010713707C | 1659C2 | 8,146.88 | 5,046.07 | 8,193.53 |
| 9010902968C | 659 CEN SR | 15,219.16 (6/06) | 12,577.88 (9/2 valf) | 15,382.23 (8/06) |

## Scope (first pass)

| In | Out (for now) |
|---|---|
| QuikIswl seed row carrying LifePRO balance at conversion date | Jill's reserve formula (separate issue after AV matches) |
| Marking converted premiums/withdrawals as already applied (`quikprmh.MISWL`, `QuikIsrr.MISWL`) | Rebuilding 1984–2002 history |
| Negative LifePRO funds floored at 0.00 (Warren 2026-09-24) | Changing QLAdmin program logic |
| Evidence for QLAdmin on the 7% / zero COI / $5 fee behavior | |

## Artifacts

| Artifact | Status |
|---|---|
| LifePRO fund history `PFNDRDET` (2002/2003 → 8/2026) | Extracted to `QLA_Migration/Source/` |
| PFNDR summaries 6/30 and 8/31 | In Source |
| QL QuikIswl from Warren's 9/23 anniversary run | Read-only in `Q:\CSO\CSO_Test_6_30_2026` |
| QLAdmin Help §5.7.9 (UL rate files), §7.146 QuikIswl, §7.147 QuikIsxp | `docs/claims_conversion_reference/QLAdmin_Help.pdf` |

## Immediate blockers visible at intake

The seeded balance alone does not make QLAdmin track LifePRO after conversion (see Planning proof test). Whether QLAdmin's ISWL interest, COI and expense can be table-driven is not answerable from the repo.

## Gate G0

- [x] Issue folder exists
- [x] Intake summary written
- [x] Example policies listed
- [x] Owner and priority assigned
- [x] No code or rulebook changes
