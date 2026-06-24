# Client Issue Log Decisions — Items 14–19

**Recorded:** 2026-06-11
**Source:** Client responses to `Issue Log Items.docx` follow-up questions
**Status:** Authorized business decisions (pending items noted at bottom)

---

## Item 14 — Surrender Validation

| # | Question | Client Decision |
|---|---|---|
| 14.1 | Are the Item 14 accounting chains (`2031` Surrender Clearing ↔ `604416R`/`604606R`/`603616R`, `2019` Unapplied Cash → `1056` Payout) the only valid true-surrender patterns? | **YES — these are the only valid patterns.** |
| 14.2 | Should surrender items showing only loan codes (`7046` Int Income / `1017` Loan) be excluded from claims entirely? | **YES — exclude; treat as loan accounting, not surrenders.** |
| 14.3 | Policy numbers for Item 14 examples? | Not provided. **Proceed best-effort against the 500-item surrender queue; client will flag issues.** |

**Impact:** Validates Phase 22 semantic governance holds (loan-only chains quarantined from QUIKCLMS). Surrender review queue (500 items) can be triaged against the approved patterns.

---

## Item 15 — Orphan Payments

| # | Question | Client Decision |
|---|---|---|
| 15.1 | Orphan payments with blocked parent claims (e.g., $7,770.08 on `9010363098`, $8,353.43 on `9010374779`): fix parent, convert standalone, or defer? | **(B) Convert the payment STANDALONE.** |
| 15.2 | Policy number for $1,134.57 orphan example? | Not provided. |

**Impact:** The 374 deferred orphan payments move from `DEFERRED_NOT_IN_UAT` toward standalone conversion treatment (mechanics to be confirmed — see open items).

---

## Item 16 — Unbalanced Claims

| # | Question | Client Decision |
|---|---|---|
| 16.1 | Permanently exclude `603703R` / `2023 Div Left on Dep` from death-benefit balancing for ALL claims? | **YES — exclude `2023` on all claims.** |
| 16.2 | With exclusion applied, approve `9010150740` ($3,213.59) and `9010331157` ($19,446.62) for UAT? | **YES — confirmed for UAT inclusion.** |
| 16.3 | `9010335038` (no accounting, terminated death claim 4/22/2018): convert or exclude? | **Convert with NO financial history.** |

**Impact:** Balancing rule refinement authorized. Two previously deferred unbalanced claims approved for UAT. One no-accounting claim converts header-only.

---

## Item 18 — Potential Missing Claims

| # | Question | Client Decision |
|---|---|---|
| 18.1 | When loan payoff is part of a death settlement, should QLAdmin claim amount be DB only or DB + loan payout combined? | **DB + loan payout COMBINED.** |
| 18.2 | Policy numbers for Item 18 examples ($5,603.16, $7,041.97, $22,556.61)? | Not provided. |

**Impact:** Claim amount derivation rule: death settlements include loan payoff in the converted claim amount.

---

## Item 19 — Payee/Beneficiary Validation

| # | Question | Client Decision |
|---|---|---|
| 19.1 / 19.2 | `010807842C` ($125,000, payee shown as insured Patricia Mayhew): correct payee? Issued wrong in LifePRO or extract-only issue? | **"The payee was correct but the payout was to Kenneth Wayne Matthew."** (Clarification pending — see open items.) |

Previously confirmed correct (no action needed):
- `011054986C` — RONALD LETHEBY, $100,380.91
- `010724403C` — JULIE FRAME, $100,000.00
- `010752477C` — JUDY ABRAHAM, $75,784.19

---

## General

| # | Question | Client Decision |
|---|---|---|
| G.1 | Validate against May 31 month-end data, or proceed with prior extract? | **Proceed with current data. No May re-validation required for sign-off.** |

---

## Follow-up clarifications (resolved 2026-06-11)

| # | Item | Clarification | Client Decision |
|---|---|---|---|
| 1 | Item 19 | QLAdmin payee for `010807842C` $125,000 = **KENNETH WAYNE MATTHEW** (replacing PATRICIA MAYHEW)? | **YES** |
| 2 | Item 15 | Scope of standalone treatment | **ALL 374 deferred orphan payments** stand alone |
| 3 | Item 15 | Claim status for standalone payment headers | Client requested recommendation — **recommended: CLAIMSTAT = 3 (SETTLED)**, consistent with existing DEATH_CLAIM settled mapping; payouts already completed historically in LifePRO. Importing as OPEN (1) would place historical claims into active QLAdmin work queues. |
| 4 | Item 16 | `9010335038` header values: Terminated Death Claim, status date 4/22/2018, amount $0, no financial history | **YES** |
| 5 | Item 18 | Include `7046` loan interest in DB + loan payout combined amount | **YES** |

---

*These decisions authorize claims rule refinements. Implementation requires a governed re-run of the claims pipeline (Phases 15/17 refresh) — production_dbf_flag remains N until enterprise sign-off.*
