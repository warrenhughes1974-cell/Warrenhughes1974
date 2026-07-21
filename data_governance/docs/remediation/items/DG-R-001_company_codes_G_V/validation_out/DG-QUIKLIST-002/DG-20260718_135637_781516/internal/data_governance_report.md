# QLAdmin Data Governance Executive Summary

## Overall Result

PASSED — no problems found

## Run Snapshot

| | |
|---|---|
| Data Region | `Q:\CSO\CSO_Test_6_30_2025` |
| Run ID | `DG-20260718_135637_781516` |
| Run Date | July 18, 2026 at 1:56:37 PM |
| Governance Items Executed | DG-QUIKLIST — QuikList Group Billing Integrity |
| Rules Executed | 1 |
| Rules Passed | 1 |
| Rules Failed | 0 |
| Rules Not Run | 0 |
| Rules with Processing Errors | 0 |
| Total Records Reviewed | 0 |
| Records That Looked Fine | 0 |
| Problems Found | 0 |
| Data Conformance Accuracy | **Not Available — No records were evaluated** |

## Data Conformance Accuracy

**Not Available — No records were evaluated**

Not Available — No records were evaluated

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
| When it ran | 2026-07-18 13:56:37 |
| Run ID | DG-20260718_135637_781516 |
| Data region (full path) | `Q:\CSO\CSO_Test_6_30_2025` |
| Output folder for this run | `c:\Users\warren\Documents\GitHub\Warrenhughes1974\data_governance\docs\remediation\items\DG-R-001_company_codes_G_V\validation_out\DG-QUIKLIST-002\DG-20260718_135637_781516` |
| Source opened read-only | Yes |
| Source files modified | No |
| Records reviewed | 0 |
| Records that looked fine | 0 |
| Problems found | 0 |
| Data Conformance Accuracy | Not Available — No records were evaluated |
| Technical errors | 0 |
| Validation guide | `data_governance_validation_guide.md` |
| Validation manifest | `data_governance_validation_manifest.json` |

## Item 4: QuikList Group Billing Integrity

Ensure QuikList group bill rows have unique group numbers, valid company codes, populated billing names, and business-supplied default values for sort, lapse days, status, bill day, and bill mode.

### Check: QuikList Company Code Must Exist in QuikComp

**Result:** PASSED — no problems found

**What we checked:** Ensure every company code assigned to a QuikList group is defined in QuikComp.

Looked at **0** record(s): **0** looked fine, **0** had a problem.

No issues. Nothing to fix for this check.

## What to do next

No action needed for the selected governance checks.

Companion files: `data_governance_validation_guide.md` (what was validated), `data_governance_validation_manifest.json`, `data_governance_findings.csv`, `data_governance_summary.csv`.
