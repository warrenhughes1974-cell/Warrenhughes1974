# QLAdmin Data Governance — Results (Plain Language)

## Bottom line

**FAILED — problems were found that need attention**

We found **11 problem(s)** in the company-code data. Details are listed below by check. Nothing in the source files was changed — this report only points out issues for review.

## What this report covers

These checks make sure every **company code** used for companies, agents, and policies is valid and not duplicated in QuikComp (the company table).

| | |
|---|---|
| When it ran | 2026-07-18 10:24:05 |
| Run ID | DG-20260718_102405_823544 |
| Data region (full path) | `c:\Users\warren\Documents\GitHub\Warrenhughes1974\data_governance\docs\sample_report_output\quiklist_sample` |
| Output folder for this run | `c:\Users\warren\Documents\GitHub\Warrenhughes1974\data_governance\docs\sample_report_output\quiklist_sample\DG-20260718_102405_823544` |
| Source opened read-only | Yes |
| Source files modified | No |
| Records reviewed | 18 |
| Records that looked fine | 7 |
| Problems found | 11 |
| Technical errors | 0 |

## Item 4: QuikList Group Billing Integrity

In plain English: every company code should appear once in the company table, and every agent and policy should point to a real company code.

### Check: Group Number Must Be Unique

**Result:** FAILED — problems were found that need attention

**What we checked:** Ensure each group number appears only once in QuikList.

Looked at **2** record(s): **0** looked fine, **2** had a problem.

**Problems found:**

1. QuikList contains 2 records for group number '12345678'. Each group number must be unique.
2. QuikList contains 2 records for group number '12345678'. Each group number must be unique.

### Check: QuikList Company Code Must Exist in QuikComp

**Result:** FAILED — problems were found that need attention

**What we checked:** Ensure every company code assigned to a QuikList group is defined in QuikComp.

Looked at **2** record(s): **0** looked fine, **2** had a problem.

**Problems found:**

1. Group number '12345678' uses company code 'X', but company code 'X' does not exist in QuikComp.
2. Group number '12345678' uses company code 'A', but QuikComp contains multiple records for company code 'A'.

### Check: Group Billing Name Must Be Populated

**Result:** FAILED — problems were found that need attention

**What we checked:** Ensure every QuikList group has a billing name.

Looked at **2** record(s): **1** looked fine, **1** had a problem.

**Problems found:**

1. Group number '12345678' does not contain a group billing name in MBILLNAME.

### Check: Group Bill Sort Must Default to N

**Result:** FAILED — problems were found that need attention

**What we checked:** Ensure QuikList.MSORT equals the business-supplied default N.

Looked at **2** record(s): **1** looked fine, **1** had a problem.

**Problems found:**

1. Group number '12345678' has MSORT='X'. The required governance value is 'N'.

### Check: Life Lapse Days Must Default to Zero

**Result:** FAILED — problems were found that need attention

**What we checked:** Ensure QuikList.MLAPSEL equals the business-supplied default 0.

Looked at **2** record(s): **1** looked fine, **1** had a problem.

**Problems found:**

1. Group number '12345678' has MLAPSEL='30'. The required governance value is 0.

### Check: Health and Accident Lapse Days Must Default to Zero

**Result:** FAILED — problems were found that need attention

**What we checked:** Ensure QuikList.MLAPSEH equals the business-supplied default 0.

Looked at **2** record(s): **1** looked fine, **1** had a problem.

**Problems found:**

1. Group number '12345678' has MLAPSEH='30'. The required governance value is 0.

### Check: Group Status Must Default to Active

**Result:** FAILED — problems were found that need attention

**What we checked:** Ensure QuikList.MSTATUS equals the business-supplied default A.

Looked at **2** record(s): **1** looked fine, **1** had a problem.

**Problems found:**

1. Group number '12345678' has MSTATUS='I'. The required governance value is 'A'.

### Check: Group Bill Day Must Default to Zero

**Result:** FAILED — problems were found that need attention

**What we checked:** Ensure QuikList.MBILLDAY equals the business-supplied default 0.

Looked at **2** record(s): **1** looked fine, **1** had a problem.

**Problems found:**

1. Group number '12345678' has MBILLDAY='15'. The required governance value is 0.

### Check: Group Bill Mode Must Default to Zero

**Result:** FAILED — problems were found that need attention

**What we checked:** Ensure QuikList.MBILLMODE equals the business-supplied default 0.

Looked at **2** record(s): **1** looked fine, **1** had a problem.

**Problems found:**

1. Group number '12345678' has MBILLMODE='12'. The required governance value is 0.

## What to do next

1. Review each problem listed above with the business owner of the company/agent/policy data.
2. Correct the source QLAdmin data if the finding is valid (this tool does **not** change the data for you).
3. Re-run the governance checks after corrections.

Technical detail files (optional): `data_governance_findings.csv`, `data_governance_summary.csv`.
