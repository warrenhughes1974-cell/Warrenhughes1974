# QLAdmin Data Governance — Results (Plain Language)

**Read this file only.** It combines the automated software test results and the sample data check results in one place.

---

## Bottom line

| Area | Result |
|------|--------|
| Automated software tests (proves the checks work correctly) | **PASSED — 26 of 26 tests passed** |
| Sample data run (demo data with known problems) | **FAILED — 9 problems found** (expected for the demo) |

The software tests are meant to pass.  
The sample data run is meant to fail on purpose so you can see how problems look in the report.

---

## Part 1 — Automated software tests

**Question:** Does the new governance tool work the way we designed it?

**Answer:** Yes.

| | |
|---|---|
| When run | 2026-07-18 |
| Command | `python -m pytest data_governance/tests -q` |
| Result | **26 passed** |
| Failures | 0 |

In plain English: the tool correctly detects good data, bad data, blank codes, padded DBF values, missing company codes, and duplicate company codes. It can also run one rule, one group of rules, or all rules without stopping when one rule fails.

---

## Part 2 — Sample data run (what a real report looks like)

**Question:** If we run the three company-code checks against demo data that has problems, what do we see?

**Answer:** Overall **FAILED** — 9 problems. Nothing in the source files was changed; this only reports issues.

| | |
|---|---|
| When it ran | 2026-07-18 09:35:46 |
| Run ID | DG-20260718_093546 |
| Records reviewed | 12 |
| Looked fine | 3 |
| Problems found | 9 |
| Technical errors | 0 |

### What we checked (Item 1 — QuikComp Company Code Integrity)

In plain English: every company code should appear once in the company table, and every agent and policy should point to a real company code.

---

### Check 1: Unique QuikComp Company Code

**Result:** FAILED — problems were found that need attention

**What we checked:** Each company code in QuikComp should appear only once, and should not be blank.

**Problems found:**

1. QuikComp contains a blank company code.
2. Duplicate company code 'A' exists 2 times in QuikComp.
3. Duplicate company code 'A' exists 2 times in QuikComp. *(second of the two duplicate rows)*

**What this means:** The company list has a blank code and company “A” is listed twice. That needs cleanup in QuikComp.

---

### Check 2: Agent Company Code Must Exist in QuikComp

**Result:** FAILED — problems were found that need attention

**What we checked:** Every agent’s company code must exist once in QuikComp.

**Problems found:**

1. Agent '10002' uses company code 'Z', but 'Z' does not exist in QuikComp.
2. Agent '10003' does not have a company code.
3. Agent '10004' references company code 'A', but QuikComp contains duplicate records for that code.

**What this means:** One agent points to a company that does not exist, one agent has no company at all, and one agent points to the duplicated company “A”.

---

### Check 3: Policy Number Company Code Must Exist in QuikComp

**Result:** FAILED — problems were found that need attention

**What we checked:** The last letter of each policy number is treated as the company code (business rule). That code must exist once in QuikComp.

**Problems found:**

1. Policy '123456789X' has company code 'X', but 'X' does not exist in QuikComp.
2. A company code could not be derived from policy number '(blank)'.
3. Policy '555555555A' references company code 'A', but QuikComp contains duplicate records for that code.

**What this means:** One policy ends with a company that does not exist, one policy is blank, and one policy ends with the duplicated company “A”.

---

## What to do next

1. For **real client data**, run:

   ```bash
   python -m data_governance --data-dir "YOUR_DATA_FOLDER" --output-dir "YOUR_REPORT_FOLDER"
   ```

2. Open the single report file it creates:

   `data_governance_report.md`

3. Fix any problems in the source data (this tool does not change data for you), then re-run.

---

## Optional technical files (only if you need them)

These are for analysts who want spreadsheets. You do **not** need them to understand the results:

- `data_governance_findings.csv`
- `data_governance_summary.csv`
- `data_governance_run_summary.json`
