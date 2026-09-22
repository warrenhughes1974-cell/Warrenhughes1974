# Issue 128 — Closure

**Closed:** 2026-09-22
**Column B:** blank. Nothing from 128 ships in the next release.

## What was fixed

Nothing. No conversion field was changed for 128. Modal premium on the load was already the LifePRO modal on the original examples, including `015000055C` at $19.69. QuikVal was showing the annual $236.25 on that policy, and one-cent gaps on three others. Issue 88 corrected a separate premium-per-unit fallback. It did not change the modal premium, and it is not a 128 fix.

## Where the work went

Eric's August 18 comparison split the remaining QuikVal modal differences into four open issues. 128 stays closed as the old umbrella. Those four stay open:

| Issue | What it is |
|---|---|
| 151 | One billing-suspended policy: LifePRO modal $188.10, QLAdmin evaluation $2,899.79 |
| 152 | Rider premium included in the base modal |
| 153 | Valuation file adds the policy fee back after the load removed it |
| 154 | Gross premium due on billing-suspended policies |

Paid-up modal rows from that call stay out of scope.
