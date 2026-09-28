# Issue 175 — Validation Report

**Issue:** 175 — Res Cat Unique Field
**Framework stage:** Validation Agent
**Output:** `QLA_Migration/Output/`
**Date:** 2026-09-28
**Verdict:** **PASS**

---

## Commands

```text
python tools/validators/validate_issue175_resrvcat.py
python QLA_Migration/_validate_issue141_resrvcat.py
python tools/publish_test_validation.py --clean --issue Issue_175 quikspec
```

Both validators exited 0. `Test_Validation` now holds `quikspec.csv` for this issue.

## Trace policies

| Policy | Reserve category | Vanish | State | Source policy | Result |
|---|---|---|---|---|---|
| 9011210337C | 13 | F | KY | 9011210337 | PASS |
| 9011216680C | 13 | F | IN | 9011216680 | PASS |
| 9011217014C | 12 | F | LA | 9011217014 | PASS |
| 9010143726C | 03 | | | | PASS (Issue 141) |
| 9010148272C | 03 | | | | PASS (Issue 141) |
| 9010713704C | 05 | | | | PASS (Issue 141) |

## Field alignment

| Check | Result |
|---|---|
| L15 | 11 policies, all 13 |
| L16 | 2 policies, all 13 |
| L17 BASE | 20 policies, all 12 |
| Category L | 0 |
| Category 13 | 845 |
| Category 12 | 541 |
| Issue 141 join mismatches | 0 |
| ISWLFE on the policy field | 0 |
| Plan product 1L15GD / 1L16GD / 1L17SP | 13 / 13 / 12 |
| Lines rewritten | 33, reserve category only |

## Row counts

| Table | Rows | Columns |
|---|---:|---|
| quikspec | 5,083 | MPOLICY, VANISH, VANISHDT, RESSTATE, RESRVCAT, SOR_POL |

## Verdict

PASS. Ready for Regression. Not Closed. The Issue 175 check is not in the always-on smoke list yet. That registration is part of Closure.
