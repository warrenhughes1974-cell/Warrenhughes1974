# ISWL Source Data Discovery Report

**Analysis Date:** 2026-06-23

**Purpose:** Locate LifePRO source data for configuring QLAdmin ISWL plans

## A. Executive Summary

**Files Reviewed:** 3

**ISWL Plans Identified:** 0

### Data Found:

- Interest Values: ✓ Found (2 candidate sources)
- COI Factors: ✗ Not Found (0 candidate sources)
- Guaranteed COI: ✗ Not Found (0 candidate sources)
- Surrender Charges: ✗ Not Found (0 candidate sources)
- Gross Premiums: ✓ Found (1 candidate sources)
- Cash Values: ✗ Not Found (0 candidate sources)
- Expenses: ✗ Not Found (0 candidate sources)

### Assessment:

**Limited coverage** - Significant data gaps identified.

## B. Source-to-Target Mapping Matrix

| Requirement | QLAdmin Target | LifePRO Source | Candidate Fields | Dimensions | Confidence | Notes |
|------------|----------------|----------------|------------------|------------|------------|-------|
| Interest Values | QUIKUINT | PPBEN_PolicyBenefit_Extract_20260403.csv | JOINT_FLAG, FV_GUAR_RATE, UV_GUAR_COI_RATE | Unknown | Low |  |
| Expenses | N/A | NOT FOUND | - | - | N/A | Missing from available extracts |
| COI Factors | QUIKCOI | NOT FOUND | - | - | N/A | Missing from available extracts |
| Guaranteed COI | QUIKGCOI | NOT FOUND | - | - | N/A | Missing from available extracts |
| Surrender Charges | QUIKISSC | NOT FOUND | - | - | N/A | Missing from available extracts |
| Gross Premiums | QUIKGPS | iswl-prem.csv |  | age x duration matrix format | Low |  |
| Cash Values | QUIKCVS | NOT FOUND | - | - | N/A | Missing from available extracts |

## C. ISWL Plan Code Findings

**No explicit ISWL plan codes identified.**

*Recommendation: Request business to provide list of ISWL plan codes for targeted search.*

## D. Table-by-Table Findings

### Interest Values / QUIKUINT

**Source:** `PPBEN_PolicyBenefit_Extract_20260403.csv`


**Source:** `PPOLC_PolicyMaster_Extract_20260403.csv`


### Expenses

**Status:** Not found in available extracts

### COI / QUIKCOI

**Status:** Not found in available extracts

### Guaranteed COI / QUIKGCOI

**Status:** Not found in available extracts

### Surrender Charges / QUIKISSC

**Status:** Not found in available extracts

### Gross Premiums / QUIKGPS

**Source:** `iswl-prem.csv`

- Dimensions:
  - age x duration matrix format

### Cash Values / QUIKCVS

**Status:** Not found in available extracts

## E. Structural Uniformity Analysis

- Insufficient rate table variety found for structural comparison

## F. Data Gaps / Questions for Business

### **ISWL Plan Codes:** No ISWL plans explicitly identified - need business to provide plan code list

### **Expense Charges:** No expense charge data found - need monthly expense, % of premium fields

### **Guaranteed COI:** No guaranteed COI table found - separate from current COI?

### **Extract Completeness:** Current analysis limited by disk space - full LifePRO_Extracts_20260530.zip not extracted

### **Dimensional Consistency:** Need to verify UW class/band structures match across all ISWL rate tables

## G. Recommended Next Steps

1. **Extract Full LifePRO Package**
   - Clear disk space and extract complete `LifePRO_Extracts_20260530.zip`
   - Search for additional rate/value tables not yet reviewed

2. **Obtain ISWL Plan Code List**
   - Request business to provide definitive list of ISWL plan codes
   - Use plan codes to filter rate tables for ISWL-specific data

3. **Identify Interest Rate Source**
   - Locate LifePRO table/fields for guaranteed and current credited interest rates
   - Clarify if rates are plan-level, policy-level, or time-variant

4. **Locate Expense Charge Data**
   - Find monthly expense per policy
   - Find percent of premium expense
   - Find monthly expense per $1,000 if applicable

5. **Verify Guaranteed COI Structure**
   - Confirm if guaranteed COI is separate from current COI
   - Identify LifePRO table/TYPE_CODE for guaranteed COI

6. **Dimensional Uniformity Validation**
   - Once ISWL plans identified, extract all rate tables for those plans
   - Compare UW class, band, age, duration structures across:
     - COI
     - Guaranteed COI
     - Surrender charges
     - Gross premiums
     - Cash values
   - Document and resolve any structural mismatches before coding

7. **QLAdmin Schema Validation**
   - Confirm QLAdmin table structures for QUIKUINT, QUIKCOI, QUIKGCOI, QUIKISSC, QUIKGPS, QUIKCVS
   - Verify field mappings and data type requirements

## H. Files Reviewed

- `C:\Users\warren\Documents\GitHub\Warrenhughes1974\plan_analysis\source_data\rates\Rate_Table_Extract_20260427.csv`
- `C:\Users\warren\Documents\GitHub\Warrenhughes1974\plan_analysis\source_data\rates\PAAGERAT_AttainedAge_Rates_Extract_20260428.csv`
- `C:\Users\warren\Documents\GitHub\Warrenhughes1974\PFSA Rates\iswl-prem.csv`
