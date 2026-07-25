# Issue #114 — Validation Report (Stage 6)

**Date:** 2026-07-25
**Engine:** v58.36
**Validator:** `tools/validators/validate_issue114_dividend_history.py` (script v1.0)
**Result:** **PASS**

---

## Result

```
OK: quikbenh schema (4 fields)
OK: quikbenh.csv rows=43589 MBENTYP counts={'11': 14156, '12': 19135, '10': 3562, '8': 3657,
                                            '1': 209, '3': 264, '4': 2569, '2': 37}
OK: prior-issue rows preserved (8=3657, 10=3562, 11=14156, 12=19135)
OK: dividend rows (1-5)=3079 types={'1': 209, '2': 37, '3': 264, '4': 2569, '5': 0}
OK: additive only (40510 + 3079 = 43589)
OK: dividend MPOLICY values are 11 characters (padded)
OK: dividend MDATE YYYYMMDD format
OK: all dividend MBEN values positive
OK: dividend MBEN formatted to 2 decimals
OK: at most one 20171231 conversion adjustment per policy (579 policies)
OK: dividend-history policies=586
OK: 579 of 593 policies tie exactly to PPBENTYP DIVIDENDS_CREDITED (14 withheld to exceptions)
OK: converted $1,875,297.82 of $1,889,445.44 lifetime dividends (99.25%)
RESULT: PASS
```

The validator recomputes lifetime totals from the PPBENTYP extract itself rather than
reading the converter's own report, so it is capable of disagreeing with the converter.

---

## Defect found and fixed during validation

The first build emitted **2,504** Layer A rows. Regression check R7 flagged two repeated
`(policy, type, date, amount)` combinations, and tracing them to PACTG showed a real
double-count.

A dividend posts as a two-sided accounting entry. The dividend credited to the policy is
the **debit** leg — `debit 0517 / credit 0112` buys paid-up additions, `debit 0515 /
credit 0096` pays cash. The original code matched the election code on **either** leg, so
when a posting also carried the same code on its credit leg the dividend was written
twice.

Example — policy `9010429558`, 2021-09-01, $169.80:

| PACTG row | Credit | Debit | Meaning |
|---|---|---|---|
| control 445301926586 | 0096 | **0515** | the dividend, paid in cash |
| control 446291249170 | **0515** | 0012 | the clearing half of that same posting |

Both were emitted, so the policy showed two $169.80 cash dividends on the same day.

Across the whole extract, 2,500 of 2,504 rows carry the election code on the debit leg and
only 4 on the credit leg. Of those 4, two are duplicate clearing legs as above, and two
are reversals that `DATE_REVERSED` never flagged — one of which (`9010449158`, 2026-03-03,
$150.18) also explains the odd duplicate date sitting in `quikdvpr` and is now documented
in Issue #115.

**Fix:** emit only when the election code is on the debit leg. The 4 contra rows are
written to the exception report as `CONTRA_SIDE_NOT_EMITTED` rather than dropped silently.

Worth noting why the per-policy totals passed even while the rows were wrong: the Layer B
plug is computed as lifetime minus Layer A, so an inflated Layer A silently shrank the
plug and the policy still tied. The dollars balanced; the transaction detail did not. Only
the row-level duplicate check caught it.

---

## Reconciliation

| Measure | Value |
|---|---|
| LifePRO lifetime dividends (PPBENTYP BA `DIVIDENDS_CREDITED`) | $1,889,445.44 across 593 policies |
| Layer A — PACTG election transactions (debit leg) | 2,500 rows / $401,443.32 / 413 policies |
| Layer B — conversion adjustments (20171231) | 579 rows / $1,473,854.50 |
| Total loaded | $1,875,297.82 (99.25%) |
| Withheld to exceptions | $14,147.62 across 14 policies |
| **Per-policy variance on all 579 converted policies** | **$0.00 (max absolute)** |

Every converted policy ties to the penny. The 0.75% shortfall is entirely the 14
deliberately withheld policies, not rounding or leakage.

### Rows by benefit type

| MBENTYP | Meaning | Layer A | Layer B | Total |
|---|---|---|---|---|
| 1 | Dividend paid in cash | 177 | 32 | 209 |
| 2 | Dividend reduces premium | 30 | 7 | 37 |
| 3 | Dividend left on deposit | 200 | 64 | 264 |
| 4 | Dividend buys paid-up additions | 2,093 | 476 | 2,569 |
| 5 | Dividend buys one-year term | 0 | 0 | 0 |

Type 5 is zero because no policy in this book elects one-year term dividends — LifePRO
option 5 does not appear in `PPBENTYP.DIVIDEND` and no 0518 transactions exist in PACTG.
Expected, not a gap.

### Policy status breakdown (593 with a lifetime total)

| Status | Policies |
|---|---|
| `PLUG_EMITTED` — PACTG window rows + pre-2018 plug | 406 |
| `OPENING_BALANCE` — plug only, no activity in the PACTG window | 173 |
| `UNMAPPED_OPTION_6` — Reduce Loan, withheld | 7 |
| `UNMAPPED_OPTION_BLANK` — no dividend option, withheld | 4 |
| `NEGATIVE_OR_ZERO_GAP` — PACTG already meets/exceeds lifetime | 3 |

---

## Sample traces

Largest lifetime dividends, option 4 (paid-up additions):

| MPOLICY | Option | Type | Lifetime | PACTG txns | Layer A | Plug (20171231) | Final | Variance |
|---|---|---|---|---|---|---|---|---|
| 9010431301C | 4 | 4 | 11,907.00 | 8 | 3,684.75 | 8,222.25 | 11,907.00 | 0.00 |
| 9010543559C | 4 | 4 | 10,435.20 | 9 | 3,984.90 | 6,450.30 | 10,435.20 | 0.00 |
| 9010397118C | 4 | 4 | 9,893.09 | 8 | 3,120.91 | 6,772.18 | 9,893.09 | 0.00 |

Plug-only policy (dividends stopped before the PACTG window):

| MPOLICY | Option | Type | Lifetime | PACTG txns | Plug | Final |
|---|---|---|---|---|---|---|
| 9010300689C | 3 | 3 | 4,440.45 | 0 | 4,440.45 | 4,440.45 |

Small mixed policy, option 1 (cash):

| MPOLICY | Option | Type | Lifetime | PACTG txns | Layer A | Plug | Final |
|---|---|---|---|---|---|---|---|
| 9010143726C | 1 | 1 | 945.44 | 9 | 185.85 | 759.59 | 945.44 |

---

## Preservation and safety checks

| Check | Result |
|---|---|
| Emitted file is a **byte-prefix extension** of the pre-#114 file | PASS — first 1,227,177 bytes identical; 3,079 rows appended |
| MBENTYP 8 (Issue #34) | 3,657 rows, unchanged |
| MBENTYP 10/11/12 (Issue #54) | 3,562 / 14,156 / 19,135 rows, unchanged |
| Re-run idempotency | PASS — second `--write-output` run produced an identical SHA-256 |
| Duplicate dividend rows | PASS — none after the debit-leg fix |
| Line endings | Preserved (LF), no whole-file rewrite |
| Other Output tables | Untouched; only `quikbenh.csv` written |
| Output folder hygiene | Only `quik*.csv` in `Output/` root; reports in `Reports/`, staging under `plan_analysis/` |

---

## Artifacts

| Path | Contents |
|---|---|
| `QLA_Migration/Reports/issue114_dividend_history_validation.csv` | 593 policies: lifetime, Layer A, plug, final, variance, status |
| `QLA_Migration/Reports/issue114_dividend_history_exceptions.csv` | 21 rows — 14 withheld policies, 3 OR-row exclusions, 4 contra-leg exclusions |
| `Issue_Log_Items/Issue_114/evidence/` | Copies of both reports plus the pre-change `quikbenh.csv` backup |
| `QLA_Migration/Output/Test_Validation/quikbenh.csv` | Published for partial UAT reload |
| `plan_analysis/phase_benh_dividend_history/` | Runner, emit summary, staged layer CSVs |

## Reproduce

```powershell
python plan_analysis\phase_benh_dividend_history\quikbenh_dividend_runner.py            # dry run
python plan_analysis\phase_benh_dividend_history\quikbenh_dividend_runner.py --write-output
python tools\validators\validate_issue114_dividend_history.py
```

Rollback: restore
`Issue_Log_Items/Issue_114/evidence/quikbenh_before_issue114_v5835_20260725_164158.csv`
over `QLA_Migration/Output/quikbenh.csv`.

---

## Open questions for Eric (do not block the 579 converted policies)

1. **OQ-1** — 7 policies use LifePRO dividend option 6 (Reduce Loan), $16,514.26. QLAdmin
   has no dividend-to-loan benefit type. Type them as 3 (left on deposit), leave them out,
   or something else?
2. **OQ-2** — $18,719.96 of dividends sit on non-BA rider rows for 3 policies. Include in
   the lifetime total or leave excluded (current behaviour, matching Issue #21F)?
3. **OQ-3** — 4 policies have a lifetime dividend total but no dividend option, $163.96
   total. Default them to option 3?
4. **OQ-4** — `quikdvpr` holds 31 historical rows in a table QLAdmin defines as a
   forward-looking schedule. **Raised as Issue #115** per Warren, 2026-07-25.

## Next stage

Stage 7 Regression — see `Issue_114_Regression_Report.md`.
