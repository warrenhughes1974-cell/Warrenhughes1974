# Issue #83 — Resolution Summary

**Issue:** #83 — Fleet gender companion rate keys (F/M; Values=N)  
**Framework stage:** Closure Agent  
**Final status:** **Closed — Ready for Client UAT**  
**Release:** **v58.02** (`app.py` + `QLA_Migration/app.py`)  
**Closed date:** 2026-07-17  
**Owner:** Conversion

---

## Resolution (issue log — paste-ready)

**Resolution:** Rate setup now emits missing Female/Male companion keys fleet-wide when a plan declares both gender members but a GP/DB/CV/TV/DV family only had one sex key, without inventing factor values (QLAdmin Values=N on companions with no factors).

> Copy the line above into tracking sheets and client readouts. Long-form detail follows.

---

## Problem Statement

On QLAdmin Plan Rate File Options Keys, plans such as `221END` showed a Male Cash Value key (Values=Y) but no Female key, even though Plan Information already listed Gender members F and M. Issue #77 ensured each rate family had at least one key stub, but did not add the missing gender companion when only one sex had factor rates.

---

## Root Cause

**Category:** Rate setup / key completeness gap (scope)

1. `build_key_rows` derives keys only from factor grid segmentation — one sex with factors produced one key.  
2. `#77` default stubs added a single preferred-gender header when a whole family had no keys, not companions within a family that already had one gender.  
3. QuikPlGd already declared F+M on many plans from other families (e.g. TV), so QLAdmin expected both gender keys on CV/GP/DB/DV as well.

---

## Resolution (long-form)

### Behavior

| Area | Before | After |
|------|--------|-------|
| Gender keys on GP/DB/CV/TV/DV | Often one of F/M only | Both F+M when QuikPlGd has both and family has ≥1 F/M key |
| Companion with no factors | Missing key row | Key header present; QLAdmin **Values=N** |
| Companion assumptions | N/A | Same plan-level codes as sibling (#80 authority) |
| Factor grids | — | **Unchanged** (no invent) |
| quikplan PVO | GDVARY* often N on single-gender CV | GDVARYCV=Y where second gender key added (83 plans) |

### Fleet impact

| Metric | Value |
|--------|------:|
| Companion keys added (current Output apply) | **259** |
| Plans affected | **83** |
| QuikPlCv companions | **53** (includes `221END` F) |

### Files changed

| File | Change |
|------|--------|
| `qla_core/rate_key_setup.py` | `ensure_gender_companion_keys`, helpers |
| `qla_core/rate_pipeline.py` | Wire after member build, before `ensure_members_for_keys` |
| `app.py` / `QLA_Migration/app.py` | **v58.02** |
| `QLA_Migration/_apply_issue83_gender_companion_keys.py` | Apply to Output + Test_Validation |
| `QLA_Migration/_validate_issue83_gender_companion_keys.py` | Validator |
| `QLA_Migration/_research_issue83_gender_companion_keys.py` | Gap audit |
| `QLA_Migration/_print_issue83_uat_samples.py` | UAT sample checklist |
| `Issue_Log_Items/Issue_83/scripts/regression_issue83.py` | Regression |

### Rulebook changes

None.

---

## Evidence

| Artifact | Path |
|----------|------|
| Intake | `Issue_Log_Items/Issue_83/Issue_83_Intake_Summary.md` |
| Planning | `Issue_Log_Items/Issue_83/Issue_83_Planning_Report.md` |
| Dependency Gate | `Issue_Log_Items/Issue_83/Issue_83_Dependency_Gate.md` |
| Risk | Skipped — user approved Development after Dependency Gate PASS |
| Implementation | `Issue_Log_Items/Issue_83/Issue_83_Implementation_Notes.md` |
| Validation | **PASS** — `Issue_83_Validation_Report.md` |
| Regression | **PASS** — `Issue_83_Regression_Report.md` |
| Evidence | `Issue_Log_Items/Issue_83/evidence/` |

---

## Trace confirmation

| Plan | Expected | Result |
|------|----------|--------|
| `221END` QuikPlCv | F Values=N, M Values=Y; assumptions N1/N1/2/0 | **PASS** |
| `222END` QuikPlCv | Same END85 pattern | **PASS** |
| `1960PO` QuikPlCv | F+M both Values=Y (no regression) | **PASS** |
| `2665ST` QuikPlCv | M Values=Y, F companion Values=N | **PASS** |

---

## Explicitly not changed

- Factor cell values (QuikGps/Dbs/Cvs/Tvs/Dvs/Nps — no invent / no shrink on regression)  
- #25 MPOLICY padding, #26 MPREM mapping  
- #71 BAND=`00` on F/M keys  
- #80 Valuation_Setup assumption codes on existing keys (companions inherit sibling/plan authority)  
- Policy tables (quikmstr, quikridr, quikprmh, …)

---

## Client UAT

| Item | Status |
|------|--------|
| QLAdmin Plan Rate File Options Keys (`221END` Cash Values) | **Pending** |
| Reload package | `QLA_Migration/Output/Test_Validation/quikplan.csv` + `Test_Validation/rates/QuikPl*.csv` |
| Sample checklist | `python QLA_Migration/_print_issue83_uat_samples.py` |

**UAT anchors:** `221END`, `222END`, `2665ST`, `130JEB`, `1960PO`

---

## Residual / follow-up

| Item | Owner | Notes |
|------|-------|-------|
| UW companion keys (37 plans with multi-UW) | Future issue | Out of #83 scope (gender F/M only) |
| Client UAT sign-off | Client / CSO | Plan Information GDVARYCV may flip Y when second gender key added |
| Network machines after pull | Ops | Re-run GENERATE RATE TABLES or `_apply_issue83_gender_companion_keys.py` |

---

## Rollback

1. Revert v58.02 changes in `qla_core/rate_key_setup.py`, `rate_pipeline.py`, both `app.py` copies.  
2. Restore prior `Output/rates/QuikPl*.csv`, members, and `quikplan.csv` from backup.  
3. Re-run `python QLA_Migration/_validate_issue77_rate_setup.py` on restored package.

---

## Production readiness + git release (G7)

| Check | Status |
|-------|--------|
| Validators PASS (G5 + G6) | **Yes** |
| `app.py` version bumped | **v58.02** |
| Issue-scoped git commit | See below |
| `git push` to remote | **Pending user request** — `Output/` gitignored; push code then re-emit on network |

---

## Git release

| Item | Value |
|------|-------|
| Commit | `0637bf05b7077e5517da600653794064847e708c` |
| Branch | `issue-34-pr7-quikisrr` |
| Remote | *(not pushed — run `git push -u origin HEAD` for network rollout)* |

**Network note:** `QLA_Migration/Output/` is gitignored. After pull:

```powershell
python QLA_Migration/_apply_issue83_gender_companion_keys.py
# or GENERATE RATE TABLES in app at v58.02
```

Then load `Output/Test_Validation/` for partial UAT.

---

## Issue log entry (paste-ready)

> **Issue #83 — Fleet gender companion rate keys (F/M; Values=N) — CLOSED (2026-07-17).**  
> **Resolution:** Rate setup now emits missing Female/Male companion keys fleet-wide when a plan declares both gender members but a GP/DB/CV/TV/DV family only had one sex key, without inventing factor values (QLAdmin Values=N on companions with no factors).  
> **Evidence:** Validation and regression PASS; anchor `221END` QuikPlCv F=Values N, M=Values Y. **Preserved:** factor grids, #25/#26, #71 BAND, #80 assumptions. **Follow-ups:** Client UAT; UW companions parked.

---

## Framework checklist

- [x] Intake
- [x] Planning
- [x] Dependency Gate PASS
- [ ] Risk (waived — user approved Development after gate)
- [x] Development (v58.02)
- [x] Validation PASS
- [x] Regression PASS
- [x] Closure — Resolution summary published
- [x] Git commit (G7) — `0637bf05b7077e5517da600653794064847e708c`
- [ ] Git push (pending explicit user request)
