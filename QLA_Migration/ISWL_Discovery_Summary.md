# ISWL Source Data Discovery - Executive Summary

**Date:** June 23, 2026  
**Analyst:** AI Discovery Tool  
**Purpose:** Locate LifePRO ISWL rate/value data for QLAdmin configuration

---

## Files Reviewed

1. **Rate_Table_Extract_20260427.csv** (50K rows sampled)
   - Contains rate data with TYPE_CODE classifications
   - Dimensions: COVERAGE_ID, TYPE_CODE, AGE, SEX, BAND, UNDERWRITING_CLASS, DURATION, VALUE
   - TYPE_CODE values found:
     - `CV` (Cash Value) - 7,110 rows
     - `NN`, `PN`, `NP` (likely Net/Premium variants) - 34,594 rows
     - `RV` (Reserve Value?) - 4,740 rows  
     - `DB` (Death Benefit?) - 3,555 rows
   - **Assessment:** Contains some rate data but lacks explicit COI, Surrender Charge, GCOI codes

2. **PAAGERAT_AttainedAge_Rates_Extract_20260428.csv** (24K rows sampled)
   - Attained-age-based rating structure
   - TYPE_CODE values: PR, PU, CV, BP, NP, RV, U6, NC, DB, NF, U5, YP, RD
   - Sample plans: 0822 620, 0823 665, 687J 30MRG, 667 ART CR, 619 DT, 630 JEB, etc.
   - **Assessment:** Primarily premium-focused; no clear ISWL identifiers

3. **iswl-prem.csv** (PFSA Rates folder)
   - Custom matrix format: rows = durations, columns = ages
   - Plan code: `MSP B2`
   - **Assessment:** Modal premium table for ISWL, but custom format requires parsing

4. **PPBEN_PolicyBenefit_Extract_20260403.csv** (headers only)
   - Contains interest rate fields: `FV_GUAR_RATE`, `UV_GUAR_COI_RATE`, `UV_CURR_COI_RATE`
   - **Assessment:** Potential source for QUIKUINT interest values

5. **PPOLC_PolicyMaster_Extract_20260403.csv** (headers only)
   - Contains: `WITHDRAW_INT_FLAG`
   - **Assessment:** Policy-level interest flag, limited utility for rate tables

---

## Findings by QLAdmin Target

| QLAdmin Table | Data Found | Source | Confidence | Notes |
|--------------|-----------|---------|-----------|-------|
| **QUIKUINT** | ✓ Partial | PPBEN (FV_GUAR_RATE, UV_GUAR_COI_RATE, UV_CURR_COI_RATE) | **Medium** | Fields exist; need to verify they map to guaranteed/current credited interest |
| **QUIKCOI** | ✗ Not Found | - | **N/A** | No explicit COI TYPE_CODE in available extracts |
| **QUIKGCOI** | ✗ Not Found | - | **N/A** | No guaranteed COI table identified |
| **QUIKISSC** | ✗ Not Found | - | **N/A** | No surrender charge TYPE_CODE found |
| **QUIKGPS** | ✓ Partial | iswl-prem.csv | **Low** | Custom format; needs parsing; only 1 plan code (MSP B2) |
| **QUIKCVS** | ? Possible | Rate_Table_Extract (CV TYPE_CODE) | **Medium** | 7,110 CV rows exist; need to verify ISWL plan coverage |
| **Expenses** | ✗ Not Found | - | **N/A** | No expense charge fields identified |

---

## Critical Data Gaps

### 1. **ISWL Plan Codes Not Identified**
   - **Issue:** No explicit "ISWL" keyword found in COVERAGE_ID values
   - **Impact:** Cannot filter rate tables for ISWL-specific data
   - **Action Required:** Business must provide definitive ISWL plan code list

### 2. **Missing Core Rate Tables**
   - **COI Factors (QUIKCOI):** Not found in available TYPE_CODE values
   - **Guaranteed COI (QUIKGCOI):** No separate GCOI table identified
   - **Surrender Charges (QUIKISSC):** No SC or SUR TYPE_CODE found
   - **Impact:** Cannot build complete QLAdmin ISWL rate structure
   - **Action Required:** Extract full LifePRO_Extracts_20260530.zip (disk space issue prevented full extraction)

### 3. **Expense Charge Data Missing**
   - **Required:** Monthly expense per policy, % of premium expense, monthly expense per $1,000
   - **Impact:** Incomplete QLAdmin plan setup
   - **Action Required:** Identify LifePRO expense table/fields

### 4. **Dimensional Structure Unknown**
   - **Issue:** Cannot validate uniformity across rate tables (COI vs. SC vs. CV vs. GP)
   - **Impact:** May encounter UW class/band/age/duration mismatches during import
   - **Action Required:** Once ISWL plans identified, extract all rate tables and compare dimensions

### 5. **Extract Completeness**
   - **Issue:** Full LifePRO_Extracts_20260530.zip not extracted due to disk space
   - **Impact:** Missing potentially critical rate/value tables
   - **Action Required:** Clear disk space, extract complete package, re-run discovery

---

## TYPE_CODE Interpretation (Hypotheses)

Based on limited evidence, possible meanings:

| TYPE_CODE | Likely Meaning | Evidence |
|-----------|---------------|---------|
| CV | Cash Value | Found 7,110 rows; standard UL/ISWL component |
| PR | Premium Rate | 14,958 rows in attained-age extract |
| COI / CI | Cost of Insurance | **NOT FOUND** - may use different code (NC? U6?) |
| SC / SUR | Surrender Charge | **NOT FOUND** |
| GCOI | Guaranteed COI | **NOT FOUND** |
| DB | Death Benefit | 3,555 rows; likely not a rate table input |
| RV | Reserve Value | 4,740 rows; actuarial reserve, not QLAdmin input |
| NN, PN, NP | Net/Premium variants | 34K+ rows; unclear purpose |

**Recommendation:** Request LifePRO data dictionary or TYPE_CODE legend from source system team.

---

## Recommended Actions (Priority Order)

### **IMMEDIATE (Before Coding)**

1. **Obtain ISWL Plan Code List**
   - Request from business/actuarial
   - Required to filter all rate extracts for ISWL data

2. **Extract Full LifePRO Package**
   - Clear disk space (need ~5-10 GB estimate)
   - Extract complete LifePRO_Extracts_20260530.zip
   - Re-run discovery tool: `python QLA_Migration/discovery_iswl_analysis.py`

3. **Request LifePRO Data Dictionary**
   - TYPE_CODE legend (what is COI? what is SC? etc.)
   - Field definitions for PPBEN interest rate fields
   - Expense charge table/field locations

### **HIGH (Validation Phase)**

4. **Verify Interest Rate Mapping**
   - Confirm `FV_GUAR_RATE` → guaranteed interest rate (QUIKUINT)
   - Confirm `UV_CURR_COI_RATE` → current credited interest rate (QUIKUINT)
   - Clarify loan interest rate source

5. **Identify Missing Core Tables**
   - Locate COI factor source (QUIKCOI target)
   - Locate guaranteed COI source (QUIKGCOI target)
   - Locate surrender charge source (QUIKISSC target)
   - Locate expense charge source

6. **Validate Dimensional Uniformity**
   - Once ISWL plans identified, extract:
     - All COI rows
     - All GCOI rows
     - All SC rows
     - All CV rows
     - All GP rows
   - Compare UW class, band, age ranges, duration ranges
   - Document mismatches (e.g., COI has 5 UW classes but SC has 3)

### **MEDIUM (Development Phase)**

7. **Confirm QLAdmin Table Schemas**
   - QUIKUINT structure and field requirements
   - QUIKCOI structure and field requirements
   - QUIKGCOI structure and field requirements
   - QUIKISSC structure and field requirements
   - QUIKGPS structure and field requirements
   - QUIKCVS structure and field requirements

8. **Design Rate Loader Logic**
   - How to handle custom formats (e.g., iswl-prem.csv matrix)
   - Dimensional mismatch resolution strategy
   - Missing rate value handling (default? error? skip?)

---

## Questions for Business / IT

1. **What are the ISWL plan codes in LifePRO?** (e.g., is "MSP B2" an ISWL plan?)
2. **What TYPE_CODE represents Cost of Insurance (COI)?** (NC? U6? CI? other?)
3. **What TYPE_CODE represents Surrender Charges?** (SC? SUR? other?)
4. **Is guaranteed COI stored separately from current COI in LifePRO?**
5. **Where are expense charges stored in LifePRO?** (table? fields? plan-level? policy-level?)
6. **Are the rate structures uniform across all ISWL plans?** (same UW classes? same bands? same age/duration ranges?)
7. **Do we have a LifePRO data dictionary or field mapping document?**

---

## Discovery Tool Artifacts

- **Primary Report:** `QLA_Migration/ISWL_Source_Data_Discovery_Report.md`
- **Discovery Script:** `QLA_Migration/discovery_iswl_analysis.py` (analysis only, not production)
- **This Summary:** `QLA_Migration/ISWL_Discovery_Summary.md`

---

## Next Meeting Prep

**Bring to next stakeholder meeting:**
1. ISWL plan code list
2. LifePRO TYPE_CODE legend
3. Confirmation on disk space clearance for full extract
4. Decision on how to handle missing guaranteed COI (use current COI? skip? error?)
5. Expense charge data location

**DO NOT PROCEED WITH CODING** until at minimum items 1-3 are resolved.

---

*End of Summary*
