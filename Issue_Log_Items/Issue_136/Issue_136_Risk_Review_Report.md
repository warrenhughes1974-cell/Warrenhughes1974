# Issue #136 — Risk Review Report

**Issue ID:** #136  
**Framework stage:** Risk  
**Date:** 2026-08-02  
**Reviewer:** Conversion (Cursor Grok 4.5) + Luna concurrence on rule  
**Coding:** Not started — **awaiting Development approval**

---

## Go / No-Go

| Criterion | Result |
|-----------|--------|
| Business rule locked | **Go** |
| Scope clear / blast radius known | **Go** |
| Dependencies cleared or superseded | **Go** |
| Rollback path | **Go** — revert flag logic; restore archived Q DBFs / prior `quikplan.csv` |
| Residual risk acceptable | **Go** with Validation gates below |

**Overall: GO for Development — pending explicit Warren approval.**

---

## Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|------------|--------|------------|
| R1 | Clearing Band/State flags breaks a QLAdmin UI expectation that “any rate ⇒ Band checked” | Med | Med | UAT on 1658C1 + sample plans with real GP/CV/TV; Robert/Warren confirm Band NOT APPLICABLE with no checkboxes is correct |
| R2 | Softening Issue #96 leaves CV/TV unusable if `PLANVALOPT` incorrectly goes N while factors exist | Med | High | After change: any plan with real QuikCvs/QuikTvs and legitimate Gender/UW must keep `PLANVALOPT=Y`; add Validation assert |
| R3 | Gender/UW incorrectly cleared if “default” genders/`00` UW mishandled | Low | High | Keep multi-value rule; unit tests for 1658C1-like GP F/M × NS/PR/SM |
| R4 | Fleet plans that somehow had genuine multi-band/state get cleared wrongly | Low | Med | Enable when >1 distinct non-default (or multi) band/state in real factors; fleet scan before Closure |
| R5 | Issue #77 auditors / old docs confuse Validation | Med | Low | Document supersession; update validators that assert STVARYGP/BDVARY on presence |
| R6 | DBF redeploy to Q while QLAdmin open locks files | Low | Med | Close QLAdmin before redeploy; archive Q first (existing pattern) |

---

## Regression fence (must stay green)

- Default-only PUA plans: keys present, `PLANVALOPT=N`, all VARY N  
- GP variation preserved where real: e.g. `1658C1`, `1659C2`, `1659CR`, `1668SP` Gender/UW as supported by factors  
- DV plans with real QuikDvs: `BDVARYDV`/related only if DV grid truly varies; `PAR` rules unchanged  
- No blank-PLAN orphans; schema/order intact  
- Claims untouched  
- LOANINTX 137 A / 4 R unchanged  

---

## Validation gates before Closure

1. Unit tests for Band/State default-only + DV/DB absence  
2. Full Output validator / fleet scan vs locked criteria  
3. 1658C1 gold: Band N, DV N, State N; no DB without QuikDbs  
4. Publish `quikplan.csv` to Test_Validation; DBF Append → Q  
5. UAT screenshot re-check of Plan Values Options for 1658C1  

---

## Development approval request

Please reply **Approved for Development** (or equivalent) to implement #136 surgically in `quikplan_rate_variation_flags.py` (+ Issue #96 softener + tests), then Validation — no coding until then.

### Proposed Development scope (for approval)

1. Change `derive_plan_flags()` Band/State rules per locked criteria  
2. Stop Issue #96 from forcing Band (and Gender without multi-value)  
3. Ensure no DB/DV flags without real family factors  
4. Tests + rebatch + UAT redeploy of `quikplan` (rate tables unchanged unless Validation proves otherwise)