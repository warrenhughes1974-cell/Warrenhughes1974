# Issue 71 — Resolution Summary

**Issue:** #71 — BAND standardize to `00`  
**Framework stage:** Closure Agent  
**Final status:** **Closed**  
**Engine version:** v57.90  
**Closed date:** 2026-07-14  
**Owner:** Conversion + Client UAT

---

## Resolution (issue log — paste-ready)

**Resolution:** All rate factor and rate-key BAND values (and QuikPlBd BDCODE) now emit as `00` (NOT APPLICABLE) to match quikridr MBAND=00, restoring Policy Display cash-value lookup.

> Copy the line above into tracking sheets and client readouts. Long-form detail follows.

---

## Problem Statement

Policy Display showed **zero cash values** on otherwise valid policies (e.g. **`010718309C`** / plan **`1658C1`**) even though stored **`MCV0`** was populated (~986). Chris confirmed policy band **`MBAND=00`** (NOT APPLICABLE) is correct; rate tables were emitting **`BAND=01`**, so QLAdmin could not match policy to rate keys.

---

## Root Cause

**Category:** Mapping / emit alignment

LifePRO source bands 1/2/3 were mapped to QLAdmin `01`/`02`/`03` via `map_band()` while the rulebook and fleet already standardized **`quikridr.MBAND=00`**. Rate lookup requires policy band and rate-key band to align.

---

## Resolution (long-form)

v57.90 collapses all LifePRO bands to **`00`** at rate emit via centralized `map_band()`. QuikGps/QuikPlGp multi-band rows dedupe on collapse, keeping former band **`01`** content (SD-71-5). Rates regenerated to `Output/rates/` and published to `Test_Validation/rates/`. Client UAT confirmed CV display restored (“back in business”).

### Files changed

| File | Change |
|------|--------|
| `qla_core/rate_dbf_schema.py` | `map_band()` → `00`; `band_collapse_priority()` |
| `qla_core/rate_factor_loader.py` | GP dedupe; `source_band_raw` on transforms |
| `qla_core/pdage_missfill.py` | `source_band_raw` |
| `qla_core/cv_inheritance_loader.py` | `source_band_raw` |
| `qla_core/paagerat_pr_loader.py` | `source_band_raw` |
| `qla_core/rate_inheritance_loader.py` | `source_band_raw` |
| `qla_core/shared_rate_candidate_loader.py` | `source_band_raw` |
| `qla_core/paagerat_ul_coi_loader.py` | `source_band_raw` |
| `qla_core/quikissc_loader.py` | Fallback band `00` |
| `app.py`, `QLA_Migration/app.py` | `APP_VERSION` → **v57.90** |
| `Issue_Log_Items/Issue_71/scripts/validate_issue71_band.py` | Issue validator (new) |

### Rulebook changes

| Rulebook | Before | After |
|----------|--------|-------|
| `Sync_Rulebook_quikridr.csv` MBAND | `00` | **Unchanged** (already correct) |

No rulebook edit required — fix was rate emit only.

### Engine changes

- Centralized `map_band()` collapse to `00`
- Band-collapse collision resolution in `build_factor_grid()` (prefer ex-`01`)
- Rate re-emit only; no policy-table converter changes

---

## Evidence

| Artifact | Path |
|----------|------|
| Intake | `Issue_Log_Items/Issue_71/Issue_71_Intake_Summary.md` |
| Planning | `Issue_Log_Items/Issue_71/Issue_71_Planning_Report.md` |
| Dependency Gate | `Issue_Log_Items/Issue_71/Issue_71_Dependency_Gate.md` |
| Risk review | `Issue_Log_Items/Issue_71/Issue_71_Risk_Review_Report.md` |
| Implementation | `Issue_Log_Items/Issue_71/Issue_71_Implementation_Notes.md` |
| Validation report | **PASS** — `Issue_Log_Items/Issue_71/Issue_71_Validation_Report.md` |
| Regression report | **PASS** — `Issue_Log_Items/Issue_71/Issue_71_Regression_Report.md` |
| Validation script | `Issue_Log_Items/Issue_71/scripts/validate_issue71_band.py` |

---

## Trace Policy Confirmation

| Policy | Plan | Check | Expected | Actual | Match |
|--------|------|-------|----------|--------|-------|
| 010718309C | 1658C1 | MBAND | `00` | `00` | Yes |
| 010718309C | 1658C1 | QuikPlCv BAND | `00` | `00` | Yes |
| 010718309C | 1658C1 | MCV0 | ~986 | 986.03 | Yes |
| 010718309C | 1658C1 | Policy Display CV | Non-zero | Client UAT PASS | Yes |
| 010713704C | 1659C2 | MBAND / PlCv BAND | `00` | `00` | Yes |
| 015000057C | 17CSI5 | MBAND / PlCv BAND | `00` | `00` | Yes |
| 5L01MA | — | QuikPlGp BAND | `00` | `00` | Yes |

---

## Explicitly Not Changed

- quikridr / quikplan / quikmstr / quikprmh row counts and non-band fields
- **MCV0** stored amounts
- **NFOINT** on quikplan (Issue #60 Track B still open for CRVM blanks)
- **LOANINTX** (Issue #70 — 141/141 = `A`)
- Issue #25 MPOLICY 10-char padding
- Issue #26 MPREM / MMODPREM mapping
- quikridr MBAND (not flipped to `01`)

---

## Fleet Impact

| Metric | Value |
|--------|------:|
| QuikCvs BAND cells remapped | 38,047 → `00` |
| QuikGps rows after dedupe | 415 |
| Policy table rows changed | 0 |

---

## Production Readiness + Git Release (G7)

| Check | Status |
|-------|--------|
| Validators PASS (G5 + G6) | **Yes** |
| `app.py` version bumped | **v57.90** (both app.py files) |
| Issue-scoped git commit | Pending — see below |
| **`git push` to remote** | Pending — see below |
| Network batch note | **`Output/` gitignored** — after pull: run **GENERATE RATE TABLES** (or `QLA_Migration/_emit_all_rate_csvs.py`), reload `Test_Validation/rates/` into QLAdmin Data Admin |

---

## Client UAT

| Item | Status |
|------|--------|
| Policy Display CV on `010718309C` | **PASS** — client confirmed restored |
| Rate reload `Test_Validation/rates/` | **PASS** |

---

## Residual Risks / Follow-ups

| Item | Owner | Notes |
|------|-------|-------|
| Issue #60 Track B — blank NFOINT CRVM plans | CSO / Conversion | Separate from #71; still blocks CV $ on those plans |
| Issue #60 golden YE sample | Conversion | Pre-existing YE fail; not introduced by #71 |
| GP multi-band UAT depth | Client | Spot-check `5L01MA` peers if GP products in scope |

---

## Rollback

1. Revert v57.90 commit (restore `map_band()` 1→01/2→02/3→03 and remove band-collapse dedupe)
2. Re-run rate emit: `python QLA_Migration/_emit_all_rate_csvs.py`
3. Reload prior rate CSVs into QLAdmin Data Admin
4. Confirm `validate_issue71_band.py` fails (BAND=`01`) on rolled-back rates

---

## Issue Log Entry (paste-ready)

> **Issue #71 — BAND standardize to `00` — CLOSED (2026-07-14).**  
> **Resolution:** All rate factor and rate-key BAND values (and QuikPlBd BDCODE) now emit as `00` (NOT APPLICABLE) to match quikridr MBAND=00, restoring Policy Display cash-value lookup.  
> **Evidence:** Validation and regression PASS; trace policies 010718309C, 010713704C, 015000057C confirmed; client UAT PASS. **Preserved:** MPOLICY padding (#25), MPREM mapping (#26), LOANINTX (#70), MCV0 amounts, NFOINT. **Follow-ups:** Issue #60 Track B NFOINT for CRVM plans (separate).

---

## Framework Checklist

- [x] Intake
- [x] Planning
- [x] Dependency Gate PASS
- [x] Risk Conditional Go
- [x] Development (v57.90)
- [x] Validation PASS
- [x] Regression PASS
- [x] Client UAT PASS
- [x] Closure — **`Resolution:`** one-line + long-form summary
- [ ] Git commit + push (G7 release gate) — next step below
