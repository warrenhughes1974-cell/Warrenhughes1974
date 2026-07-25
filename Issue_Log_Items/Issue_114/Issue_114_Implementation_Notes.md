# Issue #114 — Implementation Notes (Stage 5, Development)

**Date:** 2026-07-25
**Engine:** v58.35 → **v58.36**
**Approval:** Warren, 2026-07-25 — "Approved for Development", exceptions withheld for the edge-case policies; `quikdvpr` deferred to a separate issue (OQ-4 answer A).

---

## What was built

LifePRO dividend history now converts into **QuikBenh** (Policy Benefit History) as benefit
types 1-5, using the same two-layer shape as the Issue #21F premium history fix.

| Layer | Source | Rows | Dollars | MDATE |
|---|---|---|---|---|
| A — real transactions | PACTG dividend election codes 0514/0515/0516/0517/0518, debit leg | 2,500 | $401,443.32 | actual `EFFECTIVE_DATE` (2018+) |
| B — conversion adjustment | `PPBENTYP.DIVIDENDS_CREDITED` minus Layer A | 579 | $1,473,854.50 | `20171231` |

Together these give QLAdmin the dividend component of cost basis. The premium component
was already delivered by Issue #21F, so the two figures a cost-basis calculation needs are
now both in the load.

### Code-to-benefit-type mapping

| PACTG code | LifePRO meaning | QuikBenh MBENTYP |
|---|---|---|
| 0515 | Dividend paid in cash | 1 |
| 0516 | Dividend reduces premium | 2 |
| 0514 | Dividend left on deposit | 3 |
| 0517 | Dividend buys paid-up additions | 4 |
| 0518 | Dividend buys one-year term | 5 |

Layer B rows are typed from `PPBENTYP.DIVIDEND` (the policy's standing dividend option)
using the same 1→1 … 5→5 mapping.

Only the **debit leg** of each PACTG transaction is emitted. The dividend is credited to
the policy on the debit side (`debit 0517 / credit 0112` buys paid-up additions). The same
code appearing on the credit leg is the contra side — either the clearing half of a
posting already captured, or a reversal `DATE_REVERSED` did not flag — and emitting it too
would count the dividend twice. Four such rows exist; they go to the exception report as
`CONTRA_SIDE_NOT_EMITTED`. Regression check R7 caught this after the first build; see the
Validation Report.

---

## Files

| File | Change |
|---|---|
| `qla_core/quikbenh_dividend_history_converter.py` | **New.** Converter module. |
| `plan_governance/config/quikbenh_dividend_history_rules.json` | **New.** Code map, option map, plug date, exclusions, preserve list. |
| `plan_analysis/phase_benh_dividend_history/quikbenh_dividend_runner.py` | **New.** CLI runner (dry run by default, `--write-output` to emit). |
| `tools/validators/validate_issue114_dividend_history.py` | **New.** Issue validator. |
| `app.py` | Import, `_emit_quikbenh_dividend_history()` helper, quikbenh batch block now supports both emits, `APP_VERSION` v58.36. |
| `QLA_Migration/app.py` | Same four edits (mirror kept in sync). |

## Gating

```powershell
$env:QLA_ENABLE_QUIKBENH_DIVIDEND_EMIT = "1"   # run the emit
$env:QLA_QUIKBENH_DIVIDEND_WRITE_OUTPUT = "1"  # write Output/quikbenh.csv
```

Both default off, so a normal batch is unchanged until the flags are set. The Issue #54
loan flag (`QLA_ENABLE_QUIKBENH_LOAN_EMIT`) is untouched and independent — either, both,
or neither can run.

---

## Design decisions

**Append, don't re-sort.** The converter strips only MBENTYP 1-5 from the existing
`quikbenh.csv` and appends new rows at the end, leaving prior rows in their original
positions. The emitted file is a strict byte-prefix extension of the previous one, which
makes preservation of Issue #34 (type 8) and Issue #54 (types 10/11/12) provable by
comparison rather than by row counting.

**Line endings preserved.** `quikbenh.csv` was LF-terminated while pandas' default on
Windows is CRLF. Rewriting 40,510 untouched rows' line endings would have produced a
whole-file diff for no reason, so the writer detects and reuses the file's existing
terminator.

**Idempotent.** Because MBENTYP 1-5 are replaced rather than added to, re-running produces
a byte-identical file — verified.

**Nothing guessed, nothing silently dropped.** Any policy with a lifetime dividend total
that cannot be converted lands in
`QLA_Migration/Reports/issue114_dividend_history_exceptions.csv` with a reason. The
validator fails if a policy is missing from both the output and the exception report.

**PACTG streamed, not loaded.** The extract is ~800 MB; the converter reads it with the
`csv` module rather than pandas. Full run is about 50 seconds.

---

## Withheld populations (14 policies, $14,147.62)

| Reason | Policies | Dollars | Why |
|---|---|---|---|
| `UNMAPPED_OPTION_6` | 7 | $16,514.26 | LifePRO option 6 = Reduce Loan. QLAdmin has no dividend-to-loan benefit type; the nearest is type 12, which belongs to Issue #54 loan history. Needs a client answer (OQ-1). Four of the seven still get their real PACTG rows ($4,769.18); only the plug is withheld. |
| `UNMAPPED_OPTION_BLANK` | 4 | $163.96 | No dividend option on the PPBENTYP BA row, so the benefit type is not derivable (OQ-3). Small dollars. |
| `NEGATIVE_OR_ZERO_GAP` | 3 | −$2,530.60 | PACTG transactions already exceed the lifetime total. Their real transactions are still loaded; only the plug is suppressed, so no negative row is written. |

Three additional rows in the exception report are `OR_ROW_DOLLARS_EXCLUDED` — $18,719.96
of dividends carried on non-BA rider rows on 3 policies, excluded from the lifetime target
to match the Issue #21F premium treatment (OQ-2).

These four open questions are for Eric; none of them block the 579 policies that do
convert.

---

## Not in scope

`quikdvpr` still holds 31 rows of historical dividend-paid-premium data even though
QLAdmin defines QuikDvpr as the forward-looking "Dividends to Pay Premium" schedule.
Warren deferred this to a separate issue rather than folding it into #114.
