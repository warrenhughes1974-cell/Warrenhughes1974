# QLAdmin Data Governance — Results (Plain Language)

## Bottom line

**FAILED — problems were found that need attention**

We found **3 problem(s)** in the company-code data. Details are listed below by check. Nothing in the source files was changed — this report only points out issues for review.

## What this report covers

These checks make sure every **company code** used for companies, agents, and policies is valid and not duplicated in QuikComp (the company table).

| | |
|---|---|
| When it ran | 2026-07-18 10:06:06 |
| Run ID | DG-20260718_100606_997684 |
| Data region (full path) | `c:\Users\warren\Documents\GitHub\Warrenhughes1974\data_governance\docs\sample_report_output` |
| Output folder for this run | `c:\Users\warren\Documents\GitHub\Warrenhughes1974\data_governance\docs\sample_report_output\accounting_sample\DG-20260718_100606_997684` |
| Source opened read-only | Yes |
| Source files modified | No |
| Records reviewed | 8 |
| Records that looked fine | 5 |
| Problems found | 3 |
| Technical errors | 0 |

## Item 3: Accounting Company and Account Integrity

In plain English: every company code should appear once in the company table, and every agent and policy should point to a real company code.

### Check: Company and Account Number Combination Must Be Unique

**Result:** FAILED — problems were found that need attention

**What we checked:** Ensure QuikActg does not contain duplicate accounting assignment records for the same company and plan (verified composite key MCOMP + MPLAN).

Looked at **4** record(s): **2** looked fine, **2** had a problem.

**Problems found:**

1. QuikActg contains 2 records for company code 'A' and plan code '1000'. Each company-and-plan combination must be unique.
2. QuikActg contains 2 records for company code 'A' and plan code '1000'. Each company-and-plan combination must be unique.

### Check: QuikActg Company Code Must Exist in QuikComp

**Result:** FAILED — problems were found that need attention

**What we checked:** Ensure every company code used by QuikActg is defined once in QuikComp.

Looked at **4** record(s): **3** looked fine, **1** had a problem.

**Problems found:**

1. QuikActg plan code '2000' uses company code 'X', but company code 'X' does not exist in QuikComp.

## What to do next

1. Review each problem listed above with the business owner of the company/agent/policy data.
2. Correct the source QLAdmin data if the finding is valid (this tool does **not** change the data for you).
3. Re-run the governance checks after corrections.

Technical detail files (optional): `data_governance_findings.csv`, `data_governance_summary.csv`.
