# QLAdmin Data Governance — Results (Plain Language)

## Bottom line

**FAILED — problems were found that need attention**

We found **4 problem(s)** in the company-code data. Details are listed below by check. Nothing in the source files was changed — this report only points out issues for review.

## What this report covers

These checks make sure every **company code** used for companies, agents, and policies is valid and not duplicated in QuikComp (the company table).

| | |
|---|---|
| When it ran | 2026-07-18 09:53:44 |
| Run ID | DG-20260718_095344_068734 |
| Data region (full path) | `c:\Users\warren\Documents\GitHub\Warrenhughes1974\data_governance\docs\sample_report_output` |
| Output folder for this run | `c:\Users\warren\Documents\GitHub\Warrenhughes1974\data_governance\docs\sample_report_output\DG-20260718_095344_068734` |
| Source opened read-only | Yes |
| Source files modified | No |
| Records reviewed | 5 |
| Records that looked fine | 1 |
| Problems found | 4 |
| Technical errors | 0 |

## Item 2: QuikMstr Policy Number Integrity

In plain English: every company code should appear once in the company table, and every agent and policy should point to a real company code.

### Check: Policy Number Must Contain 9 to 11 Characters

**Result:** FAILED — problems were found that need attention

**What we checked:** Ensure every policy number stored in QuikMstr contains an acceptable number of characters.

Looked at **5** record(s): **1** looked fine, **4** had a problem.

**Problems found:**

1. Policy number '12345678' contains 8 characters. Policy numbers must contain between 9 and 11 characters.
2. Policy number '123456789012' contains 12 characters. Policy numbers must contain between 9 and 11 characters.
3. A QuikMstr record contains a blank policy number. Policy numbers must contain between 9 and 11 characters.
4. A QuikMstr record contains a null policy number. Policy numbers must contain between 9 and 11 characters.

## What to do next

1. Review each problem listed above with the business owner of the company/agent/policy data.
2. Correct the source QLAdmin data if the finding is valid (this tool does **not** change the data for you).
3. Re-run the governance checks after corrections.

Technical detail files (optional): `data_governance_findings.csv`, `data_governance_summary.csv`.
