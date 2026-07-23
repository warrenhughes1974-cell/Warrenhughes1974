# Issue #98 — Resolution Summary

**Issue:** #98 — CV Endpoint Off By One (`010398471C` / `17085M`)  
**Framework stage:** Closure Agent (G7)  
**Final status:** **Closed ✓**  
**Engine version:** v58.27  
**Closed date:** 2026-07-22  
**Owner:** Conversion (Warren)

---

## Resolution (issue log — paste-ready)

**Resolution:** GL85 CV duration placement now starts `.06` in year 3 for male issue ages 1–17 and keeps the age-100 terminal `1000` (Eric `010398471C` / `17085M` M age 14).

> Copy the line above into tracking sheets and client readouts. Long-form detail follows.

---

## Problem Statement

Eric reported CV factors for policy `010398471C` (`17085M`) were still off by one duration after Issue #41. LifePRO showed `.06` starting in year 3, year 85 = `975.61`, and year 86 = `1000`; QLAdmin had `.06` at duration 4 and truncated the terminal `1000`.

---

## Root Cause

**Category:** Mapping / duration remap

Issue #37’s `cv_lifepro_first_duration` matrix (960 PO–centric) over-shifted male ages 1–17 for GL85. Issue #41 correctly kept the age-100 endpoint (`return lp_d`) but did not correct this first-duration band.

---

## Resolution (long-form)

In v58.27, male ages 1–17 use first-duration **3**. Full rates package was re-emitted; `#98` anchors and `#41` `1960PO` regression both PASS.

### Files changed

| File | Change |
|------|--------|
| `qla_core/rate_factor_loader.py` | M 1–17 first-duration = 3 |
| `qla_core/rate_key_setup.py` / `rate_pipeline.py` | Durable `#96` `1SALMI` M/F keys (same rate release) |
| `qla_core/rate_dbf_writer.py` / `rate_emit.py` / `rate_loader_emit.py` | Manifest empty-member skip |
| `app.py` / `QLA_Migration/app.py` | v58.27 |
| `Issue_Log_Items/Issue_98/*` | Framework + validator |
| `tools/validators/validate_issue_log_accountability.py` | `#98` IN_DATA check |

### Rulebook changes

None.

---

## Evidence

| Artifact | Path | Result |
|----------|------|--------|
| Intake | `Issue_98_Intake_Summary.md` | — |
| Planning | `Issue_98_Planning_Report.md` | — |
| Dependency Gate | `Issue_98_Dependency_Gate.md` | PASS (Conditional) |
| Risk | `Issue_98_Risk_Review_Report.md` | CONDITIONAL GO |
| Implementation | `Issue_98_Implementation_Notes.md` | v58.27 |
| Validation | `Issue_98_Validation_Report.md` | **PASS** |
| Regression | `Issue_98_Regression_Report.md` | **PASS** |

### Output accountability gate (G7)

| Check | Evidence | Status |
|-------|----------|--------|
| Issue validator on full Output | `validate_issue98_quikcvs_endpoint.py` | **PASS** |
| Accountability | `validate_issue_log_accountability.py` → `#98` | **IN_DATA** |
| #41 regression spot-check | `1960PO` M/26 dur57=`784.65`, dur74=`1000.00` | **PASS** |
| Test_Validation | `Output/Test_Validation/rates/QuikCvs.csv` (+ PlCv/PlTv) | Published |

---

## Trace Policy Confirmation

| Policy / Plan | Expected | Emitted | Match |
|---------------|----------|---------|-------|
| `010398471C` / `17085M` M/14 | `.06` at dur 3 | `.06` | Yes |
| same | `975.61` at dur 85 | `975.61` | Yes |
| same | `1000` at dur 86 | `1000.00` | Yes |
| `1960PO` M/26 (#41) | `784.65` at dur 57; `1000` at dur 74 | same | Yes |

---

## Explicitly Not Changed

- Issue #41 age-100 endpoint rule (`return lp_d`)
- M 18–22 / M 24+ first-duration bands from #37
- Non-CV rate families (GP/DB/DV/TV formulas unchanged)
- `QuikAing` (documented separate scope)

---

## Residual risks / follow-ups

- After QLAdmin reload, run rate audit with `--qla-export` for post-load parity.
- `QuikAing` remains a separate follow-up if annuity interest grids are required in the enterprise package.

---

## Rollback

Revert v58.27 rate-loader changes and re-emit `Output/rates` from prior commit. `QLA_Migration/Output/` is gitignored — regenerate rates after any rollback pull.

---

## Git release

| Field | Value |
|-------|-------|
| Commit | `0b122984a68125558fd5c7f13f44814d8cba4cb7` |
| Branch | `issue-34-pr7-quikisrr` |
| Remote | `origin` |
