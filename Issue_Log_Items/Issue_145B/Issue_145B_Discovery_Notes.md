# Issue #145B — Discovery Notes (Search & Discuss)

**Issue:** #145B — Vanish 0561s Out of ISRR  
**Date:** 2026-08-20  
**Framework stage:** Stage 0 Discovery (G-D)  
**Code:** None  
**Parent:** #145 Vanish Flag (VB) — flag only; Ready for Client UAT  

---

## Client ask (verbatim)

Pull the 0561s out completely from the history for vanishing policies.

---

## Verdict

This is the child of #145. **#145 only sets the Vanish flag** and left QuikIsrr alone. **#146 is non-VB leftovers.** #145B takes vanish 0561s out of converted history.

**Target:** stop emitting (and remove already-emitted) **QuikIsrr** rows whose source is PACT 0561 on policies with `PPOLC.BILLING_REASON = VB`.

Do **not** delete rows from LifePRO PACTG. Do **not** turn this on for #146 leftovers unless Intake later expands scope.

Anniversary reduces units from QuikIsrr + matching claim-payment history. If claim companions were ever built from these 0561s, those would have to come out too. Issue 34 companion recon found **0** QuikClms/QuikClmp matches for the 0561 population — so QuikIsrr is the history that matters.

---

## Why these 0561s are not surrenders

On the 2026-06-30 extract (unreversed 0561):

| Book | Policies | Rows | Amount = billed premium |
|---|---:|---:|---:|
| VB | 587 of 636 | 3,452 | 3,324 (96%) |

Typical vanish 0561: amount = mode/annual premium, credit **0013** (no payee, no EFT, no check), often the same anniversary date year after year, LifePRO `NUMBER_OF_UNITS` unchanged.

Gold:

| Policy | VB | Units in LifePRO | 0561s |
|---|---|---:|---|
| 9010815236 | Yes | 25 | 8 unreversed (9th reversed, already excluded) |
| 9011050114 | Yes | 25 | 1 × $136 |
| 9011069610 | Yes | 50 | 1 × $406 |

After exclude, those policies should have **zero** QuikIsrr rows. Units stay at LifePRO original.

---

## Current vs desired

| Area | Current | Desired |
|---|---|---|
| #145 `quikspec.VANISH` | T on 636 VB | Unchanged |
| QuikIsrr | #34 emits ISWL 0561 including VB | **No QuikIsrr rows for VB policies** |
| LifePRO PACTG 0561 | Still in extract | Unchanged |
| #146 non-VB | Still in QuikIsrr | Unchanged this issue |

---

## Related issues

| Issue | Relationship |
|---|---|
| **#145 Vanish Flag** | Parent. Flag only. Ready for Client UAT. Do not reopen. |
| **#34 QuikIsrr** | Source of the 0561 emit. #145B is an exclusion on that emit. |
| **#146 Non-VB Unit Reductions** | Same transaction type, not on vanish. Stay separate. |
| **#22 Vanish Option** | Research. Not this emit. |

---

## Proposed work list (Planning will refine)

1. Exclude VB policies from QuikIsrr emit (join PPOLC BILLING_REASON=VB).
2. Strip those rows from current `Output/QuikIsrr.csv` if already loaded.
3. Validator: 9010815236 / 9011050114 / 9011069610 have 0 QuikIsrr rows; non-VB examples 9010761639 / 9010760840 still have theirs.
4. Confirm no QuikClms/QuikClmp 0561 companions need a matching exclude.

---

## Open questions

1. Exclude **all** 0561s on a VB policy, or only amount=premium rows (128 VB rows do not match *today’s* premium)? Warren’s ask is **completely** — all 0561s on vanishing policies.
2. After Output exclude, does the already-loaded QLAdmin QuikIsrr DBF need a reload / append of the reduced file?

---

## Stop

Discovery complete. Awaiting **Proceed to Intake**.

---

## 2026-08-23 refresh (Warren)

Warren confirmed scope is **vanishing (VB) policies only**, not the whole 0561 book and not #146 leftovers.

| In scope | Out of scope |
|---|---|
| QuikIsrr rows sourced from PACT 0561 on `PPOLC.BILLING_REASON = VB` | Non-VB 0561s (#146), including 9010761639 and 9010760840 |
| Strip those rows from current `Output/QuikIsrr.csv` | Deleting LifePRO PACTG |
| Keep #145 `VANISH=T` as-is | Changing units on `quikridr` / `quikmstr` |

Current Output still has the VB 0561s (3,452 rows / 587 of 636 VB policies). The 08/20 Control vs Test package was never run in QLAdmin. Warren is ready to implement the emit exclusion without waiting on that A/B.

Closed **#34** still owns the 0561 → QuikIsrr source rule. #145B is a **VB exclusion on that emit**, not a reopen of #34. Traditional / non-VB 0561s stay.
