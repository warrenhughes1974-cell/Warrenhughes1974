# Issue #117 — Intake Summary

**Issue:** #117 — Dividend history is credits-only: QuikBenh missing MBENTYP 6 (interest) and 7 (surrendered accumulations), and the conversion opening row is not a balance
**Date:** 2026-07-25
**Framework stage:** Intake (Stage 1 of 8)
**Status:** Intake
**Owner:** Warren
**Assigned:** Warren
**Priority:** Go-No Go
**Raised by:** Warren, 2026-07-25, following a client-side review question on whether LifePRO was sending debits as well as credits
**Related:** #114 (dividend history, Closed v58.36 — this extends it), #38 / #116 (quikdvdp balance and interest date), #54 (QuikBenh loan history pattern), #110 (MDIVOPT), #115 (quikdvpr)

---

## Symptom

QLAdmin's Dividend History window does not reconcile to the balance shown in its own footer.

Policy **9010380808C**: nine history rows totalling $4,610.10 against a Current Balance of
$9,220.33. Policy **9010382426C**: history of $5,409.60 against a balance of $4,020.04 —
the gap runs in both directions.

The reason is that Issue #114 emits only dividend **credits** (MBENTYP 1–5). QLAdmin's
dividend history is a **full ledger**: credits, interest earned, and money withdrawn.

---

## Confirmed during intake

### 1. The benefit type codes exist and are documented

QLAdmin Help **§6.5 "Policy Benefit Type Codes", p.649 (PDF p.636)**:

| Code | Official label | Status in our Output |
|---|---|---|
| 1 | Dividends paid in cash | emitted (#114) — 209 rows |
| 2 | Dividends applied to premium | emitted (#114) — 37 rows |
| 3 | Dividends left to accumulate | emitted (#114) — 264 rows |
| 4 | Dividends to purchase PUA | emitted (#114) — 2,569 rows |
| 5 | Dividends to purchase one year term | none in fleet |
| **6** | **Interest on policy funds / dividend accumulation** | **not emitted** |
| **7** | **Surrendered dividend accumulations** | **not emitted** |
| 8 | Surrender benefits | emitted (#34) |
| 10 / 11 / 12 | Policy loans granted / interest received / payments | emitted (#54) |

Issue #114's Dependency Gate cited this same page but scoped the reading to codes 1–5, so
6 and 7 were never considered.

### 2. Production QLAdmin data confirms the model

The client's own production `docs/QUIKBENH.DBF` (1,597,257 rows) uses both codes:

- **Type 6** posts alongside type 3 on the same anniversary, compounding as the balance
  grows — e.g. policy 21316LK, type 3 of 0.52…1.10 each year with type 6 of 0.03, 0.06,
  0.09, 0.12, 0.16, 0.21, 0.27, 0.34, 0.40, 0.48, 0.55.
- **Type 7** drains the accumulation. Policy 16237K reaches exactly $10.04 under
  3 + 6, a type 7 of exactly $10.04 posts in December 2022, and interest restarts from
  near zero afterwards (0.39 → 0.04).

**Balance = sum(3) + sum(6) − sum(7)**, and it holds on **425 of 464** production
accumulate policies. The 39 exceptions are policies whose pre-conversion history was never
carried across — the client's own version of the gap described below.

`MBEN` also carries negative amounts in production (2,781 rows), though the client's
convention is a positive amount under type 7 rather than a negative type 3.

### 3. Warren's production screenshot matches exactly

Policy 02792356W shows "Dividends Left to Accumulate" and "Interest on Policy Funds"
interleaved on the same dates, with the footer Current Balance, Accrued Interest and
Interest Paid To beneath. That is the target presentation.

### 4. The source data is present and unused

| Row type | PACTG source | Volume | Currently |
|---|---|---:|---|
| MBENTYP 6 | debit `0641` "Interest on Dividend Accums" → credit `0310` | 788 rows / 63 policies / **$49,071.94** | explicitly excluded by `quikbenh_dividend_history_rules.json` |
| MBENTYP 7 | debit `0310` (accumulation drawn down) | 27 rows / 24 policies / **$93,804.91** | explicitly excluded — account 0310 dismissed as "a balance account, not a credit event" |

Type 7 destinations are 0038 Death Clearing (13 rows, $50,964.33), 0013 surrender
clearing (11 rows, $39,690.46) and 0012 (3 rows, $3,150.12).

### 5. The opening row is a credits remainder, not a balance

Issue #114 dates one catch-up row at 20171231 carrying `DIVIDENDS_CREDITED` minus the
in-window credits. That ties the type-3 total to LifePRO, which was #114's stated goal,
but it is not the accumulation balance at that date and so cannot make the screen foot.

For 9010380808C the true opening balance is $5,782.22 — $3,195.30 of pre-2018 dividends
plus $2,586.92 of pre-2018 interest. The current single row carries only the $3,195.30.

---

## Scope

**In scope**

- Emit **MBENTYP 6** from PACTG 641 for the 2018-forward window
- Emit **MBENTYP 7** from PACTG debit-310 postings for the 2018-forward window
- Re-derive the 20171231 opening row as a **true opening balance**, split into a type 3
  component (pre-2018 dividends — unchanged from #114, preserving its reconciliation) and a
  type 6 component (pre-2018 interest, derived as the residual that makes the ledger foot)
- Reconcile each accumulate policy: sum(3) + sum(6) − sum(7) = `quikdvdp.MDEPOSIT`
- Validation and exception reporting under `QLA_Migration/Reports/`

**Out of scope**

- MBENTYP 1, 2, 4, 5 emission logic (#114) — those dispositions leave the policy, there is
  no balance to foot to, and credits-only is correct for them
- `quikdvdp.MDEPOSIT` (#38) and `MDEPINT` — **Eric confirmed 2026-07-25 that the QLAdmin
  rates are correct**
- `quikdvdp.MINTDATE` / `MINTYTD` (#116)
- MBENTYP 8 (#34) and 10 / 11 / 12 (#54) — preserved untouched
- `quikdvpr` (#115)
- The five policies whose credits exceed their balance are **in scope for identification**
  but their plug is a business decision — see below

---

## Known gap requiring client input

Five of the 59 balance-carrying policies have lifetime credits exceeding their balance,
and the difference originates before 2018 where PACTG cannot see:

| Policy | Option | Balance | Lifetime credits | Gap |
|---|---|---:|---:|---:|
| 9010382426 | 3 | 4,020.04 | 5,409.60 | 1,389.56 |
| 9010458525 | 6 | 529.93 | 1,866.46 | 1,336.53 |
| 9010451453 | 6 | 353.29 | 4,191.45 | 3,838.16 |
| 9010497768 | 3 | 263.20 | 2,727.08 | 2,463.88 |
| 9010457623 | 3 | 1.53 | 2,596.00 | 2,594.47 |

Two explanations fit equally: a pre-2018 withdrawal, or a dividend option change (dividends
taken as cash or PUA count in `DIVIDENDS_CREDITED` but never enter the accumulation). Ten
policies demonstrably post under more than one election code even inside the short
2018-forward window, so option changes are real. LifePRO's own dividend history for these
policies would settle it.

---

## Affected path (anticipated)

- `qla_core/quikbenh_dividend_history_converter.py`
- `plan_governance/config/quikbenh_dividend_history_rules.json`
- `app.py` + `QLA_Migration/app.py` — existing `_emit_quikbenh_dividend_history` wiring, version bump
- `QLA_Migration/Reports/issue117_*.csv`

---

## G0 gate

| Criterion | Result |
|-----------|--------|
| Issue scoped | Yes |
| Symptom measurable from current Output | Yes — 0 rows of MBENTYP 6 and 7; ledger fails to foot on all 59 balance-carrying policies |
| Source artifacts identified | Yes — PACTG 641 and debit-310, both in `Source/` |
| QLAdmin target semantics confirmed | Yes — Help §6.5 p.649, corroborated by 1.6M production rows |
| Severity / owner assigned | Yes — Go-No Go, Warren |

**G0 PASS** — proceed to Planning.
