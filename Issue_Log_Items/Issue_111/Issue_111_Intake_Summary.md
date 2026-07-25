# Issue #111 — Intake Summary

**Issue:** #111 — PUA rider plans absent from `quikplan`; `MPAR` inherited rather than resolved
**Date:** 2026-07-25
**Framework stage:** Intake complete (G0)
**Status:** Open — Planning
**Owner:** Conversion (Warren) / product SME (Eric)
**Priority:** Medium
**Related:** #60 (PUA inheritance), #105 (MPAR authority), Issue A conversion checklist

---

## Symptom

`validate_issue105_mpar.py` reports 493 `quikridr` rows where the row's plan is not marked
participating in `quikplan` but `MPAR` is emitted as `1`. Every affected `MPLAN` is a PUA
rider plan (`1705PA`, `1708PA`, `1960PA`, `221EPA`, `2665PA`, `280EPA`).

## Root cause

Two behaviours combine.

1. **PUA plans do not exist in `quikplan`.** `_apply_pua_rider_inheritance` synthesises the
   PUA plan code as `base_mplan[:4] + "PA"`, but no corresponding row is emitted to
   `quikplan`. A lookup of `1705PA` against the product table therefore finds nothing.
   Note `quikplan` *does* carry unrelated `...PUA` codes (`121PUA`, `165PUA`, `170PUA`),
   so the naming is inconsistent as well.

2. **`MPAR` is resolved before the PUA rename.** Issue #105 sets `MPAR` from
   `quikplan.PAR` keyed on `MPLAN` at `app.py:7674`, inside the field loop, while `MPLAN` is
   still the base plan (e.g. `170588`, `PAR=1`). PUA rows are deferred to `pua_pending_rows`
   and renamed afterwards, so the row keeps `MPAR=1` under a plan code that resolves to
   nothing.

## Not caused by Issue #108

The v58.33 release does not touch either `MPAR` write site (`app.py:7674`, `app.py:8048`).
The pre-change baseline was written 2026-07-24 06:57 and the Issue #105 `MPAR` code was
committed 2026-07-24 11:56, so the baseline predates the feature. This is Issue #105 reaching
`Output/` for the first time.

## The question

`MPAR=1` on a paid-up addition attached to a participating base is very likely **correct**
business behaviour — a PUA on a par policy is itself par. If so, the defect is not the value
but the missing product rows: a plan code is being emitted on `quikridr` that has no
`quikplan` entry, which is exactly the orphan condition the Issue A checklist prohibits.

Three possible dispositions, to be decided at Planning with product input:

| Option | Effect |
|---|---|
| Emit PUA plans into `quikplan` with inherited `PAR` | Removes the orphan; `MPAR` resolves properly; largest blast radius |
| Resolve `MPAR` after the PUA rename, from the base plan explicitly | Makes the inheritance intentional rather than incidental; leaves the orphan |
| Accept and amend the validator | Cheapest; leaves a `quikridr` plan code with no product row |

## Affected tables

`quikridr.MPAR` (493 rows), and potentially `quikplan` if PUA plans are to be emitted.

## In scope

- Confirm with product whether PUA coverages should have their own `quikplan` rows
- Confirm the correct `MPAR` for a PUA on a participating base
- Decide between the three options and align `validate_issue105_mpar.py`

## Out of scope

- Issue #60's PUA date/age inheritance
- Issue #108 NFO work (#108D changes PUA `MPHSTAT` only)

## Immediate blockers

Needs a product decision before any code change. No conversion output is blocked in the
meantime — the current `MPAR` value is plausibly correct.

## Intake disposition

Open. Route to Eric/product for the participating question before Planning sizes a fix.
