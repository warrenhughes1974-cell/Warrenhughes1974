# Issue #28 — Regression Report

**Issue:** #28 — Incorrect Plan Number Mapping  
**Regression & Deployment date:** 2026-06-27  
**Engine version:** **v57.35**  
**Prior stages:** Intake ✅ | Planning ✅ | Dependency Gate ✅ | Risk ✅ | Development ✅ | Validation ✅ (PASS WITH OBSERVATIONS)  
**Mode:** Regression & Deployment only — no code modifications

---

## Final deployment decision

# **READY FOR CLIENT UAT**

Technical regression and deployment readiness are **confirmed**. Production release is **NOT READY** pending Client UAT (B-02) and rate team sign-off (V-16).

| Release tier | Decision |
|--------------|----------|
| Staging / UAT environment | **READY FOR CLIENT UAT** |
| Limited release (controlled policy set) | **READY FOR LIMITED RELEASE** |
| Production | **NOT READY** |

---

## 1. Regression baseline (v57.34 → v57.35)

Validated using snapshotted v57.34 output (`Issue_Log_Items/Issue_28/evidence/`) and fresh v57.35 batch output (`QLA_Migration/Output/`).

### Row counts — no regressions

| Table | v57.34 | v57.35 | Delta |
|-------|-------:|-------:|------:|
| quikplan.csv | 141 | 141 | 0 |
| quikridr.csv | 7002 | 7002 | 0 |
| quikmstr.csv | 5083 | 5083 | 0 |
| quikclid.csv | 46753 | 46753 | 0 |
| quikclnt.csv | 13846 | 13846 | 0 |
| quikprmh.csv | 205577 | 205577 | 0 |
| quikmemo.csv | 4380 | 4380 | 0 |

### Field-level changes — approved scope only

| Field | Changes | Expected | Status |
|-------|--------:|---------:|--------|
| quikplan.PLAN | **33** | 33 | ✅ |
| quikplan.FORM | 0 | 0 | ✅ |
| quikplan.DESCR | 0 | 0 | ✅ |
| quikridr.MPLAN | **262** | ~241+ (Risk est.) | ✅ |

Evidence: `Issue_Log_Items/Issue_28/evidence/v57.35_quikplan_plan_diff.csv`

### Runtime / catalog

| Check | Result |
|-------|--------|
| Batch exit code | 0 (no runtime errors) |
| Catalog governance = migration | Byte-identical (141 data rows) |
| New catalog inconsistencies | None |
| Unexpected PLAN changes | None |

---

## 2. Protected issue verification (reconfirmed 2026-06-27)

| Issue | Validator | Result | Deployment status |
|-------|-----------|--------|-------------------|
| **#25** MPOLICY width | `validate_mpolicy_width.py` | **PASS** | COMPATIBLE |
| **#26** MPREM | `validate_issue26_mprem.py` | **PASS** | COMPATIBLE |
| **#21M** QUIKMEMO | `validate_issue21m_quikmemo.py` | **PASS** | COMPATIBLE |
| **#21M-FU** DBF packaging | `validate_issue21m_dbf_packaging.py` | **PASS** | COMPATIBLE |
| **#21K** MUNIT | `validate_issue21k_munit.py` | **CSV PASS / DBF SKIP** | COMPATIBLE* |

*DBF reload requires `issue21k_units_migration.py --reload-quikridr` — optional for DBF UAT, not a deployment blocker for CSV-based UAT.

Issue #28 validator re-run: **PASS** (0 mismatches; client examples OK).

---

## 3. Deployment readiness summary

| Criterion | Status |
|-----------|--------|
| Version v57.35 consistent (`app.py`, `QLA_Migration/app.py`) | ✅ |
| Catalog synchronized | ✅ |
| Validator committed | ✅ |
| Release artifacts prepared | ✅ (this stage) |
| Rollback procedure complete | ✅ |
| Unresolved **technical** blockers | None |
| Unresolved **business** blockers | B-02 (Client UAT scope), V-16 (rate review) |

Detail: `Issue_28_Deployment_Readiness_Report.md`

---

## 4. Operational readiness

Operations has:

| Item | Location |
|------|----------|
| Deployment steps | `Issue_28_Deployment_Steps.md` |
| Rollback steps | `Issue_28_Rollback_Checklist.md` |
| Release checklist | `Issue_28_Release_Checklist.md` |
| Post-deploy validation commands | Deployment Steps § Step 4 |
| Env var documentation | `QLA_CLOSED_MPLAN_AUTHORITY=1` default ON |
| Known observations | Validation Report § Observations |
| Client communication | `Issue_28_Client_UAT_Package.md` |

---

## 5. Client UAT package

Prepared: `Issue_28_Client_UAT_Package.md`

Includes:

- Summary of corrected behavior (33 PLAN + DISCHO25)
- Three primary acceptance tests (1CSIMN, 960CWP, 94PDIS)
- Recommended spot-check scenarios
- Business impact (~219 policies)
- Acceptance criteria and fail actions

---

## 6. Release recommendation (with evidence)

| Recommendation | Supported by |
|----------------|--------------|
| **READY FOR CLIENT UAT** | 141/141 PLAN match; 33 exact corrections; protected issues PASS; batch exit 0; no output drift |
| **READY FOR LIMITED RELEASE** | Same technical evidence; deploy to controlled UAT/staging first |
| **NOT READY FOR PRODUCTION** | B-02 open; V-16 rate review pending; Client UAT not executed |

---

## Related deliverables (this stage)

| Artifact | File |
|----------|------|
| Regression report | `Issue_28_Regression_Report.md` (this file) |
| Deployment readiness | `Issue_28_Deployment_Readiness_Report.md` |
| Release checklist | `Issue_28_Release_Checklist.md` |
| Client UAT package | `Issue_28_Client_UAT_Package.md` |
| Deployment steps | `Issue_28_Deployment_Steps.md` |
| Final risk summary | `Issue_28_Final_Risk_Summary.md` |

Prior stage artifacts: `Issue_28_Validation_Report.md`, `Issue_28_Development_Report.md`, `Issue_Log_Items/Issue_28/evidence/`

---

## Stop condition

Regression & Deployment Agent **stops here**. Do not proceed to Client UAT execution, Closure, or Release Integration.

---

# Cursor Prompt — Client UAT Agent

You are continuing work on the **LifePRO → QLAdmin Conversion Project**.

**Current converter version:** **v57.35**

**Issue:** **Issue #28 — Incorrect Plan Number Mapping**

**Deployment recommendation:** **READY FOR CLIENT UAT** (Production: **NOT READY**)

The following stages have been completed:

* Intake Agent ✅
* Planning Agent ✅
* Dependency Gate ✅ (CONDITIONAL PASS)
* Ownership Decision ✅
* Risk Agent ✅ (CONDITIONAL GO)
* Development Agent ✅
* Validation Agent ✅ (PASS WITH OBSERVATIONS)
* **Regression & Deployment Agent ✅**

Do **not** repeat prior stages.

Begin **Client UAT Agent** only.

---

## Repository Governance

This repository follows the AI Issue Resolution Framework.

Client UAT is authorized for **staging/UAT environment** validation of v57.35 PLAN mapping corrections.

You may document UAT results and client feedback. Do **not** modify conversion code unless a UAT defect is proven and escalated through the framework.

Do **not** proceed to Closure or Release Integration until Client UAT PASS and production gates cleared.

---

## Required Reading

Review all Issue #28 artifacts:

```text
Issue_Log_Items/Issue_28/
```

**Regression & Deployment (required):**

* `Issue_28_Regression_Report.md` (this file)
* `Issue_28_Deployment_Readiness_Report.md`
* `Issue_28_Client_UAT_Package.md`
* `Issue_28_Deployment_Steps.md`
* `Issue_28_Release_Checklist.md`
* `Issue_28_Final_Risk_Summary.md`

**Validation (required):**

* `Issue_28_Validation_Report.md`
* `Issue_28_PLAN_Validation_Report.md`
* `Issue_28_MPLAN_Validation_Report.md`
* `Issue_28_Output_Delta_Report.md`

**Reference:**

* `Issue_28_PLAN_Comparison_Report.md` (33 transition table)
* `Issue_28_Rollback_Checklist.md`

**Evidence & output:**

```text
QLA_Migration/Output/quikplan.csv
QLA_Migration/Output/quikridr.csv
Issue_Log_Items/Issue_28/evidence/v57.35_quikplan_plan_diff.csv
```

---

## Summary of Regression & Deployment findings

### Technical readiness — APPROVED

| Check | Result |
|-------|--------|
| v57.34 → v57.35 row counts | No regressions (all tables unchanged) |
| quikplan PLAN changes | Exactly **33** (approved); FORM/DESCR unchanged |
| quikridr MPLAN changes | **262** (expected propagation) |
| Protected #25, #26, #21M, #21M-FU | **PASS** |
| Protected #21K | CSV PASS; DBF reload optional |
| Catalog sync | Byte-identical (141 data rows) |
| Batch | Exit 0 on v57.35 |

### Business gates — OPEN

| ID | Item | Blocks production |
|----|------|-------------------|
| **B-02** | Client written acceptance of re-UAT scope (33 PLAN changes) | **Yes** |
| **V-16** | Rate team review for changed PLAN codes | **Yes** |

---

## Client UAT objectives

Execute client-facing validation of v57.35 PLAN mapping corrections.

### Primary acceptance tests (mandatory)

| # | LifePRO source | Expected PLAN | Verify in |
|---|----------------|---------------|-----------|
| 1 | 10827 MN5K (CSI Life MN $5000) | **1CSIMN** | quikplan.csv |
| 2 | 0823 960CH (Waiver - Child) | **960CWP** | quikplan.csv + quikridr MPLAN (e.g. 010488878C) |
| 3 | 0824 P DIS (Payor Disability) | **94PDIS** | quikplan.csv + quikridr MPLAN (e.g. 010521756C) |
| 4 | DISCHO25 | **9DIS25** | quikplan.csv; confirm DISCHO247C → 9DS24C separate |

### Recommended spot checks

- 5 additional rows from the 33-mapping list (`Issue_28_PLAN_Comparison_Report.md`)
- Confirm a stable/unchanged product (e.g. 0823 960OL → 90OLWP) shows no drift
- PUA inheritance: 621 PUA→121PUA, 961 PUA→261PUA, 970 PUA→1970PA
- quikplan row count remains 141

---

## Required UAT evidence

Document and archive:

```text
Issue_Log_Items/Issue_28/
  Issue_28_Client_UAT_Report.md
  Issue_28_Client_UAT_Results.md
  Issue_28_Client_UAT_Signoff.md (or waiver documentation)
  evidence/client_uat/
    client_example_screenshots_or_csv_extracts/
    spot_check_worksheet.csv
```

For each primary test, capture:

- quikplan row (PLAN, FORM, DESCR)
- Sample quikridr MPLAN if rider product
- Client reviewer name/date/result (PASS/FAIL)

---

## Acceptance criteria

| Criterion | Required for UAT PASS |
|-----------|------------------------|
| 3 client examples PASS | **Yes** |
| DISCHO25 / DISCHO247C separation PASS | **Yes** |
| Spot sample (≥5 of 33 mappings) PASS | **Yes** |
| No unexpected PLAN changes beyond 33 | **Yes** |
| Client sign-off on re-UAT scope (B-02) | **Yes for production** |
| Rate team review (V-16) | **Yes for production** |

---

## UAT fail actions

| Fail type | Action |
|-----------|--------|
| Client example mismatch | **FAIL** — escalate; do not promote to production |
| Unexpected PLAN drift | Rollback per `Issue_28_Rollback_Checklist.md` |
| Client rejects scope | Hold production; document in UAT report |

---

## Protected issues (must remain unaffected)

During Client UAT, confirm no regression in:

* Issue #21M — QUIKMEMO (4380 rows, unique MEMOKEY)
* Issue #21M-FU — DBF packaging
* Issue #21K — MUNIT CSV precision
* Issue #25 — MPOLICY 10-char width
* Issue #26 — MPREM mapping

Validators available in `tools/validators/` if re-run needed.

---

## Known observations (communicate to client)

1. **33 PLAN codes change** in quikplan — internal QLAdmin codes corrected per Policy Form Crosswalk 5/22/2026.
2. **FORM and DESCR unchanged** — only PLAN field corrected.
3. **~262 quikridr MPLAN values** updated on rider policies — expected Phase 2 behavior.
4. **Some rider PLANs lack rate table entries** (94PDIS, 960CWP) — rate team review required before production; not a conversion defect.
5. **CSO crosswalk** may list corrected PLANs in missing_plan_codes — review `cso_mortality_crosswalk_qa.csv` if actuarial UAT in scope.

---

## Environment for Client UAT

Use validated v57.35 output from:

```text
QLA_Migration/Output/
```

Or re-run batch on UAT environment per `Issue_28_Deployment_Steps.md`.

Default env: `QLA_CLOSED_MPLAN_AUTHORITY=1` (P3E ON).

---

## Required Client UAT deliverables

Create in `Issue_Log_Items/Issue_28/`:

```text
Issue_28_Client_UAT_Report.md
Issue_28_Client_UAT_Results.md
Issue_28_Client_UAT_Signoff.md
Issue_28_Client_UAT_Checklist.md
```

End `Issue_28_Client_UAT_Report.md` with UAT decision:

```text
PASS
PASS WITH OBSERVATIONS
FAIL
```

---

## Explicit stop conditions

Stop Client UAT Agent after:

* Primary acceptance tests executed and documented
* Spot checks completed
* Client feedback captured (PASS/FAIL/waiver)
* UAT deliverables created
* Handoff prompt generated for Closure Agent (if UAT PASS)

Do **not** proceed to:

* Closure Agent (unless UAT PASS + explicit instruction)
* Release Integration Agent (unless production gates cleared)

---

## Mandatory handoff (Client UAT → Closure)

If UAT PASS, append to `Issue_28_Client_UAT_Report.md` under heading `# Cursor Prompt — Closure Agent` with full context for a new Cursor chat.

---

## Quick reference — corrected client examples

| LifePRO Coverage_ID | v57.34 (wrong) | v57.35 (correct) |
|---------------------|----------------|------------------|
| 10827 MN5K | 10827 MN5K | **1CSIMN** |
| 0823 960CH | 0823 960CH | **960CWP** |
| 0824 P DIS | 0824 P DIS | **94PDIS** |
| DISCHO25 | (missing) | **9DIS25** |

**Begin Client UAT now.**
