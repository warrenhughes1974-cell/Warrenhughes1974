# Issue #167 — Intake Summary

**Issue:** #167 — Dividend Premium Payment
**Framework stage:** Intake Agent (G0)
**Status recommendation:** Intake Complete → Planning → Dependency Gate → Risk
**Generated:** 2026-09-09
**Owner:** Conversion
**Priority:** No Go — Eric: 9/1/2026 Reduce-Premium dividend missing on 9010397528C

---

## Client symptom (verbatim)

> For policy 9010397528C, the dividend does not appear to have been paid on the 9/1/2026 anniversary. The dividend option is for dividend to Reduce Premium. Note dividend is larger than annual premium with remaining dividend paid in cash.

## Symptom (normalized)

On **9010397528C**, QLAdmin does not show a **9/1/2026** anniversary dividend under Reduce Premium (excess to cash). Discovery found LifePRO’s 8/31 extract never posted that 2026 dividend. Conversion already has the option (`MDIVOPT=2`) and the 9/1/2025 history. `quikridr.MLASTANN` is **55** from year-only math, so QLAdmin treats 9/1/2026 as already processed and will not generate the dividend.

## Example policies

| Policy | Role |
|---|---|
| **9010397528C** | Client gold. Issue 19710901. Active. `MLASTANN` 55 → **54**. `MDIVOPT=2`, `EXCESS_DIVIDEND=1`. |
| 9010412641C | Same option + excess-to-cash. Issue 19720401. `MLASTANN` already 54 on 8/31 — **control, no duration change**. |
| 9010367704C | Active, issue 19700701. Anniversary already passed by 8/31. `MLASTANN` 56 stays **56**. |
| 9010149295C / 9010374099C | ETI phase 1. `MLASTANN` from paid-to (#76/#108B). Must **not** be rewritten from issue date. |

## Suspected domain

Rider duration / anniversary processing — `quikridr.MLASTANN`. Calculator: `_compute_quikridr_mlastann` in both `app.py` copies. Not a missing `quikbenh` 20260901 row and not a wrong `MDIVOPT`.

## In scope (first pass)

- Anniversary-accurate `MLASTANN` for non-ETI/RPU `quikridr` rows: completed years from `MEFFDATE` (PPBEN `ISSUE_DATE`) to `QLA_VALUATION_DATE`, subtracting 1 if month/day has not occurred (same formula #108B already uses on NFO paid-to).
- Leave `_apply_issue76_eti_rpu_phase1_payup_mlastann` untouched.
- Fail-closed validator: gold **9010397528C** phase 1 = 54 on an 8/31 valuation; ETI/RPU phase-1 still matches #76; July-anniversary Active control unchanged.
- Publish `Output/Test_Validation/quikridr.csv` on PASS.

## Out of scope (first pass)

- Fabricating a 9/1/2026 `quikbenh` / `quikdvpr` row from the 8/31 PACTG extract (no such posting exists).
- Mapping LifePRO `EXCESS_DIVIDEND` (only 2 BA policies; QLAdmin target not confirmed).
- Cleaning the 9/1/2025 `quikbenh` type-1 $93.29 vs true $33.29 excess-cash leg.
- Changing `MDIVOPT`, `MPAIDTO`, `MMODEPREM`, `MPREM`, MPOLICY padding, QuikIswl `MLASTANNV`, or rate tables.

## Related issues

| Issue | Relationship |
|---|---|
| **#76 / #108B** | Same duration bug, already fixed for ETI/RPU phase 1 only. Preserve that overlay. |
| **#110** | `MDIVOPT` already 2 on the gold. Do not remap. |
| **#114 / #117** | Dividend history. Do not invent 20260901. Preserve MBENTYP 8/10/11/12. |
| **#60** | PUA inherits base `MEFFDATE`; PUA `MLASTANN` follows the shared calculator. |
| **#124** | `MLASTANNV` is issue **date**, not duration. Unrelated. |

## Immediate blockers

None. Source issue date and valuation date are already in the batch path. No new extract required.

## Artifact inventory

| Have | Missing |
|---|---|
| Current `quikridr.csv` / `quikmstr.csv` / `quikbenh.csv` | Post-9/1 LifePRO extract (not required if QLAdmin generates the 2026 dividend) |
| PPBEN `ISSUE_DATE`, PPBENTYP `DIVIDEND` / `EXCESS_DIVIDEND`, PACTG 8/31 | QLAdmin Help page for excess-dividend-to-cash (out of scope this pass) |
| Discovery notes | Screenshots from Eric (nice-to-have; before-state is measurable from Output) |

## Owner / priority

Conversion. Client priority **No Go**. No client data request for the duration fix.
