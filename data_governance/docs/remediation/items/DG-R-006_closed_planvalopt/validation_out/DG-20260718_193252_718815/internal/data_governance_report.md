# QLAdmin Data Governance Executive Summary

## Overall Result

ERROR — the check could not finish (usually a missing file)

## Run Snapshot

| | |
|---|---|
| Data Region | `Q:\CSO\CSO_Test_6_30_2026` |
| Run ID | `DG-20260718_193252_718815` |
| Run Date | July 18, 2026 at 7:32:52 PM |
| Governance Items Executed | (none) |
| Rules Executed | 1 |
| Rules Passed | 0 |
| Rules Failed | 0 |
| Rules Not Run | 0 |
| Rules with Processing Errors | 1 |
| Total Records Reviewed | 0 |
| Records That Looked Fine | 0 |
| Problems Found | 0 |
| Data Conformance Accuracy | **Not Available — No records were evaluated** |

## Data Conformance Accuracy

**Not Available — No records were evaluated**

Not Available — No records were evaluated

Data Conformance Accuracy represents the percentage of evaluated records that matched the active governance rules during this run. It does not independently confirm that every value is factually or actuarially correct.

## Top Issues

No detailed problem findings were recorded. See rule results below for processing errors or incomplete checks.

---

# QLAdmin Data Governance — Results (Plain Language)

## Bottom line

**ERROR — the check could not finish (usually a missing file)**

One or more checks could not finish (for example, a required table was missing). See the error notes below.

## What this report covers

These checks review the selected QLAdmin tables against the active governance rules for this run (uniqueness, references, required fields, formats, and configured default values).

| | |
|---|---|
| When it ran | 2026-07-18 19:32:52 |
| Run ID | DG-20260718_193252_718815 |
| Data region (full path) | `Q:\CSO\CSO_Test_6_30_2026` |
| Output folder for this run | `data_governance\docs\remediation\items\DG-R-006_closed_planvalopt\validation_out\DG-20260718_193252_718815` |
| Source opened read-only | Yes |
| Source files modified | No |
| Records reviewed | 0 |
| Records that looked fine | 0 |
| Problems found | 0 |
| Data Conformance Accuracy | Not Available — No records were evaluated |
| Technical errors | 1 |
| Validation guide | `data_governance_validation_guide.md` |
| Validation manifest | `data_governance_validation_manifest.json` |

## What to do next

1. Review each problem listed above with the business owner of the related data.
2. Correct the source QLAdmin data if the finding is valid (this tool does **not** change the data for you).
3. Re-run the governance checks after corrections.

Companion files: `data_governance_validation_guide.md` (what was validated), `data_governance_validation_manifest.json`, `data_governance_findings.csv`, `data_governance_summary.csv`.
