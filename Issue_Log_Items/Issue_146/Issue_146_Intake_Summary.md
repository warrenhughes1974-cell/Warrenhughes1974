# Issue #146 — Intake Summary

**Issue:** #146 — Non-VB Unit Reductions (PC / former-vanish 0561 exclude)  
**Framework stage:** Intake Agent (G0)  
**Status recommendation:** Intake Complete → Planning → Dependency Gate → Risk  
**Generated:** 2026-08-26  
**Owner:** Conversion  
**Priority:** Go

---

## Client symptom (verbatim + normalized)

**Verbatim (08/18):** After vanish is flipped for the VB book, leftover policies still have QLAdmin reducing units for PACT 0561 history while LifePRO keeps the original unit count.

**Verbatim (08/23 write-up to Eric):** 19 policies, billing reason PC, every 0561 equal to annual premium on the anniversary. Same vanish-premium pattern as VB. Confirm so we pull them from the surrender load.

**Verbatim (08/24 Warren):** Treat 9010808831 like the vanish book. Pull those 0561s so units stay at 25.

**Verbatim (08/26 Eric / New Era):** Most Suspended PC policies were on Vanish and now have a negative fund. New Era moves them from Vanish to Susp–PC. This should help most leftover unit discrepancies.

**Verbatim (08/26 Warren):** Proceed with removing the 0561s on these policies that were vanish.

**Normalized:** For a locked **20-policy allowlist** (19 `BILLING_REASON=PC` plus approved blank-reason 9010808831), stop sending PACT 0561 history into QuikIsrr and the matching #34 companions. Those 0561s are vanish premium taken from the fund, not cash surrenders. LifePRO units stay. After anniversary, QLAdmin units should stay. Do **not** set VANISH=TRUE on PC. Do **not** strip all non-VB 0561s.

## Example policies

| QLA policy | Billing reason | Current QuikIsrr | After this issue |
|------------|----------------|-----------------:|------------------|
| 9011077629C | PC | 8 × $276.10 ($2,208.80); MUNIT 5 | **0** rows; units stay 5 |
| 9010817956C | PC | 7 × $148.70 ($1,040.90); MUNIT 5 | **0** rows; units stay 5 |
| 9010808831C | (blank) | 8 × $138.25 ($1,106.00); MUNIT 25 | **0** rows; units stay 25 |
| 9010761639C | (blank) | 1 × $271.00 | **Unchanged** — real surrender |
| 9010760840C | (blank) | 2 × $716.40 | **Unchanged** — real surrender |

## Suspected domain

ISWL partial-surrender history — `QuikIsrr` plus the #34 PR-7 companions from the same 0561 events (`quikclms` PS- / phase 0, `quikclmp` phase 0, `quikbenh` type 8).

## In scope (first pass)

- Exclude the locked 20-policy allowlist from the #34 0561 emit (after the existing #145B VB filter).
- Strip already-emitted allowlist 0561 history from current Output on those same four tables.
- Leave LifePRO PACTG untouched.
- Leave `quikspec.VANISH` unchanged (PC stays F).
- Fail-closed validator: allowlist golds have 0 QuikIsrr; #145B leftover golds still have theirs; `MUNIT` unchanged.

## Out of scope (first pass)

- All non-VB 0561s, or all `BILLING_REASON=PC` (169 PC policies exist; only 19 of them are on this list).
- Setting `VANISH=TRUE` on PC / Susp-PC (**#145** stays VB-only).
- How QLAdmin handles negative fund / bill hold (**#154**).
- Remaining unit vs current-DB leftovers that are not this 0561 pattern (**#147**).
- Changing `quikridr.MUNIT` / `quikmstr` / billed premium.
- Deleting or rewriting LifePRO PACTG.
- Reopening #34’s 0561 source rule.
- Recreating DBFs (append-only).

## Related issues

| ID | Relationship |
|----|----------------|
| **#145B** | Closed. VB 0561s already excluded. This is the leftover book #145B deferred. Do **not** undo VB golds or the $271 / $716.40 keep golds. |
| **#145** | Vanish flag VB only. Do not set VANISH on PC. |
| **#34** | Closed 0561 → QuikIsrr source. #146 is an **allowlist exclusion** on that emit. |
| **#154** | GP / bill hold / negative fund. Separate. |
| **#22** | Vanish Option research. Not this emit. |
| **#54** | `quikbenh` loan types 10/11/12. Preserve. |

## Immediate blockers at intake

None. Current Output has all 20 allowlist policies on QuikIsrr (104 rows, $32,321.25). Warren proceeded 08/26 after Eric’s PC / former-vanish note and Luna’s scope lock.

**Closed-issue notice:** this does not undo #145B. VB golds stay at 0 QuikIsrr. 9010761639C / 9010760840C stay. The leftover book shrinks from 205 / 50 to 101 / 30 on the 6/30 package.

## Artifact inventory

| Artifact | Status |
|----------|--------|
| Discovery notes | `Issue_146_Discovery_Notes.md` (08/18) |
| 19-policy list + fingerprint | `Eric_QuikValf_VPU_Writeup_20260823.md` |
| 9010808831 exception | `Issue_146_Exception_9010808831.md` |
| Read-only research | `Issue_146/evidence/issue146_research_summary.json` |
| Current `QuikIsrr.csv` | 205 leftover rows after #145B; **104** on the allowlist |

## Severity / owner

- **Severity:** High on the 20 policies — anniversary cuts face by 0561 dollars / 1,000.
- **Owner:** Conversion (Warren). Sheet owner Eric.
