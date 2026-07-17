# Issue #77 — Resolution Summary

**Issue:** #77 — Fleet rate setup (Plan Values Options + default keys vs loaded rates)  
**Framework stage:** Closure Agent  
**Final status:** **Closed**  
**Release:** **v57.95** (`app.py` + `QLA_Migration/app.py`)  
**Closed date:** 2026-07-17  
**Owner:** Conversion  
**Model note:** Dev/Val/Reg/Closure completed on Cursor Grok 4.5 (user override of Composer 2.5 for #77)

---

## Resolution (issue log — paste-ready)

**Resolution:** Rate setup now ensures every plan with loaded rates has GP/DB/CV/TV/DV keys and correct Plan Values Options checkboxes, using NOT APPLICABLE defaults only when no real codes exist, without inventing factor values.

> Copy the line above into tracking sheets and client readouts. Long-form detail follows.

---

## Problem Statement

Plan Values Options and rate-key/member tables were incomplete or inconsistent with the rates we load. Many plans lacked keys for families with no factor rows; checkboxes did not match key participation (e.g. STVARYGP never Y); QuikPlSt.MLOANINT was blank; and default NOT APPLICABLE members (Gender `0`) were added beside real F/M codes, unlike `docs/EX_Rate_Tables`.

---

## Root Cause

**Category:** Rate setup / Plan Values Options derivation

1. Keys were emitted only where factor grids existed — missing families had no header key.  
2. R7 *VARY* used distinct-count > 1, so Band/State were often unchecked even when those dimensions are part of the key.  
3. Default stubs used Gender `0` / UW `00` even when the plan already had real codes (EX almost never does both).

---

## Resolution (long-form)

### Behavior

| Area | Before | After |
|------|--------|-------|
| Family keys | Only where factors exist | All 5 families for every rated plan (stub if no factors) |
| Stub segmentation | Always `0`/`00` | Prefer real F/M (etc.); NA only if none |
| Members | Could show `0` + F/M | NA pruned when real codes exist |
| Plan Values Options | Count>1 R7 | Band Y if family present; STVARYGP if GP; GD/UW if multi |
| QuikPlSt.MLOANINT | blank | `0.00` |
| Factor grids | — | **Unchanged** (no invent) |

### Files changed

| File | Change |
|------|--------|
| `qla_core/rate_key_setup.py` | Default stubs, preferred seg, NA repair |
| `qla_core/rate_member_setup.py` | MLOANINT `0.00`; prune NA when real exist |
| `qla_core/rate_pipeline.py` | Wire stubs + member sync |
| `qla_core/quikplan_rate_variation_flags.py` | Issue #77 PVO rule; CSV key scan |
| `app.py` / `QLA_Migration/app.py` | **v57.95** |
| `QLA_Migration/_apply_issue77_rate_setup.py` | Apply to Output |
| `QLA_Migration/_validate_issue77_rate_setup.py` | Validator |

### Rulebook changes

None.

---

## Evidence

| Artifact | Path |
|----------|------|
| Intake | `Issue_Log_Items/Issue_77/Issue_77_Intake_Summary.md` |
| Planning | `Issue_Log_Items/Issue_77/Issue_77_Planning_Report.md` |
| Dependency Gate | `Issue_Log_Items/Issue_77/Issue_77_Dependency_Gate.md` |
| Risk | `Issue_Log_Items/Issue_77/Issue_77_Risk_Review_Report.md` |
| Implementation | `Issue_Log_Items/Issue_77/Issue_77_Implementation_Notes.md` |
| Validation | **PASS** — `Issue_77_Validation_Report.md` |
| Regression | **PASS** — `Issue_77_Regression_Report.md` |
| Evidence CSVs | `Issue_Log_Items/Issue_77/evidence/` |

---

## Trace confirmation

| Plan | Result |
|------|--------|
| 1658CS | Db/Dv stub keys; F/M only; STVARYGP/BDVARYDB=Y; factors unchanged |
| 280PUA | No Gender `0`; Db stub uses F; PVO OK |

---

## Non-changes (preserved)

- Factor cell values (Gps/Dbs/Cvs/Tvs/Dvs/Nps row counts unchanged)  
- #25 MPOLICY padding, #26 MPREM  
- #71 BAND=`00`, #73 ISSCNTRY=`0000`  
- QuikPlTv RSVINT / interest assumptions (#60 Track B)  
- Policy tables (quikmstr / quikridr)

---

## Residual / follow-up

| Item | Owner |
|------|--------|
| Client UAT: reload `Output/Test_Validation/quikplan.csv` + `rates/QuikPl*` | Client / CSO |
| QuikPlTv assumption codes still blank | #60 Track B / CSO |
| Network machines: pull commit, re-run GENERATE RATE TABLES or `_apply_issue77_rate_setup.py` | Ops |

---

## Rollback

1. Revert v57.94–v57.95 `qla_core` + `app.py` changes.  
2. Restore prior `Output/rates/QuikPl*.csv`, members, and `quikplan.csv`.  

---

## Git release

| Item | Value |
|------|-------|
| Commit | `ca8221b9f66fadf8cc2d6168f40fa09c04175a4f` |
| Branch | `issue-34-pr7-quikisrr` |
| Remote | `origin/issue-34-pr7-quikisrr` |
| Message | `Close Issue #77: fleet rate setup PVO + default keys (v57.95)` |

**Network note:** `QLA_Migration/Output/` is gitignored — after pull, run GENERATE RATE TABLES or `python QLA_Migration/_apply_issue77_rate_setup.py`, then load `Output/Test_Validation/`.
