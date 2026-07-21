# QLAdmin Data Governance Executive Summary

## Overall Result

FAILED — problems were found that need attention

## Run Snapshot

| | |
|---|---|
| Data Region | `Q:\CSO\CSO_Test_6_30_2026` |
| Run ID | `DG-20260718_194450_399823` |
| Run Date | July 18, 2026 at 7:44:50 PM |
| Governance Items Executed | DG-QUIKPLAN — Plan Setup |
| Rules Executed | 1 |
| Rules Passed | 0 |
| Rules Failed | 1 |
| Rules Not Run | 0 |
| Rules with Processing Errors | 0 |
| Total Records Reviewed | 142 |
| Records That Looked Fine | 141 |
| Problems Found | 1 |
| Data Conformance Accuracy | **99.30%** |

## Data Conformance Accuracy

**99.30%**

99.30% of the record checks completed without a governance exception.

Data Conformance Accuracy represents the percentage of evaluated records that matched the active governance rules during this run. It does not independently confirm that every value is factually or actuarially correct.

## Top Issues

1. The low age must be less than the high age.

---

# QLAdmin Data Governance — Results (Plain Language)

## Bottom line

**FAILED — problems were found that need attention**

We found **1 problem(s)** in the data reviewed. Details are listed below by check. Nothing in the source files was changed — this report only points out issues for review.

## What this report covers

These checks review the selected QLAdmin tables against the active governance rules for this run (uniqueness, references, required fields, formats, and configured default values).

| | |
|---|---|
| When it ran | 2026-07-18 19:44:50 |
| Run ID | DG-20260718_194450_399823 |
| Data region (full path) | `Q:\CSO\CSO_Test_6_30_2026` |
| Output folder for this run | `data_governance\docs\remediation\items\DG-R-008_blank_plan_orphans\examine_out\DG-20260718_194450_399823` |
| Source opened read-only | Yes |
| Source files modified | No |
| Records reviewed | 142 |
| Records that looked fine | 141 |
| Problems found | 1 |
| Data Conformance Accuracy | 99.30% |
| Technical errors | 0 |
| Validation guide | `data_governance_validation_guide.md` |
| Validation manifest | `data_governance_validation_manifest.json` |

## Item 7: Plan Setup

Validate that plans are configured with valid plan codes, approved default values, appropriate payment and insurance periods, valid related setup references, and the supporting rate and value records required for the plan.

### Check: Issue Age Range Must Be Valid

**Result:** FAILED — problems were found that need attention

**What we checked:** Ensure plan issue ages (LOAGE/HIAGE) are readable and the low age is less than the high age. LOAGE may be any valid minimum issue age (DG-R-007: former Age-1 must-be-zero requirement removed).

Looked at **142** record(s): **141** looked fine, **1** had a problem.

**Problems found:**

1. The low age must be less than the high age.

## What to do next

1. Review each problem listed above with the business owner of the related data.
2. Correct the source QLAdmin data if the finding is valid (this tool does **not** change the data for you).
3. Re-run the governance checks after corrections.

Companion files: `data_governance_validation_guide.md` (what was validated), `data_governance_validation_manifest.json`, `data_governance_findings.csv`, `data_governance_summary.csv`.
