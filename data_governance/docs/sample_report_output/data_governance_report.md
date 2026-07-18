# QLAdmin Data Governance — Results (Plain Language)

## Bottom line

**FAILED — problems were found that need attention**

We found **9 problem(s)** in the company-code data. Details are listed below by check. Nothing in the source files was changed — this report only points out issues for review.

## What this report covers

These checks make sure every **company code** used for companies, agents, and policies is valid and not duplicated in QuikComp (the company table).

| | |
|---|---|
| When it ran | 2026-07-18 09:40:13 |
| Run ID | DG-20260718_094013 |
| Data looked at | `c:\Users\warren\Documents\GitHub\Warrenhughes1974\data_governance\docs\sample_report_output` |
| Records reviewed | 12 |
| Records that looked fine | 3 |
| Problems found | 9 |
| Technical errors | 0 |

## Item 1: QuikComp Company Code Integrity

In plain English: every company code should appear once in the company table, and every agent and policy should point to a real company code.

### Check: Unique QuikComp Company Code

**Result:** FAILED — problems were found that need attention

**What we checked:** Ensure each company code appears only once in QuikComp.

Looked at **4** record(s): **1** looked fine, **3** had a problem.

**Problems found:**

1. QuikComp contains a blank company code.
2. Duplicate company code 'A' exists 2 times in QuikComp.
3. Duplicate company code 'A' exists 2 times in QuikComp.

### Check: Agent Company Code Must Exist in QuikComp

**Result:** FAILED — problems were found that need attention

**What we checked:** Ensure every company code assigned to an agent is defined in QuikComp.

Looked at **4** record(s): **1** looked fine, **3** had a problem.

**Problems found:**

1. Agent '10002' uses company code 'Z', but 'Z' does not exist in QuikComp.
2. Agent '10003' does not have a company code.
3. Agent '10004' references company code 'A', but QuikComp contains duplicate records for that code.

### Check: Policy Number Company Code Must Exist in QuikComp

**Result:** FAILED — problems were found that need attention

**What we checked:** Ensure the company code represented by the final character of each policy number exists in QuikComp.

Looked at **4** record(s): **1** looked fine, **3** had a problem.

**Problems found:**

1. Policy '123456789X' has company code 'X', but 'X' does not exist in QuikComp.
2. A company code could not be derived from policy number '(blank)'.
3. Policy '555555555A' references company code 'A', but QuikComp contains duplicate records for that code.

## What to do next

1. Review each problem listed above with the business owner of the company/agent/policy data.
2. Correct the source QLAdmin data if the finding is valid (this tool does **not** change the data for you).
3. Re-run the governance checks after corrections.

Technical detail files (optional): `data_governance_findings.csv`, `data_governance_summary.csv`.
