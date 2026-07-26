# Issue #117 — Dependency Gate

**Issue:** #117 — Dividend history is credits-only: QuikBenh missing MBENTYP 6 and 7, opening row is not a balance
**Framework stage:** Dependency Gate (Stage 3 of 8)
**Generated:** 2026-07-25
**Agent:** Cursor Grok 4.5
**Code changes:** none (prohibited at this stage)

---

## Status: **PASS**

Both missing benefit types are documented in the QLAdmin manual and demonstrated in 1.6M
rows of the client's own production data. The source transactions are present in the PACTG
extract and are currently being discarded by an explicit exclusion rule. One business
question remains open, covering **5 of 59 policies**, and it carries a safe default that
withholds data rather than guessing it. Proceed to Risk.

---

## 1. Checklist

### Source data

| Check | Met? | Evidence |
|-------|------|----------|
| Required LifePRO extract present | **Met** | `PACTG_Accounting_Extract20260630.csv` and `PPBENTYP_BenefitType_Extract_20260630.csv`, both in `QLA_Migration/Source/` |
| MBENTYP 6 source rows present | **Met** | 788 non-reversed debit-`0641` rows, 63 policies, $49,071.94 |
| MBENTYP 7 source rows present | **Met** | 27 non-reversed debit-`0310` rows, 24 policies, $93,804.91 |
| Reconciliation target available | **Met** | `PPBENTYP.ACCUM_DIVIDENDS`, 59 policies, $240,248.25 |
| Extract date matches batch under test | **Met** | 20260630, same drop feeding v58.36 |
| Re-extract required? | **No, but noted** | A pre-2018 PACTG pull would remove the opening row entirely and resolve the 5 shortfall policies outright. Not required — #21F and #114 set the precedent for plugging the window floor. |

### Field definitions

| Check | Met? | Evidence |
|-------|------|----------|
| QLAdmin target table confirmed | **Met** | `QuikBenh` — `MPOLICY` C10, `MBENTYP` C2, `MDATE` D8, `MBEN` N10.2 |
| **MBENTYP 6 label confirmed** | **Met** | Help §6.5 p.649 (PDF p.636) — "Interest on policy funds / dividend accumulation" |
| **MBENTYP 7 label confirmed** | **Met** | Help §6.5 p.649 — "Surrendered dividend accumulations" |
| Balance model confirmed | **Met** | sum(3) + sum(6) − sum(7) holds on **425 of 464** production accumulate policies in `docs/QUIKBENH.DBF`; policy 16237K drains to exactly 0.00 on a type 7 of 10.04 |
| Presentation confirmed | **Met** | Production policy 02792356W screenshot — types 3 and 6 interleaved on the same dates under a Current Balance footer |
| Negative `MBEN` supported | **Met** | 2,781 negative rows exist in production, but the client's convention is a positive amount under type 7 — we follow the client convention |
| LifePRO source semantics confirmed | **Met** | Account `0641` "Interest on Dividend Accums", account `0310` "Dividend Accums on Deposit" — both named in `quikbenh_dividend_history_rules.json` |
| Transformation notes identified | **Met** | Planning §2 and §3 — sources, contra netting, opening split |

### Client clarification

| Check | Met? | Evidence |
|-------|------|----------|
| Scope boundary agreed | **Met** | Warren 2026-07-25: complete the ledger; leave the rates alone |
| Crediting rate (`MDEPINT`) | **Resolved — out of scope** | Eric confirmed 2026-07-25 that the QLAdmin rates are correct |
| Business rule for edge cases | **Met with default** | OQ-1 below; withhold and report, no guessed plug |
| UAT acceptance criteria stated | **Met** | Dividend History window foots to its own Current Balance footer for 54 of 59 accumulate policies; #114's tie to `DIVIDENDS_CREDITED` still passes |

### Evidence

| Check | Met? | Evidence |
|-------|------|----------|
| Example policies identified | **Met** | 9010380808C (interest missing), 9010382426C (credits exceed balance), production 16237K / 21316LK / 02792356W |
| Screenshots support the claim | **Met** | Two QLAdmin screens supplied by Warren 2026-07-25 |
| Before-state measurable from current Output | **Met** | MBENTYP 6 and 7 = **0 rows**; 0 of 59 accumulate policies foot |
| Projection published | **Met** | `evidence/issue117_dividend_ledger_projection.csv` |

### Regression guards

| Check | Met? | Evidence |
|-------|------|----------|
| Plan preserves #114 MBENTYP 1–5 | **Met** | Type 3 opening component is arithmetically identical to today's plug; types 1 / 2 / 4 untouched |
| Plan preserves #34 MBENTYP 8 | **Met** | Outside the replace set |
| Plan preserves #54 MBENTYP 10 / 11 / 12 | **Met** | Outside the replace set |
| Plan preserves #38 `quikdvdp` | **Met** | Read-only reconciliation target |
| Plan preserves #116 | **Met** | Different table, no interaction; #116 sequenced first |
| Plan preserves #25 MPOLICY padding | **Met** | `format_qladmin_mpolicy` for all emitted keys |
| Plan does not alter unrelated rulebooks | **Met** | Existing converter and rules JSON extended; no `Sync_Rulebook_*.csv` edits |

---

## 2. Open items carried forward (non-blocking)

| # | Question | Policies | $ | Default if unanswered |
|---|----------|---------:|--:|----------------------|
| OQ-1 | Five policies have lifetime credits exceeding their balance. Pre-2018 withdrawal, or a dividend option change (cash / PUA dividends count in `DIVIDENDS_CREDITED` but never enter the accumulation)? Ten policies demonstrably post under multiple election codes even in the short 2018-forward window. | 5 | 11,622.60 combined gap | Emit type 3 opening and window rows only; no type 6 opening, no guessed type 7; route to exception report with the computed shortfall |
| OQ-2 | Two of those five are dividend option 6 (Reduce Loan), already withheld under #114 OQ-1 | 2 | 5,174.69 | Unchanged — remain withheld |
| OQ-3 | Should a pre-2018 PACTG re-pull be requested to eliminate the opening row entirely? | all 59 | — | No — plug per #21F / #114 precedent; revisit only if OQ-1 blocks UAT |

**Exposure of OQ-1:** 5 of 59 balance-carrying policies. The remaining **54 policies
reconcile to the cent** under the proposed model.

---

## 3. Blockers

**None.**

No missing extract, no undefined QLAdmin field, no absent example policies. The two
benefit type codes that #114 omitted are enumerated in the manual and in daily use in the
client's production database, and the transactions that populate them are already in the
extract we read today.

---

## 4. Recommended issue status update

**Ready for Risk Review**

---

## G2 gate criteria

- [x] Dependency gate document published
- [x] Status is PASS
- [x] Tracking sheet row published (`Issue_117_Tracking_Sheet_Row.tsv`)
- [x] No code changes made
