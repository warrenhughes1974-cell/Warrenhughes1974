# Issue #85 — Decisions for Review (plain English)

**Date:** 2026-07-17  
**Status:** **APPROVED 2026-07-17** — conversion owner: “Approve and lets proceed.”  
**Issue:** Our conversion sometimes writes more than one claim header on the same policy and phase. The real QLAdmin system never does this. Until we fix it, claim checks don't attach cleanly and the money on the Claims screen can't be trusted.

---

## The problem in one paragraph

Think of a claim in QLAdmin as a folder: one cover page (the claim header) with the checks filed inside it. Our conversion sometimes creates **two or more cover pages for the same folder**. About 3,000 claim rows are affected. When that happens, QLAdmin can't tell which checks belong to which cover page, so the "Net Payment" on screen often doesn't match the checks underneath.

We compared against the real QLAdmin claim data we were given. It never has this problem — when a policy has more than one claim (say a withdrawal years ago and a death claim later), **each claim gets its own slot (phase) and its own claim number**.

---

## Decision 1 — How do we tell claims apart?

**Recommendation: use the claim number as the identity, and copy how the real system stores multiple claims.**

We found the ~3,000 problem rows are really two different situations:

- **True duplicates (~327 rows):** the exact same claim (same claim number) accidentally written twice. Example: policy `010914301C` — one death claim paid in two installments, but we created two cover pages for it.
  - **Fix: merge them into one claim.**
- **Crowded claims (~3,443 rows):** genuinely different claims (different claim numbers) all crammed into the same slot. Example: policy `011014579C` — eleven small annual withdrawals, each its own real event, all stacked on phase 1.
  - **Fix: give each claim its own slot (phase), which is exactly what the real system does.**

**Why:** merging everything would erase real claim history; keeping duplicates breaks the screens. This mirror-the-real-system approach does neither.

---

## Decision 2 — When we merge true duplicates, what does the surviving claim look like?

**Recommendation:** the one surviving claim header shows:

- **Net Payment = the total of everything actually paid** on that claim (this is how the real system works)
- The **earliest** date of death / date reported
- The **latest** paid date (when the claim actually finished)
- The real **face amount** (amount of insurance), not a zero
- The claim status we already fixed in Issue #79 (Paid in Full, Surrender, etc.)

**Why:** the cover page should read like the finished claim: what was insured, what was paid in total, and when it wrapped up.

---

## Decision 3 — What happens to the duplicate rows we remove?

**Recommendation: remove them from the file we load into QLAdmin, but save every removed row in an audit file.**

Nothing is destroyed — we keep a complete before-and-after record so any removal can be reviewed or undone. The audit file lives in our Reports folder and never goes into the load.

**Why:** clean data in QLAdmin, full paper trail for us.

---

## Decision 4 — How do the checks find their claim?

**Recommendation: each check follows its own claim.** We match checks to claims by payment date and amount. If a check can't be confidently matched, we attach it to the surviving claim header and **flag it on an exception list** for human review — we never silently guess and never drop a check.

**Why:** the money must stay attached to the story it belongs to, and anything uncertain gets eyes on it.

---

## Decision 5 — What order do we do the work?

**Recommendation: fix the folder structure first (this issue), then fix the money fields (Issue #84).**

- Issue #84 wants to fill in the money breakdown on claims (dividends, loan, interest, etc.) and make Net Payment match the checks. Doing that on top of duplicated cover pages means doing it twice.
- One exception can go now: Issue #84 "Track A" — about 300 claims where checks exist but the header still says $0 paid. That fix is safe regardless of this issue.

**Why:** fix the shelves before restocking them.

---

## What these decisions will NOT do

- No checks/payees will be invented or deleted (Issue #78 work is preserved)
- Claim statuses stay as decided in Issue #79
- No changes to policy master, rider, or rate files
- No code is written until these decisions are approved and the Risk step signs off

---

## What we need from the reviewer

Read the five recommendations. For each one, either **approve** or tell us what to change. Decision 1 is the important one — the rest follow from it.
