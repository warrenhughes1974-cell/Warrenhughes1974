# Issue 30 — Regression Report

**Issue:** 30 — Policies with Missing Owner/Insured Names  
**Framework stage:** Regression Agent  
**Status:** Partial PASS — Awaiting Post-Batch Issue 30 Validation  
**Engine version:** v57.51  
**Date:** 2026-07-05  

---

## Regression Commands Run

| Command | Result |
|---|---|
| `python tools\validators\validate_mpolicy_width.py` | PASS |
| `python tools\validators\validate_issue21d_blank_names.py` | PASS |
| `python tools\validators\validate_issue26_mprem.py` | PASS |

---

## Preserved Behavior

| Prior fix / area | Result |
|---|---|
| Issue 25 MPOLICY fixed-width formatting | PASS — 279,538 MPOLICY fields checked, 0 short, 0 long |
| Issue 21D B1 quikclnt referential integrity | PASS — 0 `quikclid` IDs missing from `quikclnt` in current output |
| Issue 21D `MPRIMID='I'` guard | PASS — no `MPRIMID='I'` values |
| Issue 26 MPREM mapping | PASS — trace policies and source alignment pass |
| QLAdmin schema field ordering | No schema changes made |

---

## Remaining Regression Step

After the v57.51 full batch rerun, repeat:

1. `python tools\validators\validate_issue30_relationship_names.py`
2. `python tools\validators\validate_mpolicy_width.py`
3. `python tools\validators\validate_issue21d_blank_names.py`
4. `python tools\validators\validate_issue26_mprem.py`

---

## Regression Decision

**G6 — Regression pass:** PENDING

Static/code-level and baseline prior-fix regression checks pass. Final regression remains pending until the full batch rerun emits v57.51 outputs.
