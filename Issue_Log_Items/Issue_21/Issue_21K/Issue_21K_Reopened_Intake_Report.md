# Issue #21K — Reopened Intake Report

**Issue ID:** 21K  
**Title:** PUA Amount Precision  
**Status:** Reopened / No-Go  
**Framework stage:** Reopened Intake  
**Generated:** 2026-06-28  
**Engine version:** v57.39  
**Code changes:** None (investigation only)

---

## 1. Reopen Trigger

Issue #21K was previously marked **implemented** with remediation path:

- Widen `MUNIT` from `N(*,3)` → `N(*,5)` on six QLAdmin tables
- Reload `QUIKRIDR` from conversion CSV

Client reports field sizes have **reportedly been increased**, but policy **`010448806C`** PUA Amount Insured still does not match LifePRO.

| Observation | Prior (intake) | Current (reopened) |
|-------------|---------------:|-------------------:|
| LifePRO PUA face | **$5,752.96** | **$5,752.96** (unchanged) |
| QLAdmin display | **$5,752.00** | **$5,753.00** |
| Implied failure mode | 3 dp **truncate** (5.75296 → 5.752) | 3 dp **round** or whole-dollar **round** |

**Symptom change is significant:** `$5,753.00` matches `round(5.75296, 3) × 1000 = 5.753 × 1000` or `round(5752.96) = 5753`, **not** truncate-to-3dp (`$5,752.00`).

---

## 2. Scope

| In scope | Out of scope |
|----------|--------------|
| End-to-end trace for `010448806C` | Converter code changes |
| v57.39 CSV / staging DBF verification | Rulebook / crosswalk edits |
| DBF structure vs stored value audit | Issue #27 SL logic changes |
| QLAdmin display path analysis | Production DBF modification |

---

## 3. Evidence Reviewed

| Artifact | Location | Role |
|----------|----------|------|
| LifePRO PPBEN extract | `QLA_Migration/Source/PPBEN_PolicyBenefit_Extract_20260530.csv` | Source units / VPU |
| v57.39 conversion output | `QLA_Migration/Output/quikridr.csv` | Converter CSV |
| Issue #21K migration CLI | `qladmin_core/issue21k_units_migration.py` | DBF widen + reload |
| Staging DBF (generated 2026-06-28) | `QLA_Migration/Output/qladmin_issue21k/QUIKRIDR.DBF` | N(10,5) reload proof |
| Validators | `tools/validators/validate_issue21k_*.py` | PASS on CSV + staging DBF |
| Prior 21K reports | `Issue_Log_Items/Issue_21/reports/Issue_21K_*.md` | Original root-cause chain |
| Issue #26 field defs | `Issue_Log_Items/Issue_26/Issue_26_Field_Definition_Report.md` | Amount Ins = MUNIT × MVPU |
| Client production DBF | **Not supplied** | Cannot verify active QLAdmin data path |

---

## 4. Intake Findings (Summary)

| Layer | Verdict for `010448806C` PUA |
|-------|------------------------------|
| LifePRO source | **CORRECT** — `NUMBER_OF_UNITS = 5.75296`, `VALUE_PER_UNIT = 1000.00` |
| v57.39 `quikridr.csv` | **CORRECT** — `MUNIT = 5.75296`, `MVPU = 1000.00`, face = **$5,752.96** |
| Staging `QUIKRIDR.DBF` (reload) | **CORRECT** — `MUNIT N(10,5)`, stored `5.75296`, face **$5,752.96** |
| Client QLAdmin UI | **INCORRECT** — shows **$5,753.00** |
| v57.39 converter | **Not implicated** |

---

## 5. Primary Reopen Hypothesis

Precision loss occurs **after** conversion CSV emission — in the **client QLAdmin DBF deployment / load / display path**, not in the v57.39 converter.

The new **`$5,753.00`** display suggests a **rounding layer** (3-decimal unit round or whole-dollar face round) is still applied even if DBF field width was expanded.

---

## 6. Routing

| Next stage | Reason |
|------------|--------|
| **Dependency Gate** (immediate) | Client must supply production `QUIKRIDR.DBF` row + field structure for `010448806C` / MPHASE 2 / `1708PA` |
| **Deployment/DBF Remediation Agent** (after gate) | Verify six-table migration + CSV reload + reindex on active data folder |

**Not routed to Development Agent** unless production DBF proves CSV is wrong (currently disproven).

---

## 7. Protected Issues

No changes to #21D, #21J, #21M, #21M-FU, #25, #26, #27, #28.

---

**Stop point:** Intake complete. Proceed to root cause analysis and end-to-end trace documents.
