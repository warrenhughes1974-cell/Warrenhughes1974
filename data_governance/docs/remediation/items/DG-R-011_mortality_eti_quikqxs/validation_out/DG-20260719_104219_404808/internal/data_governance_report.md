# QLAdmin Data Governance Executive Summary

## Overall Result

PASSED — no problems found

## Run Snapshot

| | |
|---|---|
| Data Region | `Q:\CSO\CSO_Test_6_30_2026` |
| Run ID | `DG-20260719_104219_404808` |
| Run Date | July 19, 2026 at 10:42:19 AM |
| Governance Items Executed | DG-PLANVALUES — Plan Value Reference Integrity |
| Rules Executed | 1 |
| Rules Passed | 1 |
| Rules Failed | 0 |
| Rules Not Run | 0 |
| Rules with Processing Errors | 0 |
| Total Records Reviewed | 245 |
| Records That Looked Fine | 245 |
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
| When it ran | 2026-07-19 10:42:19 |
| Run ID | DG-20260719_104219_404808 |
| Data region (full path) | `Q:\CSO\CSO_Test_6_30_2026` |
| Output folder for this run | `c:\Users\warren\Documents\GitHub\Warrenhughes1974\data_governance\docs\remediation\items\DG-R-011_mortality_eti_quikqxs\validation_out\DG-20260719_104219_404808` |
| Source opened read-only | Yes |
| Source files modified | No |
| Records reviewed | 245 |
| Records that looked fine | 245 |
| Problems found | 0 |
| Data Conformance Accuracy | 100.00% |
| Technical errors | 0 |
| Validation guide | `data_governance_validation_guide.md` |
| Validation manifest | `data_governance_validation_manifest.json` |

## Item 6: Plan Value Reference Integrity

Validate that mortality tables, plans, gender codes, underwriting classes, bands, issue states, and effective dates used by QuikPlCv, QuikPlTv, QuikPlGp, QuikPlDb, and QuikPlDv are approved defaults or valid setup references.

### Check: Mortality Table Must Exist in QuikQxs

**Result:** PASSED — no problems found

**What we checked:** Ensure every populated normalized MORT value on applicable plan-value tables exists exactly once in QuikQxs. Blank and null MORT are skipped (DG-R-011).

Looked at **245** record(s): **245** looked fine, **0** had a problem.

No issues. Nothing to fix for this check.

## What to do next

No action needed for the selected governance checks.

Companion files: `data_governance_validation_guide.md` (what was validated), `data_governance_validation_manifest.json`, `data_governance_findings.csv`, `data_governance_summary.csv`.
