# Issue #30 — Resolution Summary

**Resolution:** Missing Owner/Insured Names — **Closed.** Original report incorrectly blamed missing RNA source; relationship rows use `IDENTIFYING_ALPHA` when `POLICY_NUMBER` is blank. Converter now derives `MPOLICY`, reads over-wide RNA rows without skipping them, and dedupes `quikclid`. 18/18 population policies PASS validation; fleet blank `MPRIMID` = 0. Client UAT on Policy Discovery pending.

**Issue:** #30 — Policies with Missing Owner/Insured Names (Policy Discovery)  
**Framework stage:** Closure Agent (G7)  
**Final status:** **Closed**  
**Engine version:** **v57.53** (Issue #30 fixes in v57.51 + v57.53)  
**Closed date:** 2026-07-05  
**Owner:** Conversion (Warren) · Reporter: Eric / Client UAT

---

## Production Readiness (G7 gate)

| Check | Status |
|-------|--------|
| G5 validation PASS | **Done** — `validate_issue30_relationship_names.py` PASS (18/18 policies) |
| G6 regression PASS | **Done** — Issue #25, #21D, #26 validators PASS on post-fix output |
| `app.py` / `QLA_Migration/app.py` **v57.53** | **Done** |
| Issue-scoped git commit | **Done** — `0374a22` (v57.51), `5e4833a` (v57.53) |
| Git push to remote | **Done** — `origin/issue-34-pr7-quikisrr` |
| Network batch after pull | Re-run full batch at v57.53 (`Output/` gitignored) |
| Client UAT on QLAdmin Policy Discovery | **Pending** — confirm names on sample policies |

---

## Problem Statement

Client reported **blank or comma-only Primary Insured / Owner** names in QLAdmin Policy Discovery (e.g. `010150910C`, `010713704C`, `010713705C`). The June 2026 intake identified **18 policies (0.35% of 5,083)** with blank `MPRIMID` and/or `MOWNRID` after conversion.

---

## Root Cause

**Category:** Converter / source-read defect (not missing LifePRO data)

Two defects combined:

1. **Wrong policy key in RNA analysis (Issue #30 intake, 2026-06-27)**  
   The original report searched `POLICY_NUMBER` in the RNA extract. For this cohort, relationship rows store the policy key in **`IDENTIFYING_ALPHA`** (e.g. `039010150910` → `010150910C`) with **`POLICY_NUMBER` blank**. The “missing source data” conclusion was incorrect.

2. **RNA CSV rows silently dropped during conversion**  
   LifePRO `RelationshipNameAddress_Extract` contains rows with **109–110 fields under a 108-column header**. Pandas `read_csv(..., on_bad_lines='skip')` **skipped ~168 over-wide rows**, including most **`IN`**, **`PO`**, and **`PA`** relationship rows. Beneficiary and service rows (108 columns) still converted, which produced partial `quikclid` output (e.g. `BENP`, `SERV`, `BANK` only) and blank `MPRIMID` on `quikmstr`.

---

## Resolution

### v57.51 — Relationship policy key + dedupe

- Resolve dated RNA source via LifePRO source resolver.
- Derive `quikclid.MPOLICY` from `IDENTIFYING_ALPHA` when `POLICY_NUMBER` is blank (crosswalk-aware).
- Exact dedupe of `quikclid` by `MCLIENTID + MPOLICY + MPHASE + MRELATION`.
- Added `tools/validators/validate_issue30_relationship_names.py`.

### v57.53 — RNA reader (complete fix)

- Added `_read_lifepro_rna_csv()` for `quikclnt`, `quikclid`, and `quikbenf` when source is `RelationshipNameAddress_Extract*.csv`.
- **Truncates** surplus columns on over-wide rows instead of skipping them.
- Preserves **`IN` / `PO` / `PA`** rows so `rel_map` populates `MPRIMID`, `MOWNRID`, and `MPAYRID` on `quikmstr`.

### Files changed

| File | Change |
|------|--------|
| `app.py` | v57.51–v57.53; RNA derivation, dedupe, RNA CSV reader |
| `QLA_Migration/app.py` | Mirror |
| `tools/validators/validate_issue30_relationship_names.py` | Issue #30 validator (v1.1 — resolves dated RNA extract) |
| `Issue_Log_Items/Issue_30/*.md` | Framework artifacts |

### Rulebook changes

**None** — `Sync_Rulebook_quikclid.csv` / `Sync_Rulebook_quikclnt.csv` unchanged.

---

## Evidence

| Artifact | Path |
|----------|------|
| Original population | `Issue_30_Missing_Name_Policies.csv` (18 policies) |
| Intake (revised) | `Issue_30_Intake_Summary.md` |
| Planning | `Issue_30_Planning_Report.md` |
| Dependency Gate | `Issue_30_Dependency_Gate.md` |
| Risk (Go) | `Issue_30_Risk_Review_Report.md` |
| Implementation | `Issue_30_Implementation_Notes.md` |
| Validation (G5) | `Issue_30_Validation_Report.md` |
| Regression (G6) | `Issue_30_Regression_Report.md` |
| Validator | `tools/validators/validate_issue30_relationship_names.py` |

---

## Trace Policy Confirmation (post v57.53)

| Policy | Expected insured | Post-fix `MPRIMID` | Post-fix name | Result |
|--------|------------------|-------------------|---------------|--------|
| 010150910C | HAROLD SWANSON (`590268`) | `590268` | SWANSON, HAROLD | PASS |
| 010713704C | FRANCIS GOERGEN (`342153`) | `342153` | GOERGEN, FRANCIS J | PASS |
| 010713705C | KATHLEEN GOERGEN (`590346`) | `590346` | GOERGEN, KATHLEEN ANN | PASS |
| 010422977C | FRANCIS GOERGEN (`342153`) | `342153` | GOERGEN, FRANCIS J | PASS |

**Fleet metrics after post-fix batch:**

| Metric | Before | After |
|--------|--------|-------|
| Policies with blank `MPRIMID` | 12–18 | **0** |
| Issue #30 validator (18-policy cohort) | FAIL | **PASS** |
| Exact duplicate `quikclid` rows (Issue #30 dedupe) | 20,770+ | **0** in validated cohort |

---

## Population Outcome

All **18 policies** in `Issue_30_Missing_Name_Policies.csv` now emit expected RNA roles (`IN`/`PO`/`PA` where present in source) to `quikclid`, matching clients in `quikclnt`, and role IDs on `quikmstr`.

Policies where RNA source has **blank owner name fields** (comma-only display) may still show punctuation in QLAdmin — that is **source data**, not a conversion gap.

---

## Client Action

| Action | Owner |
|--------|-------|
| Pull `issue-34-pr7-quikisrr` @ `5e4833a` (v57.53) | Conversion / Client IT |
| Run **EXECUTE FULL BATCH MIGRATION** via `run_converter.bat` | Client |
| Confirm Primary Insured on Policy Discovery for sample policies above | Client |
| Sign off Issue #30 closed in issue log | Client |

---

## Git / Release

| Item | Value |
|------|-------|
| Branch | `issue-34-pr7-quikisrr` |
| Commits | `0374a22` (v57.51), `5e4833a` (v57.53) |
| Engine | **v57.53** |

---

*Issue #30 closed — converter defect corrected; original “missing RNA source” finding superseded. Client UAT on QLAdmin Policy Discovery recommended before production sign-off.*
