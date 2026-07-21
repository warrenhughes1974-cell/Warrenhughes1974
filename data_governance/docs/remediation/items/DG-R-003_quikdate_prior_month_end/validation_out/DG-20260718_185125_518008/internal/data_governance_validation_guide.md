# QLAdmin Data Governance Validation Guide

This companion document explains exactly what the governance process validated in this specific run. It is generated from the registered rules that were selected and from the actual run results.

## Run Information

| | |
|---|---|
| Run ID | `DG-20260718_185125_518008` |
| Run date and time | July 18, 2026 at 6:51:25 PM |
| Data-region path | `Q:\CSO\CSO_Test_6_30_2026` |
| Output path | `c:\Users\warren\Documents\GitHub\Warrenhughes1974\data_governance\docs\remediation\items\DG-R-003_quikdate_prior_month_end\validation_out\DG-20260718_185125_518008` |
| Overall result | PASSED |
| Data Conformance Accuracy | 100.00% |
| Source opened read-only | Yes |
| Source files modified | No |

100.00% of the record checks completed without a governance exception.

## What This Run Did

This run reviewed the selected QLAdmin data region against the active governance rules listed below. It did not change any source data. Each rule checked a specific table, field, relationship, format, uniqueness requirement, or expected value.

## Tables Reviewed

- QuikDate

## Validation Rules Executed

## DG-QUIKDATE-001 — PAC Bill Date Must Be Set to the Previous Month End

**Governance item ID:** DG-QUIKDATE

**Technical name:** Validate QuikDate PAC Bill Prior Month End

**Purpose:**

Ensure the QuikDate PAC Bill date equals the final calendar day of the month immediately before the governance run date.

**Tables reviewed:**

- QuikDate

**Fields reviewed:**

- PACBILL

**Severity:** Critical

**Records reviewed:** 1

**Records that looked fine:** 1

**Problems found:** 0

**Result:** PASSED

**Exact validation performed:**

Verified field PACBILL (D). Decode the DBF date and compare calendar date only to the dynamically calculated prior-month-end date for the run date.

**Normalization / interpretation applied:**

Verified field PACBILL (D). Decode the DBF date and compare calendar date only to the dynamically calculated prior-month-end date for the run date.

**Conditions that pass:**

- Verified field PACBILL (D). Decode the DBF date and compare calendar date only to the dynamically calculated prior-month-end date for the run date.
- The record was available for evaluation.
- None of the listed failure conditions applied after normalization.

**Conditions that fail:**

- PACBILL is null or blank.
- PACBILL is invalid or unreadable.
- PACBILL is any valid date other than the calculated prior-month-end date.

**What this rule does not validate:**

- Whether values are factually or actuarially correct beyond this rule's checks.
- Fields on the same table that are not listed in this rule.
- Business intent that is not encoded in the rule definition.
- Whether missing reference data should be created automatically.

## DG-QUIKDATE-002 — Direct Bill Date Must Be Set to the Previous Month End

**Governance item ID:** DG-QUIKDATE

**Technical name:** Validate QuikDate Direct Bill Prior Month End

**Purpose:**

Ensure the QuikDate Direct Bill date equals the final calendar day of the month immediately before the governance run date.

**Tables reviewed:**

- QuikDate

**Fields reviewed:**

- DIRBILL

**Severity:** Critical

**Records reviewed:** 1

**Records that looked fine:** 1

**Problems found:** 0

**Result:** PASSED

**Exact validation performed:**

Verified field DIRBILL (D). Decode the DBF date and compare calendar date only to the dynamically calculated prior-month-end date for the run date.

**Normalization / interpretation applied:**

Verified field DIRBILL (D). Decode the DBF date and compare calendar date only to the dynamically calculated prior-month-end date for the run date.

**Conditions that pass:**

- Verified field DIRBILL (D). Decode the DBF date and compare calendar date only to the dynamically calculated prior-month-end date for the run date.
- The record was available for evaluation.
- None of the listed failure conditions applied after normalization.

**Conditions that fail:**

- DIRBILL is null or blank.
- DIRBILL is invalid or unreadable.
- DIRBILL is any valid date other than the calculated prior-month-end date.

**What this rule does not validate:**

- Whether values are factually or actuarially correct beyond this rule's checks.
- Fields on the same table that are not listed in this rule.
- Business intent that is not encoded in the rule definition.
- Whether missing reference data should be created automatically.

## DG-QUIKDATE-003 — Reinsurance Bill Date Must Be Set to the Previous Month End

**Governance item ID:** DG-QUIKDATE

**Technical name:** Validate QuikDate Reinsurance Bill Prior Month End

**Purpose:**

Ensure the QuikDate Reinsurance Bill date equals the final calendar day of the month immediately before the governance run date.

**Tables reviewed:**

- QuikDate

**Fields reviewed:**

- REINBILL

**Severity:** Critical

**Records reviewed:** 1

**Records that looked fine:** 1

**Problems found:** 0

**Result:** PASSED

**Exact validation performed:**

Verified field REINBILL (D). Business label: Reinsurance Bill. Decode the DBF date and compare calendar date only to the dynamically calculated prior-month-end date for the run date.

**Normalization / interpretation applied:**

Verified field REINBILL (D). Business label: Reinsurance Bill. Decode the DBF date and compare calendar date only to the dynamically calculated prior-month-end date for the run date.

**Conditions that pass:**

- Verified field REINBILL (D). Business label: Reinsurance Bill. Decode the DBF date and compare calendar date only to the dynamically calculated prior-month-end date for the run date.
- The record was available for evaluation.
- None of the listed failure conditions applied after normalization.

**Conditions that fail:**

- REINBILL is null or blank.
- REINBILL is invalid or unreadable.
- REINBILL is any valid date other than the calculated prior-month-end date.

**What this rule does not validate:**

- Whether values are factually or actuarially correct beyond this rule's checks.
- Fields on the same table that are not listed in this rule.
- Business intent that is not encoded in the rule definition.
- Whether missing reference data should be created automatically.

## DG-QUIKDATE-004 — ACH File ID Must Default to Zero

**Governance item ID:** DG-QUIKDATE

**Technical name:** Validate QuikDate ACHFILEID Default

**Purpose:**

Ensure QuikDate.ACHFILEID equals the business-supplied default 0.

**Tables reviewed:**

- QuikDate

**Fields reviewed:**

- ACHFILEID

**Severity:** Error

**Records reviewed:** 1

**Records that looked fine:** 1

**Problems found:** 0

**Result:** PASSED

**Exact validation performed:**

Verified field ACHFILEID N(1). Must decode to numeric zero. Null and blank are not treated as zero. Separate from ACHFILEID2.

**Normalization / interpretation applied:**

Verified field ACHFILEID N(1). Must decode to numeric zero. Null and blank are not treated as zero. Separate from ACHFILEID2.

**Conditions that pass:**

- Verified field ACHFILEID N(1). Must decode to numeric zero. Null and blank are not treated as zero. Separate from ACHFILEID2.
- The record was available for evaluation.
- None of the listed failure conditions applied after normalization.

**Conditions that fail:**

- ACHFILEID is null, blank, or unreadable.
- ACHFILEID contains a numeric value other than zero.

**What this rule does not validate:**

- Whether values are factually or actuarially correct beyond this rule's checks.
- Fields on the same table that are not listed in this rule.
- Business intent that is not encoded in the rule definition.
- Whether missing reference data should be created automatically.

## DG-QUIKDATE-005 — Secondary ACH File ID Must Default to A

**Governance item ID:** DG-QUIKDATE

**Technical name:** Validate QuikDate ACHFILEID2 Default

**Purpose:**

Ensure QuikDate.ACHFILEID2 equals the business-supplied default A.

**Tables reviewed:**

- QuikDate

**Fields reviewed:**

- ACHFILEID2

**Severity:** Error

**Records reviewed:** 1

**Records that looked fine:** 1

**Problems found:** 0

**Result:** PASSED

**Exact validation performed:**

Verified field ACHFILEID2 C(1). After trim and case normalization must equal 'A'. Separate from ACHFILEID.

**Normalization / interpretation applied:**

Verified field ACHFILEID2 C(1). After trim and case normalization must equal 'A'. Separate from ACHFILEID.

**Conditions that pass:**

- Verified field ACHFILEID2 C(1). After trim and case normalization must equal 'A'. Separate from ACHFILEID.
- The record was available for evaluation.
- None of the listed failure conditions applied after normalization.

**Conditions that fail:**

- ACHFILEID2 is null or blank.
- ACHFILEID2 contains any normalized value other than A.

**What this rule does not validate:**

- Whether values are factually or actuarially correct beyond this rule's checks.
- Fields on the same table that are not listed in this rule.
- Business intent that is not encoded in the rule definition.
- Whether missing reference data should be created automatically.

## DG-QUIKDATE-006 — ESCDATE Must Be Blank

**Governance item ID:** DG-QUIKDATE

**Technical name:** Validate QuikDate ESCDATE Blank

**Purpose:**

Ensure the QuikDate ESCDATE value is blank (physical field ESC_DATE).

**Tables reviewed:**

- QuikDate

**Fields reviewed:**

- ESC_DATE

**Severity:** Error

**Records reviewed:** 1

**Records that looked fine:** 1

**Problems found:** 0

**Result:** PASSED

**Exact validation performed:**

Verified physical field ESC_DATE (D) — business label ESCDATE. Passes when the value is a supported empty DBF date, null representing no date, or blank after trim. Populated dates fail.

**Normalization / interpretation applied:**

Verified physical field ESC_DATE (D) — business label ESCDATE. Passes when the value is a supported empty DBF date, null representing no date, or blank after trim. Populated dates fail.

**Conditions that pass:**

- Verified physical field ESC_DATE (D) — business label ESCDATE. Passes when the value is a supported empty DBF date, null representing no date, or blank after trim. Populated dates fail.
- The record was available for evaluation.
- None of the listed failure conditions applied after normalization.

**Conditions that fail:**

- ESC_DATE contains a populated date.
- ESC_DATE contains a nonblank character or unreadable nonblank value.

**What this rule does not validate:**

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
- **DG-PLANVALUES-001** — Mortality Table Must Exist in QuikQxs
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-PLANVALUES-002** — ETI Mortality Table Must Exist in QuikQxs
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
- **DG-QUIKPLAN-008** — Low Age Must Be Valid
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
- **DG-QUIKPLAN-022** — Closed Plans Cannot Use Plan Value Option
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-023** — MLAPSE Must Default to 0
  - Status: NOT SELECTED
  - Reason: Not selected for this run (full suite not requested, or a single governance item/rule filter was applied).
- **DG-QUIKPLAN-024** — MNAICLOB Must Default to N
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
