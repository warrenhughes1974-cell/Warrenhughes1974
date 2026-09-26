# Issue #145 — What is special about the 0561 rows that drop units?

**Date:** 2026-08-19  
**Mode:** Read-only source research (6/30 extract)  
**Code:** None  

Eric’s question: on vanishing policies, units should not drop. The drop comes from anniversary processing applying QuikIsrr / PACT 0561 “partial withdrawals.” Is there anything on those transactions that marks them as vanish premium, not a true surrender?

## Answer

Yes. Almost all VB 0561s are **premium-sized internal clearing rows**, not cash surrenders.

They are booked as debit **0561** / credit **0013** (Surrender Clearing). There is **no payee, no EFT, no check on the 0561 itself, and no description.** The amount equals the policy’s billed mode / annual premium.

LifePRO never reduced `NUMBER_OF_UNITS`. QLAdmin does, because it treats every QuikIsrr 0561 as a face reduction:  
`new units = (units × $1000 − 0561 amount) / $1000`.

## Counts (unreversed 0561, 2026-06-30)

| Book | Policies | 0561 rows | Amount = billed mode prem |
|---|---:|---:|---:|
| VB (on vanish) | 587 of 636 | 3,452 | **3,324 (96%)** |
| VB with no 0561 | 49 | 0 | — |
| Not VB | 52 | 209 | 206 (99%) |

The 128 VB rows that do **not** match *today’s* mode premium are mostly the same annual series after a premium change (example: 9010815236 was $174.51 for years, now $176.67).

## Transaction markers that distinguish vanish deductions

| Marker | Vanish 0561 (typical) | A real cash surrender |
|---|---|---|
| Amount | Equals billed mode / annual premium | Odd amount, not the premium |
| Credit | **0013** Surrender Clearing (3,445 / 3,452 VB) | Sometimes **0012** cash (only 7 VB rows) |
| Payee / EFT / description | All blank | Payee or check expected |
| Pattern | Same month-day + same amount, year after year (471 VB policies) | One-off |
| Coder | **C03A** system/batch (3,332 / 3,452) | Manual IDs (PAKA, CADA, …) |
| LifePRO units | Still original (e.g. 25) | Would have been reduced if LifePRO treated it as a surrender |

What does **not** work as a same-row flag: PACTG `MODE_PREMIUM` on the 0561 itself is **0.00**. Description is blank. `TERM_REASON=P` is on almost every row and is not a termination.

Policy-level “has a 0090 check somewhere” is noisy (91 VB policies have some 0090 in history that is not paired to these 0561s).

## Call examples

| Policy | VB? | LifePRO units | 0561 | Billed prem | If QLAdmin reduces |
|---|---|---:|---:|---:|---:|
| 9010815236 | Yes | 25 | 8 rows, $1,402.56 (annual Oct 2; 9th reversed) | $176.67 now / $174.51 earlier | 23.597 |
| 9011050114 | Yes | 25 | $136 (2017-12-26) | $121 now | 24.864 |
| 9011069610 | Yes | 50 | $406 | $406 | 49.594 |
| 9010761639 | **No** | 25 | $271 | **$271** | **24.729** (the call example) |
| 9010760840 | **No** | 35 | 2 × $358.20 | **$358.20** | 34.284 |

9010761639 / 9010760840 are #146 leftovers on the sheet, but they are the **same transaction type**: 0561 amount = billed premium, credit 13, no payee. They just lack BILLING_REASON=VB.

True money-out 0561s are rare. One non-VB example: 9011283208, $13,650, not equal to premium $850.25, and that policy has a 0090 check.

## What this means for units

Two separate levers:

1. **#145 vanish flag** — `quikspec.VANISH=T` on VB. Eric’s hope: anniversary will not reduce face when vanish is on. That does not change the 0561 history we already loaded into QuikIsrr.
2. **Do not treat premium-sized 0561s as QuikIsrr surrenders** — if anniversary still subtracts them after the flag, the durable rule is: 0561 where amount equals billed premium (and no payee/check) is a vanish premium deduction, not a unit-reducing withdrawal.

Do not delete 0561 history. Anniversary will rebuild from whatever is in QuikIsrr.

## Artifacts

- `evidence/issue145_vb_0561_markers.json`
- `evidence/issue145_vb_0561_examples.csv`
- Probe: `_probe_vb_0561_unit_markers.py`
