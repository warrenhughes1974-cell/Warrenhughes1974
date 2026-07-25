# Issue #115 — Dividend-pays-premium schedule has old payments in it

**Raised:** 2026-07-25 by Warren (came out of Issue #114)
**Table:** `quikdvpr`
**Status:** Open — needs a decision

---

## The short version

Seven policies pay their premium with their dividend instead of the owner writing a check.

QLAdmin has a table that answers one question for those policies: **"what dividend is
coming up next, and when do we apply it?"** It's a to-do list for future payments.

We filled that to-do list with **payments that already happened**. All 31 entries are in
the past. There is nothing in there about what happens next.

On top of that, Issue #114 just loaded all of that same payment history into the proper
history table. So those 31 old payments are now sitting in the system **twice**.

---

## An example

Take policy **9010412641C**. Here is what's in the schedule table today:

| Date | Amount |
|---|---|
| 2018-04-01 | $164.07 |
| 2019-04-01 | $169.00 |
| 2020-04-01 | $174.11 |
| ... | ... |
| 2025-04-01 | $199.40 |
| 2026-04-01 | $204.42 |

Every one of those already happened. This policy pays its premium every April 1st, so
the next one is **April 2027** — and that entry doesn't exist. The table that's supposed
to tell QLAdmin what's coming has nothing about what's coming.

Meanwhile, after Issue #114, those exact same nine payments are also recorded in the
dividend history table, where they belong. Same policy, same dates, same amounts.

We checked all 31 entries. **Every single one is an exact duplicate** of a row Issue #114
just loaded — same policy, same date, same dollar amount, no exceptions.

---

## A second, smaller problem

Seven policies are set up to pay premiums with dividends. Only six of them have anything
in the schedule table.

Policy **9010463017C** is set to "dividend pays the premium" but has no schedule entries
at all — not old ones, not new ones. It got missed.

---

## Why this matters

Three reasons, in order of how much they'd bother a person:

1. **The same dividend shows up twice.** Anyone looking at policy 9010412641C sees the
   April 2020 dividend of $174.11 in two different places. If someone adds them up, the
   policy looks like it got twice as much as it did.

2. **QLAdmin might try to pay them again.** This table is a to-do list. We don't yet know
   for certain what New Era's system does with a past-dated entry sitting in it — it may
   ignore it, or it may try to apply a 2018 dividend to a premium in 2027. That needs an
   answer before go-live, not after.

3. **Nobody's premium is scheduled.** Right now, none of the seven policies have a next
   payment lined up. If QLAdmin needs that to bill correctly, seven policies bill wrong.

The dollars are small — $4,846.21 across all 31 entries — but a premium that doesn't get
paid causes a lapse notice, and that's a phone call from a policyholder.

---

## What we need to decide

**Question for Eric:** does New Era populate this table when they set up a
dividend-pays-premium policy, and does their system build the next entry automatically
after each payment?

His answer picks the fix:

- **If QLAdmin builds the schedule itself** — we empty the table and let their system fill
  it in. Easy fix, and the history is already safe in the right place after #114.
- **If we're expected to supply it** — we clear out the 31 old entries and calculate the
  next upcoming payment for each of the seven policies instead.
- **If they want the history left where it is** — we leave it alone, but then we should
  tell them the same numbers now appear in two tables so nobody double-counts.

We are not guessing at this. Nothing changes until Eric answers.

---

## The facts behind all of the above

| What we checked | What we found |
|---|---|
| Entries in `quikdvpr` | 31, across 6 policies, $4,846.21 total |
| How many are dated in the future | **Zero.** Newest is 2026-04-01, about four months ago |
| How many duplicate an Issue #114 row exactly | **31 of 31** |
| Policies set to dividend-pays-premium (`MDIVOPT` = 2) | 7 |
| Of those, how many have schedule entries | 6 — `9010463017C` has none |
| Where the entries came from | LifePRO accounting code 516 (dividend applied to premium), per `QLA_Migration/Balancing/Balancing_Methodology.md` BAL-C08 |
| What QLAdmin says the table is for | Help §7.87 p.772 — "Dividends to Pay Premium", where `MDATE` is the *date to apply* the dividend. A separate table, `QuikDvph`, is the history counterpart |

## Not part of this issue

- The dividend history loaded by Issue #114 — that's correct and stays.
- `quikdvdp` (dividend balances left on deposit, Issue #38) — different thing, untouched.
- `quikmstr.MDIVOPT` (which option each policy elected, Issue #110) — correct, untouched.

## Related

Issue #114 (dividend history into `quikbenh`), Issue #38 (dividend accumulations),
Issue #110 (dividend option codes).
