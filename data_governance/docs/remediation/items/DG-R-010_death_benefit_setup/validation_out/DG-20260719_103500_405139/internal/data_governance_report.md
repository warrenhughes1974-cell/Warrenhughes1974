# QLAdmin Data Governance Executive Summary

## Overall Result

PASSED — no problems found

## Run Snapshot

| | |
|---|---|
| Data Region | `Q:\CSO\CSO_Test_6_30_2026` |
| Run ID | `DG-20260719_103500_405139` |
| Run Date | July 19, 2026 at 10:35:00 AM |
| Governance Items Executed | DG-QUIKPLAN — Plan Setup |
| Rules Executed | 1 |
| Rules Passed | 1 |
| Rules Failed | 0 |
| Rules Not Run | 0 |
| Rules with Processing Errors | 0 |
| Total Records Reviewed | 40 |
| Records That Looked Fine | 40 |
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
| When it ran | 2026-07-19 10:35:00 |
| Run ID | DG-20260719_103500_405139 |
| Data region (full path) | `Q:\CSO\CSO_Test_6_30_2026` |
| Output folder for this run | `c:\Users\warren\Documents\GitHub\Warrenhughes1974\data_governance\docs\remediation\items\DG-R-010_death_benefit_setup\validation_out\DG-20260719_103500_405139` |
| Source opened read-only | Yes |
| Source files modified | No |
| Records reviewed | 40 |
| Records that looked fine | 40 |
| Problems found | 0 |
| Data Conformance Accuracy | 100.00% |
| Technical errors | 0 |
| Validation guide | `data_governance_validation_guide.md` |
| Validation manifest | `data_governance_validation_manifest.json` |

## Item 7: Plan Setup

Validate that plans are configured with valid plan codes, approved default values, appropriate payment and insurance periods, valid related setup references, and the supporting rate and value records required for the plan.

### Check: Death Benefit Supporting Tables Must Exist

**Result:** PASSED — no problems found

**What we checked:** Ensure plans with varying death-benefit schedules (VARDB 1/2/3) have required supporting records. Level (VARDB 0 / INITVAL) and not-on-file (VARDB 4) skip.

Looked at **40** record(s): **40** looked fine, **0** had a problem.

No issues. Nothing to fix for this check.

## What to do next

No action needed for the selected governance checks.

Companion files: `data_governance_validation_guide.md` (what was validated), `data_governance_validation_manifest.json`, `data_governance_findings.csv`, `data_governance_summary.csv`.
