# Issue #151 — Discovery Notes (Search & Discuss)

**Issue:** #151 — Val X Modal Prem Outlier  
**Date:** 2026-08-18  
**Framework stage:** Stage 0 Discovery (G-D)  
**Code:** None  

---

## Client ask (verbatim)

Interest-sensitive / Val X life modal premium is way off. LifePRO / Val X shows **$188.10**. QLAdmin evaluation shows **$2,899.79**. Policy is billing suspended. Eric said the conversion file is coming over correctly and he does not know why the evaluation file pulls it that way. Question for Robert.

---

## Verdict

This is an **evaluation / QLAdmin programming** question first, not a conversion remap.

Eric’s working note: LifePRO modal premium equals annual premium even when the policy is monthly; conversion maps mode premium straight through. This one policy could not be explained by rider or fee (#152 / #153). Paid-up modal rows on the same color group are **out of scope** (already handled; Eric said ignore).

Do not change `quikmstr.MMODEPREM` / `quikridr.MPREM` until Robert says the eval source is wrong vs the load.

#128 remains the old umbrella (“QuikVal modal premiums still not matching”). #151–#154 are the granular 8/18 splits.

---

## Related issues

| Issue | Relationship |
|---|---|
| **#128 QuikVal Modal Premiums** | Umbrella. Keep open; work the splits. |
| **#137 Names-tab Modalized Annual** | Conversion modalized annual. Different screen. |
| **#152 / #153 / #154** | Other 8/18 modal / GP groups. |

---

## Proposed work list (Planning will refine)

1. Get the policy number from the Teams file.
2. Confirm Output MMODEPREM / MPREM vs LifePRO MODE_PREMIUM / annual.
3. Robert: which Val X / QuikVal field is $2,899.79 and why billing-suspended changes it.

---

## Open questions

1. Policy number?
2. Is $2,899.79 annualized, a fund value, or a wrong mode factor?
3. Does billing-suspended / bill hold change the eval premium source?

---

## Stop

Discovery complete. Awaiting **Proceed to Intake**.

---

## 2026-09-22 Intake supersession

Pre-Development (Intake → Risk) **supersedes** the 08/18 “eval-only / do not change conversion” verdict.

Root cause on **9010969231C** is leftover former-vanish PACT 0561 history (same fingerprint as Closed #146). `$2,899.79` is `QuikValf.MPREM1`/`MANNLZD` after units were cut to 3.4952 — not a conversion premium. Warren approved **2026-09-22** adding this policy to the #146 allowlist (20 → 21). Do **not** remap `MMODEPREM` (Closed #139 stays at $163.10). Fresh QLAdmin valuation remains a UAT criterion and is **not** claimed passed.

See `Issue_151_Intake_Summary.md` and `Issue_151_Risk_Review_Report.md`.
