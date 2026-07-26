# Issue #117 — Planning Report

**Issue:** #117 — Dividend history is credits-only: QuikBenh missing MBENTYP 6 and 7, opening row is not a balance
**Framework stage:** Planning (Stage 2 of 8)
**Generated:** 2026-07-25
**Agent:** Cursor Grok 4.5
**Code changes:** none (prohibited at this stage)
**Baseline:** v58.36

---

## 1. Objective

Make the QLAdmin Dividend History window reconcile to its own footer for every policy on
the dividend-accumulation option, by completing the ledger that Issue #114 started.

Target identity, per QLAdmin Help §6.5 and verified on 425 of 464 production policies:

```
sum(MBENTYP 3) + sum(MBENTYP 6) - sum(MBENTYP 7) = quikdvdp.MDEPOSIT
```

---

## 2. Row sources

| MBENTYP | Label (Help §6.5 p.649) | LifePRO source | Sign |
|---|---|---|---|
| 3 | Dividends left to accumulate | PACTG debit `0514` → credit `0310` | inflow |
| 6 | Interest on policy funds / dividend accumulation | PACTG debit `0641` → credit `0310` | inflow |
| 7 | Surrendered dividend accumulations | PACTG debit `0310` → any credit | outflow |

All three are read from the debit leg, consistent with #114's `emit_side: debit` rule.
Reversed rows (`DATE_REVERSED` non-zero) are excluded as they are today.

**Contra handling.** A small number of debit-310 postings are reversed by a matching
credit-310 entry under a non-dividend debit code days later — policy 9010382426 has a
$2,594.56 pair three days apart in April 2026 that nets to zero. These must be netted, not
emitted as a type 7, or the ledger will understate the balance. Detection is an exact
amount match against a credit-310 posting under a debit code outside `0514–0518` / `0641`.

---

## 3. Opening row (20171231)

Replace #114's single credits-remainder row with a two-part opening that carries the real
balance at the conversion floor:

| Component | MBENTYP | Amount |
|---|---|---|
| Pre-2018 dividends | 3 | `DIVIDENDS_CREDITED` − in-window type 3 — **identical to today's #114 plug** |
| Pre-2018 interest | 6 | opening balance − pre-2018 dividends |

where

```
opening balance = MDEPOSIT - window(3) - window(6) + window(7) - window(contra)
```

Because the type 3 component is unchanged, **#114's reconciliation to
`PPBENTYP.DIVIDENDS_CREDITED` is preserved exactly** while the balance now also foots.

Worked example, 9010380808C:

| Row | Before (#114) | After (#117) |
|---|---|---|
| 20171231 type 3 | 3,195.30 | 3,195.30 (unchanged) |
| 20171231 type 6 | — | **2,586.92** |
| 2018–2025 type 3 | 1,414.80 (8 rows) | 1,414.80 (unchanged) |
| 2018–2025 type 6 | — | **2,023.31 (16 rows)** |
| **Ledger total** | 4,610.10 | **9,220.33** |
| `quikdvdp.MDEPOSIT` | 9,220.33 | 9,220.33 |
| **Foots?** | **No — short $4,610.23** | **Yes, to the cent** |

---

## 4. Expected volumes

Projection from `Source/` — see `evidence/issue117_dividend_ledger_projection.csv`
(59 rows, one per policy holding a balance).

| Measure | Before | After |
|---|---:|---:|
| `quikbenh` MBENTYP 6 rows | 0 | 788 window + 54 opening |
| `quikbenh` MBENTYP 7 rows | 0 | up to 27 window (less netted contras) |
| MBENTYP 3 rows | 264 | 264 (unchanged) |
| MBENTYP 1 / 2 / 4 rows | 209 / 37 / 2,569 | unchanged |
| MBENTYP 8 / 10 / 11 / 12 rows | 3,657 / 3,562 / 14,156 / 19,135 | unchanged |
| Balance-carrying policies whose ledger foots | 0 of 59 | **54 of 59** |

Of the 59 policies, **54 split cleanly** into a type 3 and a non-negative type 6 opening.
The remaining **5** produce a negative type 6, meaning value left the account before 2018.

---

## 5. The five policies that do not foot

| Policy | Option | Balance | Lifetime credits | Implied pre-2018 outflow |
|---|---|---:|---:|---:|
| 9010382426 | 3 | 4,020.04 | 5,409.60 | ≥ 2,128.46 |
| 9010458525 | 6 | 529.93 | 1,866.46 | ≥ 1,382.89 |
| 9010451453 | 6 | 353.29 | 4,191.45 | ≥ 3,843.34 |
| 9010497768 | 3 | 263.20 | 2,727.08 | ≥ 2,204.58 |
| 9010457623 | 3 | 1.53 | 2,596.00 | ≥ 2,594.85 |

Two of the five are dividend option 6 (Reduce Loan), which #114 already withholds under
OQ-1, so only three are live cases.

**Default if unresolved:** emit the type 3 opening and the in-window rows, omit a type 6
opening, and route the policy to the exception report with the computed shortfall. No
guessed type 7 plug. This mirrors #114's convention of withholding rather than inventing,
and mirrors the client's own production data, where 39 policies likewise do not foot
because pre-conversion history was not carried.

**Preferred resolution:** LifePRO dividend accumulation history for 9010382426 and
9010457623 would distinguish a genuine withdrawal from a dividend option change.

---

## 6. Validation plan

1. For all 54 clean policies: sum(3) + sum(6) − sum(7) equals `quikdvdp.MDEPOSIT` to the cent.
2. Per policy, sum of MBENTYP 3 still equals `PPBENTYP.DIVIDENDS_CREDITED` minus any
   non-accumulate disposition — **#114's assertion must still pass unchanged**.
3. MBENTYP 6 window rows tie to the PACTG 641 total of $49,071.94 across 63 policies.
4. MBENTYP 7 window rows tie to the debit-310 total of $93,804.91 less netted contras.
5. No negative `MBEN` emitted (client convention is a positive amount under type 7).
6. No type 6 or 7 row dated later than the extract date 20260630.
7. The 5 shortfall policies appear in the exception report with their computed gap.
8. Running ledger never goes negative on any emitted policy.

## 7. Regression plan

| Guard | Check |
|---|---|
| #114 MBENTYP 1–5 | Type 3 rows and totals byte-identical; types 1 / 2 / 4 untouched |
| #34 MBENTYP 8 | 3,657 rows byte-identical |
| #54 MBENTYP 10 / 11 / 12 | 3,562 / 14,156 / 19,135 rows byte-identical |
| #38 `quikdvdp.MDEPOSIT` | Read-only — used as the reconciliation target, never written |
| #116 `MINTDATE` | Different table; no interaction |
| #25 MPOLICY padding | `format_qladmin_mpolicy` for all emitted keys |
| Schema | `MPOLICY, MBENTYP, MDATE, MBEN` order and types preserved |
| Idempotency | Replace-set extends from `{1,2,3,4,5}` to `{1,2,3,4,5,6,7}`; re-running produces identical output |

**Sequencing note.** #116 should land first. It does not change any value #117 depends on,
but it makes the QLAdmin screen readable end to end, so a single UAT pass can confirm both
the ledger and the footer.

---

## G1 gate

| Criterion | Result |
|---|---|
| Target model confirmed against the manual and production data | Yes — Help §6.5 p.649; 425 of 464 production policies |
| Change is additive and reversible | Yes — new row types, replace-set guarded |
| Before/after quantified from data | Yes — 59-row projection published |
| Validation and regression checks defined | Yes — §6 and §7 |
| Unresolved business questions have safe defaults | Yes — §5, withhold and report |
| No code written at this stage | Correct |

**G1 PASS** — proceed to Dependency Gate.
