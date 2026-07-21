# QLAdmin Data Governance Executive Summary

## Overall Result

PASSED — no problems found

## Run Snapshot

| | |
|---|---|
| Data Region | `Q:\CSO\CSO_Test_6_30_2026` |
| Run ID | `DG-20260718_185125_518008` |
| Run Date | July 18, 2026 at 6:51:25 PM |
| Governance Items Executed | DG-QUIKDATE — QuikDate Processing Date Integrity |
| Rules Executed | 6 |
| Rules Passed | 6 |
| Rules Failed | 0 |
| Rules Not Run | 0 |
| Rules with Processing Errors | 0 |
| Total Records Reviewed | 6 |
| Records That Looked Fine | 6 |
| Problems Found | 0 |
| Data Conformance Accuracy | **100.00%** |

## Data Conformance Accuracy

**100.00%**

100.00% of the record checks completed without a governance exception.

Data Conformance Accuracy represents the percentage of evaluated records that matched the active governance rules during this run. It does not independently confirm that every value is factually or actuarially correct.

## Top Issues

No significant issues were found in this run.

---

# QLAdmin Data Governance — Results (Plain Language)

## Bottom line

**PASSED — no problems found**

All selected governance checks completed successfully. No problems were found in the records reviewed for this run.

## What this report covers

These checks review the selected QLAdmin tables against the active governance rules for this run (uniqueness, references, required fields, formats, and configured default values).

| | |
|---|---|
| When it ran | 2026-07-18 18:51:25 |
| Run ID | DG-20260718_185125_518008 |
| Data region (full path) | `Q:\CSO\CSO_Test_6_30_2026` |
| Output folder for this run | `c:\Users\warren\Documents\GitHub\Warrenhughes1974\data_governance\docs\remediation\items\DG-R-003_quikdate_prior_month_end\validation_out\DG-20260718_185125_518008` |
| Source opened read-only | Yes |
| Source files modified | No |
| Records reviewed | 6 |
| Records that looked fine | 6 |
| Problems found | 0 |
| Data Conformance Accuracy | 100.00% |
| Technical errors | 0 |
| Validation guide | `data_governance_validation_guide.md` |
| Validation manifest | `data_governance_validation_manifest.json` |

## Item 5: QuikDate Processing Date Integrity

Validate that QuikDate PAC Bill, Direct Bill, and Reinsurance Bill dates equal the prior-month-end date for the governance run date, and that ACHFILEID, ACHFILEID2, and ESCDATE (ESC_DATE) match required defaults.

### Check: PAC Bill Date Must Be Set to the Previous Month End

**Result:** PASSED — no problems found

**What we checked:** Ensure the QuikDate PAC Bill date equals the final calendar day of the month immediately before the governance run date.

Looked at **1** record(s): **1** looked fine, **0** had a problem.

No issues. Nothing to fix for this check.

### Check: Direct Bill Date Must Be Set to the Previous Month End

**Result:** PASSED — no problems found

**What we checked:** Ensure the QuikDate Direct Bill date equals the final calendar day of the month immediately before the governance run date.

Looked at **1** record(s): **1** looked fine, **0** had a problem.

No issues. Nothing to fix for this check.

### Check: Reinsurance Bill Date Must Be Set to the Previous Month End

**Result:** PASSED — no problems found

**What we checked:** Ensure the QuikDate Reinsurance Bill date equals the final calendar day of the month immediately before the governance run date.

Looked at **1** record(s): **1** looked fine, **0** had a problem.

No issues. Nothing to fix for this check.

### Check: ACH File ID Must Default to Zero

**Result:** PASSED — no problems found

**What we checked:** Ensure QuikDate.ACHFILEID equals the business-supplied default 0.

Looked at **1** record(s): **1** looked fine, **0** had a problem.

No issues. Nothing to fix for this check.

### Check: Secondary ACH File ID Must Default to A

**Result:** PASSED — no problems found

**What we checked:** Ensure QuikDate.ACHFILEID2 equals the business-supplied default A.

Looked at **1** record(s): **1** looked fine, **0** had a problem.

No issues. Nothing to fix for this check.

### Check: ESCDATE Must Be Blank

**Result:** PASSED — no problems found

**What we checked:** Ensure the QuikDate ESCDATE value is blank (physical field ESC_DATE).

Looked at **1** record(s): **1** looked fine, **0** had a problem.

No issues. Nothing to fix for this check.

## What to do next

No action needed for the selected governance checks.

Companion files: `data_governance_validation_guide.md` (what was validated), `data_governance_validation_manifest.json`, `data_governance_findings.csv`, `data_governance_summary.csv`.
