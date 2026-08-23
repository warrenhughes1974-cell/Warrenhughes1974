# Issue #145B — Intake Summary

**Issue:** #145B — Vanish 0561s Out of ISRR  
**Framework stage:** Intake Agent (G0)  
**Status recommendation:** Intake Complete → Planning → Dependency Gate → Risk  
**Generated:** 2026-08-23  
**Owner:** Conversion  
**Priority:** Go

---

## Client symptom (verbatim + normalized)

**Verbatim (08/20):** Pull the 0561s out completely from the history for vanishing policies.

**Verbatim (08/23):** Not from all policies. From the vanishing policies.

**Normalized:** For policies on vanish in LifePRO (`PPOLC.BILLING_REASON = VB`), stop sending PACT 0561 history into QuikIsrr (and the matching #34 companion rows). Those 0561s are vanish premium taken from the policy, not cash surrenders. LifePRO keeps original units. After anniversary, QLAdmin should keep those units.

## Example policies

| QLA policy | VB / VANISH | Current QuikIsrr | After this issue |
|------------|-------------|-----------------:|------------------|
| 9010815236C | Yes / T | 8 rows ($1,402.56) | **0** rows; units stay 25 |
| 9011050114C | Yes / T | 1 row ($136.00) | **0** rows; units stay 25 |
| 9011069610C | Yes / T | 1 row ($406.00) | **0** rows; units stay 50 |
| 9010761639C | No / F | 1 row ($271.00) | Unchanged — **#146** |
| 9010760840C | No / F | 2 rows ($716.40) | Unchanged — **#146** |

## Suspected domain

ISWL partial-surrender history — `QuikIsrr` plus the #34 PR-7 companions written from the same 0561 events (`quikclms` PS- / phase 0, `quikclmp` phase 0, `quikbenh` type 8).

## In scope (first pass)

- Exclude VB policies from the #34 0561 emit.
- Strip already-emitted VB 0561 history from current Output on those same four tables.
- Leave LifePRO PACTG untouched.
- Validator + fail-closed smoke: golds have 0 QuikIsrr; #146 examples still have theirs; `VANISH` stays T.

## Out of scope (first pass)

- Non-VB 0561 leftovers (**#146**).
- Changing `quikridr.MUNIT` / `quikmstr` / billed premium.
- Changing `quikspec.VANISH` (**#145** already set).
- Deleting or rewriting LifePRO PACTG.
- Reopening #34’s 0561 source rule for non-VB policies.
- Recreating DBFs (append-only).

## Related issues

| ID | Relationship |
|----|----------------|
| **#145** | Parent. Flag only. Ready for Client UAT. Do not reopen. |
| **#34** | Closed 0561 → QuikIsrr source. #145B is a **VB exclusion** on that emit. |
| **#146** | Non-VB unit leftovers. Stay separate. |
| **#54** | `quikbenh` loan types 10/11/12. Preserve. Do not wipe the file. |
| **#22** | Vanish Option research. Not this emit. |

## Immediate blockers at intake

None. Source PPOLC and PACTG are in the package. Current Output has the rows. Warren locked VB-only on 08/23.

**Closed-issue notice:** this does not undo #34. Non-VB 0561s still emit. The #34 emit script’s hard floor (`3657` rows / `637` policies) must be restated to the leftover book when Development runs.

## Artifact inventory

| Artifact | Status |
|----------|--------|
| Discovery notes | `Issue_145B_Discovery_Notes.md` (08/20 + 08/23 refresh) |
| Analysis | `Issue_145B_Analysis_Report.md` — unit formula proven |
| A/B UAT package | Built 08/20; QLAdmin anniversary **not** run; Warren chose to implement without waiting |
| PPOLC / VANISH | 636 VB; `quikspec.VANISH=T` already on current Output |
| Current `QuikIsrr.csv` | 3,657 rows; **3,452** VB / **205** non-VB |

## Severity / owner

- **Severity:** High on the vanish book — anniversary cuts face by 0561 dollars / 1,000.
- **Owner:** Conversion (Warren). Sheet owner QLA.
