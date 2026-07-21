# QLAdmin Data Governance Validation Guide

This companion document explains exactly what the governance process validated in this specific run. It is generated from the registered rules that were selected and from the actual run results.

## Run Information

| | |
|---|---|
| Run ID | `DG-20260719_104221_679821` |
| Run date and time | July 19, 2026 at 10:42:21 AM |
| Data-region path | `Q:\CSO\CSO_Test_6_30_2026` |
| Output path | `c:\Users\warren\Documents\GitHub\Warrenhughes1974\data_governance\docs\remediation\items\DG-R-011_mortality_eti_quikqxs\validation_out\DG-20260719_104221_679821` |
| Overall result | PASSED |
| Data Conformance Accuracy | 100.00% |
| Source opened read-only | Yes |
| Source files modified | No |

100.00% of the record checks completed without a governance exception.

## What This Run Did

This run reviewed the selected QLAdmin data region against the active governance rules listed below. It did not change any source data. Each rule checked a specific table, field, relationship, format, uniqueness requirement, or expected value.

## Tables Reviewed

- QuikPlCv
- QuikPlDb
- QuikPlDv
- QuikPlGp
- QuikPlTv
- QuikQxs

## Validation Rules Executed

## DG-PLANVALUES-002 — ETI Mortality Table Must Exist in QuikQxs

**Governance item ID:** DG-PLANVALUES

**Technical name:** Validate Plan Value ETI Mortality Table Reference

**Purpose:**

Ensure every populated normalized ETIMORT value exists exactly once in QuikQxs. Blank and null ETIMORT are skipped (DG-R-011).

**Tables reviewed:**

- QuikPlCv
- QuikPlTv
- QuikPlGp
- QuikPlDb
- QuikPlDv
- QuikQxs

**Fields reviewed:**

- ETIMORT
- QuikQxs.MORT

**Reference tables / fields:**

- QuikQxs
- QuikPlTv
- QuikPlGp
- QuikPlDb
- QuikPlDv
- QuikQxs.MORT

**Severity:** Critical

**Records reviewed:** 102

**Records that looked fine:** 102

**Problems found:** 0

**Result:** PASSED

**Totals by source table:**

`{"QuikPlCv": {"failed": 0, "not_run": 0, "not_run_reason": "", "passed": 102, "reviewed": 102}, "QuikPlDb": {"failed": 0, "not_run": 1, "not_run_reason": "QuikPlDb does not contain field ETIMORT.", "passed": 0, "reviewed": 0}, "QuikPlDv": {"failed": 0, "not_run": 1, "not_run_reason": "QuikPlDv does not contain field ETIMORT.", "passed": 0, "reviewed": 0}, "QuikPlGp": {"failed": 0, "not_run": 1, "not_run_reason": "QuikPlGp does not contain field ETIMORT.", "passed": 0, "reviewed": 0}, "QuikPlTv": {"failed": 0, "not_run": 1, "not_run_reason": "QuikPlTv does not contain field ETIMORT.", "passed": 0, "reviewed": 0}}`

**Exact validation performed:**

Source field ETIMORT C(2) on QuikPlCv only (verified). Same QuikQxs.MORT key as MORT. Null and blank are skipped (optional). Tables without ETIMORT are NOT_RUN.

**Normalization / interpretation applied:**

Source field ETIMORT C(2) on QuikPlCv only (verified). Same QuikQxs.MORT key as MORT. Null and blank are skipped (optional). Tables without ETIMORT are NOT_RUN.

**Conditions that pass:**

- Source field ETIMORT C(2) on QuikPlCv only (verified). Same QuikQxs.MORT key as MORT. Null and blank are skipped (optional). Tables without ETIMORT are NOT_RUN.
- The record was available for evaluation.
- None of the listed failure conditions applied after normalization.

**Conditions that fail:**

- ETIMORT is populated and does not exist in QuikQxs.
- The matching QuikQxs.MORT key is duplicated.

**What this rule does not validate:**

- This rule confirms that the ETI mortality-table code exists in QuikQxs. It does not confirm that the mortality table is actuarially appropriate for the plan.
- Whether values are factually or actuarially correct beyond this rule's checks.
- Fields on the same table that are not listed in this rule.
- Business intent that is not encoded in the rule definition.
- Whether missing reference data should be created automatically.

## Rules Not Executed or Not Completed

### Registered rules not selected for this run

- **DG-QUIKCOMP-001** — Unique QuikComp Company Code
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKCOMP-002** — Agent Company Code Must Exist in QuikComp
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKCOMP-003** — Policy Number Company Code Must Exist in QuikComp
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKMSTR-001** — Policy Number Must Contain 4 to 11 Characters
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKACTG-001** — Company and Account Number Combination Must Be Unique
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKACTG-002** — QuikActg Company Code Must Exist in QuikComp
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKLIST-001** — Group Number Must Be Unique
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKLIST-002** — QuikList Company Code Must Exist in QuikComp
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKLIST-003** — Group Billing Name Must Be Populated
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKLIST-004** — Group Bill Sort Must Default to N
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKLIST-005** — Life Lapse Days Must Default to Zero
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKLIST-006** — Health and Accident Lapse Days Must Default to Zero
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKLIST-007** — Group Status Must Default to Active
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKLIST-008** — Group Bill Day Must Default to Zero
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKLIST-009** — Group Bill Mode Must Default to Zero
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKDATE-001** — PAC Bill Date Must Be Set to the Previous Month End
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKDATE-002** — Direct Bill Date Must Be Set to the Previous Month End
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKDATE-003** — Reinsurance Bill Date Must Be Set to the Previous Month End
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKDATE-004** — ACH File ID Must Default to Zero
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKDATE-005** — Secondary ACH File ID Must Default to A
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKDATE-006** — ESCDATE Must Be Blank
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-PLANVALUES-001** — Mortality Table Must Exist in QuikQxs
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-PLANVALUES-003** — Plan Must Exist in QuikPlan
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-PLANVALUES-004** — Gender Must Be Default Zero or a Valid Gender Code
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-PLANVALUES-005** — Underwriting Class Must Be Default 00 or a Valid Class
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-PLANVALUES-006** — Band Must Be Default 00 or a Valid Band
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-PLANVALUES-007** — Issue State Must Be Default 00 or a Valid State Abbreviation
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-PLANVALUES-008** — Effective Date Must Be Within the Approved Date Range
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-001** — Plan Code Must Contain Six Characters
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-002** — Plan Code May Contain Only Letters and Numbers
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-003** — Plan Code May Not Use a Reserved PUA Suffix
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-004** — PAR Must Be 0 or 1
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-005** — Annuity Basis Must Match the Plan Type
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-006** — Loan Interest Option Must Be A or R
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-007** — MYGA Plans Must Have Positive Deposit Interest
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-008** — Issue Age Range Must Be Valid
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-009** — Renewal Setting Must Be Valid
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-010** — Payment Years and Payment Age Cannot Both Be Zero
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-011** — Insurance Years and Insurance Age Cannot Both Be Zero
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-012** — Single-Premium Plans Must Use Single-Premium Settings
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-013** — Payment Age May Not Exceed 125
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-014** — Insurance Age May Not Exceed 125
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-015** — Initial Value Must Use the Approved Default
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-016** — Commission ID Must Exist or Be Blank
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-017** — Maximum Units Must Not Be Below Minimum Units
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-018** — Rounding Rule Must Default to B
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-019** — Automatic NFO Must Default to 0
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-020** — Deficiency Must Be N for Alphabetic or 9-Series Plans
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-021** — Active Plan Status Must Use a Valid Logical Value
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-023** — MLAPSE Must Default to 0
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-024** — MNAICLOB Must Default to NAPLAN
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-025** — Gross Premium Supporting Tables Must Exist
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-026** — Death Benefit Supporting Tables Must Exist
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-027** — Traditional Plans Should Have Required Value Tables
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-028** — Annuity Plans Should Have Required Annuity Tables
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-029** — UL Plans Must Exist in QuikUint
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-030** — MEDS Plan Flags Must Match the Plan Type
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-031** — Rate and Key Table Plan Codes Must Exist in QuikPlan
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-032** — Company Codes Must Exist in Company Setup
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-033** — Conversion Dates Outside the Approved Range Must Be Warned
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).

## What This Governance Run Does Not Prove

This run:

- Validates only the currently registered and selected governance rules.
- Does not guarantee that all QLAdmin data is correct.
- Does not validate fields for which no rule has been created.
- Does not confirm actuarial calculations unless a specific actuarial rule exists.
- Does not confirm business intent beyond the rule definitions.
- Does not modify or repair source data.
- Does not replace user acceptance testing.
- Does not replace reconciliation to an authoritative source system.
- Does not confirm that an expected default is correct for every client unless the rule is configured as a universal standard.

A high Data Conformance Accuracy percentage means most evaluated records matched the active governance rules. It does not mean untested data is correct.
