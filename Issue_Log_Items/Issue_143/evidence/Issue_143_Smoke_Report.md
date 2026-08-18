# Issue #143 — Final Release Smoke Report

**Generated:** 2026-08-18T13:48:36Z
**Overall:** **PASS**

A FAIL on any condition blocks final release sign-off.

| # | Condition | Result | Detail |
|---|-----------|--------|--------|
| 1 | 23 authorized BF RPU still have corrected MUNIT | **PASS** | candidates=23 corrected=23 missing=[] |
| 2 | Gold 9010757606C MUNIT=19.10196 MVPU=1000 Amount Ins=19101.96 | **PASS** | MUNIT=19.10196 MVPU=1000.00 AmountIns=19101.96 |
| 3 | 23 rows MUNIT×MVPU = BF_CURRENT_DB / Column DD | **PASS** | fails=0 |
| 4 | 82 aligned BF RPU unchanged | **PASS** | aligned=82 unchanged=82 fail=[] |
| 5 | 199 BA RPU receive no #143 remap | **PASS** | ba_source=199 present_unchanged=184 remapped=[] |
| 6 | MPREM / MVPU / MSAVEUNIT / MPOLICY unaffected | **PASS** | fails=0 |
| 7 | Issue #55 and #108A protections pass | **PASS** | floor=0 traces=True validate_issue55=0 msave_fail=[] |
| 8 | After authorized #124 reseed, MDB = corrected MUNIT×1000 | **PASS** | gold_stored=19101.96 gold_expected=19101.96 mismatches=0 |
| 9 | No unauthorized MUNIT changes outside the 23 | **PASS** | unauthorized=[] authorized_corrected=23 |

**Issue #143 Smoke: PASS**

Command: `python tools/validators/validate_issue143_smoke.py`
Also run via: `python tools/validators/validate_release_closed_issues.py --smoke-only`

