# Issue #112 — Issue validators stale after v58.29 / v58.32 / v58.33

**Track:** **Internal only** — not on the CSO / client issue log. See `Issue_112_Internal_Track.md`.

**Date:** 2026-07-25
**Status:** Partially resolved — key-format and superseded-behaviour half done; hardcoded
extract dates remain.

## Why this mattered

The G7 closure gate requires an issue validator PASS on full `QLA_Migration/Output/`. Six
validators were failing for reasons that had nothing to do with the conversion, which
blocked closure of 108A–108D, 108F and 110 even though the data was verified correct by
hand. These were validator defects, not conversion defects.

## Resolved

### Superseded behaviour

| Validator | Was asserting | Now asserts |
|---|---|---|
| `validate_issue72_mnfopt_status` v2.0 | the `MNFOPT` force Robert asked to remove (277 violations) | `MNFOPT` is **not** forced, and the emitted disagreements match `Reports/nfo_election_status_mismatch.csv` exactly — no silently forced rows, no phantom rows |
| `validate_issue76_eti_rpu_payup` v2.0 | calendar-year duration against the system clock (312 violations) | anniversary-accurate duration against the batch valuation date, resolved from `QLA_VALUATION_DATE` the same way `app.py` resolves it |
| `validate_issue60_pua_phase` v2.0 | PUA inherits base `MAGE`/`MLASTANN`/`MPHSTAT` on every row (81 violations) | inheritance on non-NFO bases; `MPHSTAT`=54 on NFO bases per #108D |

### Policy-key regression (Issue #2, v58.29)

`MPOLICY` went from 10 characters (strip leading 9, + `C`) to 11 (source + `C`). Trace
policies are recorded in the older form, so lookups silently returned nothing.

Added a `_canon` helper — drop a trailing `C` and a single leading `9` — to
`validate_issue57_mnfopt`, `validate_issue60_pua_phase`, `validate_issue72_mnfopt_status`,
`validate_issue76_eti_rpu_payup`, and to the spot-checks in
`validate_issue_log_accountability` via a `_PolicyIndex` lookup that resolves either
convention.

`validate_issue57_mnfopt` also stopped routing its source spot-check through
`Master_Crosswalk.csv`, which still holds pre-Issue-#2 `New_Value` keys.

### Two silent passes found while fixing this

Worth recording, because both had been reporting success without testing anything:

1. **Issue #60's baseline guard.** `quikridr_pre_v5785_baseline.csv` is keyed in the old
   format, so every baseline lookup missed and the loop `continue`d. The non-PUA and
   phase-1 regression guards had been vacuous since v58.29. They now run.
2. **The accountability spot-checks.** `#57`, `#59`, `#60`, `#49`, `#13` and `#58` were
   reporting GAP purely because their trace lookups missed. GAPs fell from 19 to 11 and
   `IN_DATA` rose from 25 to 36 with no conversion change.

### New validator

`validate_issue110_mdivopt.py` — `MDIVOPT` had no coverage at all. It rebuilds the expected
election from PPBENTYP rather than trusting the output, and reconciles 5,083 of 5,083.

### Registered in the accountability harness

`#72`, `#76` and `#110` were not being run at all. All three now appear and report
`IN_DATA`.

## Baseline drift handling

Turning Issue #60's guard back on exposed 6,916 differences against a v57.85 baseline that
predates fifteen releases. Rather than delete the guard or rubber-stamp the drift, fields
are split:

- **Hard** — `MEFFDATE`, `MAGE`, `MPHSTAT`, `MPAYUP`. Any movement fails. Currently **0**.
- **Valuation-sensitive** — `MLASTANN`, `MPREM`. Reported, and failed under
  `--strict-baseline`.

`MPREM` is compared numerically so `0.00` vs `0` is not counted (2,233 rows). `MLASTANN`
drift must be *uniform*: all 4,683 rows shift by exactly −1, which is the v57.86
configurable valuation date (2025-12-31) against a baseline computed on a 2026 system
clock. A scattered delta fails, so a real duration bug is still caught.

That the fields Issue #60 owns show zero drift is the useful result — it confirms the PUA
work never moved dates, ages or statuses on unrelated rows.

## Remaining

Several validators still hardcode a retired `_20260530` extract and error out:
`validate_issue21a_mnfopt`, `validate_issue26_mprem`, `validate_issue13_mstatus`,
`validate_issue21m_quikmemo`, `validate_issue38_mdeposit`, `validate_quikloan_issue32`,
`iswl_quikcvs_parity`.

The accountability harness classifies these as WARN (environmental), not GAP, so they do
not block closure. The fix is the newest-match resolution used in
`validate_issue110_mdivopt._find_ppbentyp`. Left for a separate pass to keep the blast
radius small — each one needs its own check that the newer extract has the columns it
expects.

## Files changed

```text
tools/validators/validate_issue57_mnfopt.py            v1.0 -> v1.1
tools/validators/validate_issue60_pua_phase.py         v1.0 -> v2.0
tools/validators/validate_issue72_mnfopt_status.py     v1.1 -> v2.0
tools/validators/validate_issue76_eti_rpu_payup.py     v1.0 -> v2.0
tools/validators/validate_issue110_mdivopt.py          new
tools/validators/validate_issue_log_accountability.py  _canon / _PolicyIndex; +#72 #76 #110
```

No production conversion code was touched.
