# Issue 30 — Validation Report

**Issue:** 30 — Policies with Missing Owner/Insured Names  
**Framework stage:** Validation Agent  
**Status:** Awaiting Full Batch Rerun  
**Engine version:** v57.51  
**Date:** 2026-07-05  

---

## Validation Commands Run

| Command | Result |
|---|---|
| `python -m py_compile QLA_Migration\app.py app.py` | PASS |
| `python -m py_compile tools\validators\validate_issue30_relationship_names.py` | PASS |
| Targeted helper check: `039010150910` derives to `010150910C` | PASS |
| Targeted dedupe check: duplicate `quikclid` row removed | PASS |
| `python tools\validators\validate_issue30_relationship_names.py` against current output | FAIL as expected — output predates v57.51 |

---

## Current Output Baseline

The validator confirms current output still reflects the pre-fix condition:

- `010150910C` RNA source expects `OWNR`, `INSD`, and `PAYR` for `MCLIENTID=590268`.
- Current `quikclid` is missing those rows.
- Current `quikclnt` is missing `MCLIENTID=590268`.
- Current `quikmstr` still has blank `MPRIMID`, `MOWNRID`, and `MPAYRID`.
- Current `quikclid` contains 20,770 duplicate exact relationship rows.

This is expected until a full batch rerun writes v57.51 outputs.

---

## Required Post-Batch Pass Criteria

After running full batch migration from the GUI with v57.51:

1. Run `python tools\validators\validate_issue30_relationship_names.py`.
2. Expected result: PASS.
3. Confirm trace policy `010150910C` emits:
   - `quikclid`: `INSD/590268`, `OWNR/590268`, `PAYR/590268`
   - `quikclnt`: `590268` / `HAROLD SWANSON`
   - `quikmstr`: `MPRIMID=590268`, `MOWNRID=590268`, `MPAYRID=590268`
4. Confirm duplicate exact `quikclid` row count is zero.

---

## Validation Decision

**G5 — Validation pass:** PENDING

Code-level validation passed. Output-level validation requires the GUI full batch rerun because no headless batch runner exists; `QLA_Migration/run_converter.bat` launches the UI and instructs the operator to execute full batch migration.
