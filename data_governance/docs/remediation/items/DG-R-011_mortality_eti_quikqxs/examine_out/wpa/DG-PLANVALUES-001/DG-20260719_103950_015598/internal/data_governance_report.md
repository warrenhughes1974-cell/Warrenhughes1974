# QLAdmin Data Governance Executive Summary

## Overall Result

FAILED — problems were found that need attention

## Run Snapshot

| | |
|---|---|
| Data Region | `Q:\WPA\WPA_GABIE` |
| Run ID | `DG-20260719_103950_015598` |
| Run Date | July 19, 2026 at 10:39:50 AM |
| Governance Items Executed | DG-PLANVALUES — Plan Value Reference Integrity |
| Rules Executed | 1 |
| Rules Passed | 0 |
| Rules Failed | 1 |
| Rules Not Run | 0 |
| Rules with Processing Errors | 0 |
| Total Records Reviewed | 1,431 |
| Records That Looked Fine | 1,415 |
| Problems Found | 16 |
| Data Conformance Accuracy | **98.88%** |

## Data Conformance Accuracy

**98.88%**

98.88% of the record checks completed without a governance exception.

Data Conformance Accuracy represents the percentage of evaluated records that matched the active governance rules during this run. It does not independently confirm that every value is factually or actuarially correct.

## Top Issues

1. 16 records failed 'Mortality Table Must Exist in QuikQxs' (example: QuikPlCv plan '517P10' contains a blank mortality table.)

---

# QLAdmin Data Governance — Results (Plain Language)

## Bottom line

**FAILED — problems were found that need attention**

We found **16 problem(s)** in the data reviewed. Details are listed below by check. Nothing in the source files was changed — this report only points out issues for review.

## What this report covers

These checks review the selected QLAdmin tables against the active governance rules for this run (uniqueness, references, required fields, formats, and configured default values).

| | |
|---|---|
| When it ran | 2026-07-19 10:39:50 |
| Run ID | DG-20260719_103950_015598 |
| Data region (full path) | `Q:\WPA\WPA_GABIE` |
| Output folder for this run | `C:\Users\warren\Documents\GitHub\Warrenhughes1974\data_governance\docs\remediation\items\DG-R-011_mortality_eti_quikqxs\examine_out\wpa\DG-PLANVALUES-001\DG-20260719_103950_015598` |
| Source opened read-only | Yes |
| Source files modified | No |
| Records reviewed | 1,431 |
| Records that looked fine | 1,415 |
| Problems found | 16 |
| Data Conformance Accuracy | 98.88% |
| Technical errors | 0 |
| Validation guide | `data_governance_validation_guide.md` |
| Validation manifest | `data_governance_validation_manifest.json` |

## Item 6: Plan Value Reference Integrity

Validate that mortality tables, plans, gender codes, underwriting classes, bands, issue states, and effective dates used by QuikPlCv, QuikPlTv, QuikPlGp, QuikPlDb, and QuikPlDv are approved defaults or valid setup references.

### Check: Mortality Table Must Exist in QuikQxs

**Result:** FAILED — problems were found that need attention

**What we checked:** Ensure every populated normalized MORT value on applicable plan-value tables exists exactly once in QuikQxs.

Looked at **1431** record(s): **1415** looked fine, **16** had a problem.

**Problems found:**

1. QuikPlCv plan '517P10' contains a blank mortality table.
2. QuikPlCv plan '517P20' contains a blank mortality table.
3. QuikPlCv plan '517P30' contains a blank mortality table.
4. QuikPlCv plan '517T10' contains a blank mortality table.
5. QuikPlCv plan '517T20' contains a blank mortality table.
6. QuikPlCv plan '517T30' contains a blank mortality table.
7. QuikPlCv plan '517YRT' contains a blank mortality table.
8. QuikPlCv plan '517R10' contains a blank mortality table.
9. QuikPlCv plan '517F10' contains a blank mortality table.
10. QuikPlCv plan '517F20' contains a blank mortality table.
11. QuikPlCv plan '517F30' contains a blank mortality table.
12. QuikPlCv plan '517T2R' contains a blank mortality table.
13. QuikPlCv plan '517T1R' contains a blank mortality table.
14. QuikPlCv plan '517T3R' contains a blank mortality table.
15. QuikPlCv plan '517R1F' contains a blank mortality table.
16. QuikPlCv plan '5RACTG' contains a blank mortality table.

## What to do next

1. Review each problem listed above with the business owner of the related data.
2. Correct the source QLAdmin data if the finding is valid (this tool does **not** change the data for you).
3. Re-run the governance checks after corrections.

Companion files: `data_governance_validation_guide.md` (what was validated), `data_governance_validation_manifest.json`, `data_governance_findings.csv`, `data_governance_summary.csv`.
