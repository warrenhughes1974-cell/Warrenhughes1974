# Issue #114 — Regression Report (Stage 7)

**Date:** 2026-07-25
**Engine:** v58.36
**Script:** `Issue_Log_Items/Issue_114/scripts/regression_issue114.py`
**Result:** **PASS**

---

## Result

```
PASS: R1 quikbenh is a byte-prefix extension of the pre-change file
      — 1,227,177 bytes preserved, 92,066 bytes appended
PASS: R2 prior-issue benefit types preserved (8 / 10 / 11 / 12)
      — 8=3657, 10=3562, 11=14156, 12=19135
PASS: R3 no dividend rows on non-candidate policies
      — 586 policies with rows, all within the 593 LifePRO candidates
PASS: R4 every dividend-history policy exists in quikmstr — 586 of 5083 master policies
PASS: R5 conversion adjustment type matches quikmstr.MDIVOPT (Issue #110)
      — 579 adjustment rows checked
INFO: quikdvdp unchanged: 5,083 rows, MDEPOSIT total $240,248.25
PASS: R7 duplicate dividend rows reviewed — none
REGRESSION RESULT: PASS
```

---

## What each check proves

**R1 — intended policies changed, nothing else moved.** The emitted `quikbenh.csv` is a
strict byte-prefix extension of the file that existed before this issue: the first
1,227,177 bytes are identical and 3,079 rows are appended. This is stronger than comparing
row counts — no pre-existing row shifted position, changed value, or changed line ending.

**R2 — prior fixes intact.** Issue #34's MBENTYP 8 rows and Issue #54's MBENTYP 10/11/12
rows are unchanged in count and, per R1, unchanged byte-for-byte.

**R3 — non-candidates untouched.** Every policy that received a dividend row is one of the
593 policies LifePRO reports a lifetime dividend for. No policy without dividends gained a
row.

**R4 — no orphans.** All 586 policies with dividend history exist in `quikmstr`.

**R5 — independent cross-table agreement.** For all 579 conversion adjustment rows, the
benefit type we assigned matches `quikmstr.MDIVOPT`, which was loaded separately by
Issue #110 from a different source path. Two independent derivations agree, which is
better evidence than either one alone.

**R7 — no double-counting.** No repeated `(policy, type, date, amount)` combination
remains.

---

## R7 caught a real defect

On the first run R7 reported 2 repeated combinations. Tracing them to PACTG showed the
converter was emitting both accounting legs of the same dividend, writing it twice. Full
detail is in `Issue_114_Validation_Report.md`; the short version is that the dividend is
credited on the **debit** leg and the same code appearing on the credit leg is the
contra side.

This is worth recording because the per-policy dollar reconciliation **passed** while the
rows were wrong. The Layer B plug is computed as lifetime minus Layer A, so an inflated
Layer A quietly shrank the plug and the policy still tied to the penny. A totals-only
check would have shipped this. The row-level duplicate check is what found it.

After the fix, Layer A dropped from 2,504 to 2,500 rows and $402,010.24 to $401,443.32;
the plug absorbed the same $566.92, so the reconciled total is unchanged.

---

## Tables not modified

| Table | Rows | Status |
|---|---|---|
| `quikmstr` | 5,083 | Untouched — `MDIVOPT` (#110) unchanged |
| `quikdvdp` | 5,083 | Untouched — MDEPOSIT total $240,248.25 (#38) |
| `quikdvpr` | 31 | Untouched — deferred to Issue #115 |
| `quikprmh` | — | Untouched — Issue #21F premium history unaffected |
| `quikloan` | 356 | Untouched |

Only `quikbenh.csv` was written. Confirmed by file modification times across `Output/`.

---

## Issue #54 validator — pre-existing failure, not a regression

`validate_issue54_quikbenh_loan_history.py` reports FAIL, and shows as `GAP` in the
accountability run. It fails **identically against the pre-#114 backup**:

- `MPOLICY width violations` — the script expects 10 characters; Issue #2 (v58.29) moved
  MPOLICY to 11.
- `Loan-type rows=36853 outside expected 37300–37600`, and the missing opening seed for
  `010822238C` — both use stale 10-character policy keys.

Verified by pointing that validator at the backup file: same three failures on 40,510 rows
as on 43,589. The accountability GAP count is 10 both before and after this change.

**Recommendation:** refresh the #54 validator's baselines for the 11-character MPOLICY.
That is a separate cleanup, not part of #114.

---

## Reproduce

```powershell
python Issue_Log_Items\Issue_114\scripts\regression_issue114.py
```
