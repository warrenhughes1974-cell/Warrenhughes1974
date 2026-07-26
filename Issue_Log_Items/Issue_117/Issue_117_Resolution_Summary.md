# Issue #117 — Resolution Summary (Stage 8, Closure)

**Closed:** 2026-07-26  
**Engine:** v58.37  
**Status:** Closed — G7 gate satisfied  

---

Resolution: QuikBenh dividend history is now a full accumulation ledger — dividends (types 1–5), interest credited (type 6), and withdrawals (type 7) — so history foots to the QuikDvdp balance for policies with complete post-2017 accounting.

---

## The problem, in plain terms

Issue #114 loaded dividend credits, but QLAdmin's dividend history screen is meant to be a running account. Interest left on deposit and money taken out were missing, so history did not add up to the on-screen balance (gaps in both directions).

## Fix (v58.37)

Treat dividend history as a ledger:

- **MBENTYP 6** — interest credited (PACTG 0641 → 0310)
- **MBENTYP 7** — accumulation outflows (0310)
- Net self-reversing 0310 pairs; split 20171231 opening into type 3 + type 6 where needed so `sum(3)+sum(6)-sum(7)` foots to QuikDvdp
- Issue #114 type 1–5 amounts preserved by design; types 8/10/11/12 unchanged

## Held exceptions (by design)

Three policies still do not foot because LifePRO shows more lifetime dividends than the current balance can explain and our accounting extract only goes back to 2018 — guessing a pre-2018 withdrawal would invent history:

- `9010382426` — history short vs balance (original review policy)
- `9010457623`
- `9010497768`

(Validator reports 4 known/reported exceptions including related held cases; unexplained variances = 0.)

## Validation / G7 (full Output 2026-07-26)

| Check | Result |
|---|---|
| `validate_issue117.py` | **PASS** — 55/59 foot; unexplained 0 |
| `validate_issue114_dividend_history.py` (allow 6/7) | **PASS** — types 1–5 preserved |
| Row counts | baseline 40,510 + div 3,079 + ledger 867 = **44,456** |
| Accountability | **IN_DATA** |

## Rollback

Revert `qla_core/quikbenh_dividend_history_converter.py` + `plan_governance/config/quikbenh_dividend_history_rules.json` and restore prior `quikbenh.csv`. Branch `issue-34-pr7-quikisrr`.
