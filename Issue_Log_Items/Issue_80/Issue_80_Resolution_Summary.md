# Issue #80 — Resolution Summary

**Issue:** #80 — CSO Valuation Setup → exact QuikPlCv / QuikPlTv / quikplan assumptions  
**Framework stage:** Closure Agent (Composer 2.5)  
**Final status:** **Closed**  
**Release:** **v58.01** (`app.py` + `QLA_Migration/app.py`)  
**Closed date:** 2026-07-17  
**Owner:** Conversion / CSO actuarial authority

---

## Resolution (issue log — paste-ready)

**Resolution:** CSO Valuation_Setup is now the authoritative source for cash-value and reserve assumption codes on 51 non-PUA plans, writing exact QuikPlCv, QuikPlTv, and quikplan NFOINT/INTMETHCV values with blank workbook cells left blank.

> Copy the line above into tracking sheets and client readouts. Long-form detail follows.

---

## Problem Statement

Plan and rate key assumption fields (mortality, interest, reserve method, logical flags) for CSO products did not match the actuarial authority in `docs/Valuation_Setup.xlsx`. QuikPlTv reserve fields were largely blank, quikplan NFOINT/INTMETHCV relied on an older CSO mortality crosswalk, and values conflicted with the delivered valuation workbook.

---

## Root Cause

**Category:** Client definition / scope gap

1. Assumption codes were split across legacy `CSO_Mortiality_Crosswalk.csv` and incomplete rate-key emit — Valuation_Setup was not wired as authority.  
2. QuikPlTv reserve columns (RSVINT, RSVMETH, STOREMEANS, etc.) were deferred pending actuarial input.  
3. PUA and missing-QLA rows in the workbook required separate issues (#81, #82).

---

## Resolution (long-form)

### Behavior

| Area | Before | After |
|------|--------|-------|
| QuikPlCv assumptions (48 keyed plans) | Crosswalk / blank | Valuation_Setup exact codes |
| QuikPlTv assumptions | Mostly blank | Filled per workbook (51 plans on authority; 48 with keys) |
| quikplan NFOINT / INTMETHCV | Crosswalk | Valuation_Setup wins after crosswalk overlay |
| Blank workbook cell | Sometimes inherited | **Blank** — assumption does not apply |
| `221END` / `222END` ETIMORT | Uncoded | **`N1`** (1941 CSO) per SME lock |
| `10L171` / `10L172` / `117JPO` | — | quikplan only — **no** QuikPlCv/Tv keys |
| PUA plans | In workbook | **Out of scope** → #81 / #82 |

### Files changed

| File | Change |
|------|--------|
| `qla_core/cso_valuation_setup.py` | **New** — loader, providers, quikplan overlay |
| `qla_core/rate_pipeline.py` | CompositeAssumptionProvider; Valuation_Setup wins |
| `plan_analysis/source_data/rates/CSO_Valuation_Setup.csv` | **New** — 51-plan authority |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | `cso_valuation_setup` path |
| `app.py` / `QLA_Migration/app.py` | quikplan overlay; QA → Reports; **v58.01** |
| `QLA_Migration/_validate_issue80_valuation_setup.py` | Validator + package checks |
| `QLA_Migration/_apply_issue80_quikplan_overlay.py` | Headless quikplan helper |
| `QLA_Migration/_risk_review_issue80_valuation_setup.py` | Risk simulation |
| `tools/publish_test_validation.py` | `--clean` + `--rates` publish |
| `Issue_Log_Items/Issue_80/scripts/regression_issue80.py` | Regression checks |

### Rulebook changes

None.

---

## Evidence

| Artifact | Path |
|----------|------|
| Intake | `Issue_80_Intake_Summary.md` |
| Planning | `Issue_80_Planning_Report.md` |
| Dependency Gate | `Issue_80_Dependency_Gate.md` (G2 PASS) |
| Risk | `Issue_80_Risk_Review_Report.md` (Conditional Go) |
| Implementation | `Issue_80_Implementation_Notes.md` |
| Validation | **PASS** — `Issue_80_Validation_Report.md` |
| Regression | **PASS** — `Issue_80_Regression_Report.md` |
| Regression CSV | `evidence/issue80_regression_checks.csv` |
| Coded expected | `evidence/cso_valuation_setup_coded_expected.csv` |

---

## Trace confirmation

| Plan | Surface | Key values |
|------|---------|------------|
| `1960PO` | QuikPlCv / Tv / quikplan | NFOINT=`6`, ETIMORT=`Q1`, RSVINT=`6`, RSVMETH=`3` |
| `221END` | QuikPlCv / Tv | ETIMORT=`N1`, NFOINT=`2`, RSVINT=`2` |
| `1658C1` | QuikPlTv | RSVINT=`A`, RSVMETH=`3`, STOREMEANS=`N` |
| `17CSI3` | quikplan | NFOINT=`A` (was crosswalk `F`) |
| `10L171` | quikplan only | NFOINT=`A`; no rate keys |

---

## Explicitly not changed

- Factor grid cell values (Gps/Dbs/Cvs/Tvs/Dvs/Nps — no shrink)  
- Policy tables (quikmstr, quikridr, quikclid, quikclnt)  
- #25 MPOLICY padding, #26 MPREM mapping  
- #60 Track A PUA phase on quikridr  
- Citizens / CFIC conversion folders  
- PUA assumption writes (#82) and missing-QLA PUA rows (#81)

---

## Fleet impact

| Metric | Value |
|--------|------:|
| Plans on authority | 51 |
| Assumption cells validated | 1,248 |
| Non-candidate quikplan NFOINT/INTMETHCV drift | 0 |
| Intentional quikplan updates (candidates) | 36 cells |

---

## Production readiness + Git release (G7)

| Check | Status |
|-------|--------|
| Validators PASS (G5 + G6) | **Yes** |
| `app.py` v58.01 | **Yes** |
| Issue-scoped git commit | See below |
| Network batch note | `Output/` gitignored — after pull: GENERATE RATE TABLES + full batch v58.01, or overlay helper |

---

## Client UAT

| Item | Status |
|------|--------|
| Partial reload package | `Output/Test_Validation/quikplan.csv` + `rates/QuikPlCv.csv` + `rates/QuikPlTv.csv` |
| QLAdmin screen verification | **Pending** — anchor plans: `1960PO`, `221END`, `17CSI3`, `5646AT`, `10L171` |
| Client sign-off | Pending |

---

## Residual risks / follow-ups

| Item | Owner | Issue |
|------|-------|-------|
| PUA QuikPl* keys vs quikplan PA gap | CSO / Conversion | **#82** |
| Four PUA rows missing QLA Plan | CSO / Conversion | **#81** |
| Unrelated `FORM` NA→blank on 4 rider plans | Triage if needed | Outside #80 |
| Full QuikPlCv/Tv non-candidate baseline | N/A | Limited archive; quikplan targets proven stable |

---

## Rollback

1. Revert v58.00–v58.01 changes to `qla_core/cso_valuation_setup.py`, `rate_pipeline.py`, and both `app.py` files.  
2. Remove `cso_valuation_setup` from rate loader config.  
3. Restore prior `Output/quikplan.csv` and `Output/rates/QuikPlCv.csv` / `QuikPlTv.csv` from Archive.  
4. Re-run rate emit without Valuation_Setup provider.

---

## Git release

| Item | Value |
|------|-------|
| Commit | *(recorded after commit)* |
| Branch | `issue-34-pr7-quikisrr` |
| Message | `Close Issue #80: CSO Valuation Setup exact assumptions (v58.01)` |

**Network note:** After pull, run **GENERATE RATE TABLES** (or `rate_loader_gui_runner.py --emit-csv`) and full batch at v58.01. Load `Output/Test_Validation/` for partial UAT.

---

## Issue log entry (paste-ready)

> **Issue #80 — CSO Valuation Setup → exact QuikPlCv / QuikPlTv assumptions — CLOSED (2026-07-17).**  
> **Resolution:** CSO Valuation_Setup is now the authoritative source for cash-value and reserve assumption codes on 51 non-PUA plans, writing exact QuikPlCv, QuikPlTv, and quikplan NFOINT/INTMETHCV values with blank workbook cells left blank.  
> **Evidence:** Validation and regression PASS (1,248/1,248 cells); v58.01. **Preserved:** factor grids, policy tables, #25/#26, PUA out of scope. **Follow-ups:** #81 (missing QLA PUA), #82 (PUA QuikPl keys).

---

## Framework checklist

- [x] Intake  
- [x] Planning  
- [x] Dependency Gate PASS  
- [x] Risk Conditional Go  
- [x] Development (v58.00 → v58.01)  
- [x] Validation PASS  
- [x] Regression PASS  
- [x] Closure — Resolution summary published  
- [x] Git commit + push (G7)
