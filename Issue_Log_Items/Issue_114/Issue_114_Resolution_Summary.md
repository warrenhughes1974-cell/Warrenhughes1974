# Issue #114 — Resolution Summary (Stage 8, Closure)

**Closed:** 2026-07-25
**Engine:** v58.36
**Status:** Closed — G7 gate satisfied

---

## The problem, in plain terms

When a whole life policy earns a dividend, that dividend is part of what the policyholder
has put into the contract. If they ever surrender the policy or take money out, the
taxable amount depends on how much they paid in versus how much they got back — the cost
basis. You need two numbers to work that out: total premiums paid, and total dividends
credited.

We had already brought over the premium side (Issue #21F). The dividend side was missing
entirely. QLAdmin's dividend history screen was **completely blank** for every policy, and
LifePRO says those policies earned **$1,889,445.44** in dividends across 593 policies.

Eric asked for the dividend total to come over "the way we did the premium history." That
is what this issue delivered.

## Why it wasn't a simple copy

The accounting extract only goes back to 2018, but these policies have been paying
dividends for decades. So we did the same two-part trick that worked for premiums:

1. **Load the real payments we have.** 2,500 actual dividend transactions from 2018
   onward, each with its real date and amount — $401,443.32.
2. **Add one catch-up entry for everything before that.** One line per policy dated
   2017-12-31 for the difference between the lifetime total and what we loaded —
   $1,473,854.50.

Add those together and each policy's dividend history matches what LifePRO says the policy
earned over its lifetime.

## Result

| | |
|---|---|
| Policies now with dividend history | 586 (was 0) |
| Dividends loaded | $1,875,297.82 of $1,889,445.44 — **99.25%** |
| Policies that match LifePRO exactly | **579 of 579 converted, to the penny** |
| Rows added to `quikbenh` | 3,079 (40,510 → 43,589) |
| Policies held back for a client decision | 14 |

---

## What was held back and why

Fourteen policies ($14,147.62) are parked in an exception report rather than guessed at:

- **7 policies** use a LifePRO dividend option called "Reduce Loan." QLAdmin has no
  matching category for it. We're not going to invent one.
- **4 policies** have a dividend total but no dividend option recorded, so there's no way
  to tell which category the dividend belongs in. $163.96 total.
- **3 policies** already have more in the 2018-onward transactions than LifePRO reports as
  their lifetime total. Their real transactions still loaded; we just didn't add a
  catch-up entry, because it would have been negative.

Separately, $18,719.96 of dividends sit on rider records rather than the base policy. We
left those out to stay consistent with how Issue #21F handled premiums.

All four of these are questions for Eric. None of them stop the other 579 policies.

---

## A bug we caught before it shipped

The first build wrote 2,504 dividend rows. A duplicate check flagged two policies with the
same dividend recorded twice on the same day.

The cause: a dividend posts as a two-sided accounting entry, and we were reading both
sides as if each were a separate dividend. Policy `9010429558` looked like it got two
$169.80 cash dividends on 2021-09-01 when it got one.

What makes this worth writing down is that **the dollar totals still balanced**. The
catch-up entry is calculated as "lifetime total minus what we loaded," so when we loaded
too much, the catch-up shrank by the same amount and the policy still tied out perfectly.
A totals-only check would have passed this straight through to the client. The row-level
duplicate check is the only thing that caught it.

Fixed by reading only the correct side of the entry. Four rows were affected across the
whole book, and all four are now documented in the exception report rather than silently
dropped. One of them also turned out to explain an odd duplicate date in another table,
which is now Issue #115.

---

## Verification

| Check | Result |
|---|---|
| Issue validator on full `QLA_Migration/Output/` | **PASS** |
| Accountability (`validate_issue_log_accountability.py`) | **IN_DATA** |
| Regression | **PASS** — 6 of 6 checks |
| Existing rows preserved | Byte-for-byte — the new file is a strict extension of the old one |
| Re-running the converter | Produces an identical file |
| Cross-check against Issue #110 | All 579 catch-up entries agree with the dividend option loaded separately in `quikmstr` |

The validator recalculates the lifetime totals from the LifePRO extract itself instead of
trusting the converter's own report, so it is able to disagree with the converter — and
during this issue, it did.

---

## Files changed

| File | Change |
|---|---|
| `qla_core/quikbenh_dividend_history_converter.py` | New — the converter |
| `plan_governance/config/quikbenh_dividend_history_rules.json` | New — code mappings and rules |
| `plan_analysis/phase_benh_dividend_history/quikbenh_dividend_runner.py` | New — command-line runner |
| `tools/validators/validate_issue114_dividend_history.py` | New — issue validator |
| `tools/validators/validate_issue_log_accountability.py` | Registered #114 |
| `app.py` and `QLA_Migration/app.py` | Wired in behind a flag; version v58.36 |
| `QLA_Migration/Output/quikbenh.csv` | 40,510 → 43,589 rows |

Turned on with `QLA_ENABLE_QUIKBENH_DIVIDEND_EMIT=1` and
`QLA_QUIKBENH_DIVIDEND_WRITE_OUTPUT=1`. Both default off, so an ordinary batch is
unaffected until they're set.

**Rollback:** restore
`Issue_Log_Items/Issue_114/evidence/quikbenh_before_issue114_v5835_20260725_164158.csv`
over `QLA_Migration/Output/quikbenh.csv`.

---

## Follow-ups

- **For Eric:** the four open questions above (Reduce Loan, rider-row dividends, missing
  dividend options, and confirmation that deriving cost basis outside QLAdmin is
  acceptable — QLAdmin has no cost-basis field for life policies, only annuities).
- **Issue #115** — the dividend-pays-premium schedule table holds old payments instead of
  upcoming ones.
- **Housekeeping** — the Issue #54 validator still expects the old 10-character policy
  number format and fails for that reason alone, before and after this change. Its
  baselines need refreshing.
