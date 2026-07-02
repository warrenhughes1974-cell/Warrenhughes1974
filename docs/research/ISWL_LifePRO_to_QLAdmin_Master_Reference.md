# ISWL LifePRO to QLAdmin Conversion Master Reference

## Purpose

This document combines:

1. The lead developer's QLAdmin implementation requirements for ISWL.
2. LifePRO product documentation research showing where these values should come from conceptually.
3. Cursor's May 2026 ZIP/source-data findings showing what actually exists in the source files.
4. Remaining gaps, blockers, and recommended next steps.

Important: Some ISWL product setup may already be implemented in the repo. Do not assume every item below is missing. Use this document as the ISWL conversion reference baseline. First compare current repo implementation against this reference, then identify only remaining gaps.

> **Update 2026-06-30 (Issue #31):** `PSEGT`, `PDINT`, and `PDINTTBL` extracts received in `QLA_Migration/Source/` (20260629). Segment hierarchy trace is now authoritative for PSEGT-mapped codes. See `docs/research/ISWL_Segment_Trace/ISWL_Segment_Trace_Addendum_20260629.md`.

---

# 1. Developer Requirement

The lead developer stated that the following values are needed to implement ISWL products in QLAdmin.

## 1.1 Interest Values

Needed:

* Guaranteed interest rate -> `QUIKUINT`
* Current credited interest rate -> `QUIKUINT`
* Credited rate on loan balance, if applicable

## 1.2 Expenses

Needed:

* Monthly expense per policy
* Percent of premium expense
* Monthly expense per $1,000, if applicable

## 1.3 COI Factors

Needed:

* Current cost of insurance amounts -> `QUIKCOI`

## 1.4 Guaranteed COI Factors

Needed:

* Guaranteed cost of insurance amounts -> `QUIKGCOI`

## 1.5 Surrender Charges

Needed:

* Surrender charge values -> `QUIKISSC`

## 1.6 Gross Premiums

Needed:

* Gross premium values -> `QUIKGPS`

## 1.7 Cash Values

Needed:

* Cash value values -> `QUIKCVS`

## 1.8 Developer Warning

Rates and values may vary by:

* Underwriting class
* Band
* Issue age
* Attained age
* Duration
* Sex
* Plan
* Coverage
* Segment
* Effective date

If rates vary by underwriting class and bands, the structure must be uniform across all applicable QLAdmin tables for each plan. This caused issues during PFSA, so ISWL must be validated up front.

---

# 2. Core LifePRO Product Model

ISWL conversion should not be driven only from policy-level rows like `PPBEN`.

LifePRO product setup should be reconstructed through the product hierarchy:

```text
PPRDF -> PCOMP -> PCOVR -> PCOVRSGT -> PSEGT -> rate tables
```

## 2.1 Primary LifePRO Product Setup Tables

```text
PPRDF      Product header
PCOMP      Component/coverage linkage
PCOVR      Coverage setup
PCOVRSGT   Coverage-to-segment attachment
PSEGT      Segment definitions
PDAGE      Age/duration rate table
PAAGE      Attained-age or issue-age rate header
PAAGERAT   Attained-age or issue-age rate detail
PDINT      Declared interest rate header
PDINTTBL   Declared interest rate detail
PMODE      Premium mode rules
```

## 2.2 Policy-Level Validation Tables

Use these as validation/evidence, not as first authority for product rates:

```text
PPBEN
PPBENTYP
PPRBNUL
PPRBN
PFNDR
PFNDA, if present
PFNDD, if present
PLOAN, if needed for loan-rate validation
```

---

# 3. May 2026 ZIP Source-Data Findings

Cursor analyzed:

```text
C:\Users\warren\Downloads\LifePRO_Extracts_20260530 (1).zip
```

The ZIP was streamed using Python `zipfile`; it was not fully extracted.

Key facts:

```text
Compressed size: approximately 1.49 GB
Uncompressed size: approximately 50.24 GB
File count: 125 files
Files not previously in repo: 113 of 125
```

This was the first full inventory and ISWL-target analysis of the complete May ZIP. Prior research had used April rate extracts and a May policy subset copied into `QLA_Migration/Source`, but not the entire ZIP.

## 3.1 Highest-Value New Sources

```text
PDAGE_AgeDuration_Rates_Extract_20260530.csv
- 203 MB
- 41,083 ISWL rows
- CV = 12,084 rows
- TP = 2,128 rows
- TX = 2,128 rows

PDDIC_DataDictionary_Extract_20260530.csv
- 112 MB
- Schema/metadata
- Contains COI/GCOI text but no provable TYPE_CODE lookup

PDDICFLD_DataDictionaryField_Extract_20260530.csv
- 55 MB
- Field definitions

PRBEN_BenefitRates_Extract_20260530.csv
- 47 MB
- Benefit-level rates

PRBENINT_BenefitRatesINT_Extract_20260530.csv
- 5 MB
- Interest-rate candidate for QUIKUINT

PAAGE_AttainedAge_Rates_Extract_20260530.csv
- 796 KB
- Attained-age rate headers
- 41 ISWL rows

PAAGERAT_AttainedAge_Rates_Extract_20260530.csv
- 24,425 total rows
- 3,287 ISWL rows
- Matches April PAAGERAT row counts

PPRDF_ProductInformation_Extract_20260530.csv
- Product-level setup
```

## 3.2 Critical Absence

The May ZIP does not contain `Rate_Table_Extract`.

Prior `QUIKCVS` research used April files:

```text
Rate_Table_Extract_20260427.csv
PAAGERAT_Extract_20260428.csv
```

Therefore, if the converter currently depends on `Rate_Table_Extract`, Cursor must determine whether:

```text
1. April Rate_Table remains the intended source for production CV work
or
2. May PDAGE CV should replace the old Rate_Table path
```

This requires parity validation and SME/business sign-off.

---

# 4. ISWL Product Universe Finding

Cursor found that user-requested MPLANs and coverages are not present in the proven ISWL fleet data:

```text
Requested MPLANs not found:
1668B1
1669B2
1678CS

Requested coverage IDs not found:
668 CEN I
678 CEN SEN
679 CEN SEN
```

Only eight proven ISWL coverage IDs appear in the actual source evidence.

Cursor must base implementation on proven source coverage IDs, not expected/requested coverage IDs unless the missing products are later supplied or clarified.

---

# 5. Target-by-Target Mapping and Findings

---

## 5.1 Cash Values

### QLAdmin Target

```text
QUIKCVS
```

### LifePRO Documentation Source Candidate

```text
CV = Cash Values Segment
PDAGE / PAAGE / PAAGERAT = rate/value tables
```

For UL/EIWL/ISWL, LifePRO may use tabular cash values as a guaranteed floor. Fund value less surrender charge should not fall below tabular cash value where a CV table applies.

### Cursor ZIP Finding

Strong source evidence exists in May `PDAGE`:

```text
PDAGE TYPE_CODE = CV
ISWL CV rows = 12,084
```

Cursor also noted that prior `QUIKCVS` research from April `Rate_Table` is strengthened because May `PDAGE` contains CV tables for all ISWL coverages.

Example:

```text
Coverage: 658 CEN I
Duration: 2
PDAGE CV values:
VALUE1 = 11.0
VALUE2 = 14.0
...
Interpretation: per-$1,000 cash values by band
```

### Confidence

```text
High confidence that CV source data exists.
Medium confidence on converter routing until April Rate_Table vs May PDAGE parity is validated.
```

### Current Concern

The May ZIP does not contain `Rate_Table_Extract`. If current converter logic expects `Rate_Table_Extract`, Cursor must either:

```text
1. Continue using the April Rate_Table source with explicit approval
or
2. Add/redirect CV loading to May PDAGE TYPE_CODE=CV after parity validation
```

### Required Cursor Action

```text
1. Inspect current QUIKCVS implementation.
2. Determine whether it uses Rate_Table_Extract or PDAGE.
3. Compare April Rate_Table CV values to May PDAGE CV values for ISWL.
4. Confirm row counts, durations, bands, coverages, and values.
5. Report whether PDAGE can replace Rate_Table for May production.
6. Do not change routing until parity and sign-off are documented.
```

---

## 5.2 Current COI Factors

### QLAdmin Target

```text
QUIKCOI
```

### LifePRO Documentation Source Candidate

```text
U6 = Current COI Rates Segment
PDAGE / PAAGE / PAAGERAT = possible rate sources
```

### Cursor ZIP Finding

Cursor found a candidate in `PAAGERAT`:

```text
PAAGERAT TYPE_CODE = NC
ISWL rows = 690
VALUE_INFO approximately 1.46 to 1.51
```

Sample:

```text
Coverage: 658 CEN I
TYPE_CODE: NC
VALUE_INFO: 1.4640000
Interpretation: attained-age COI factor candidate
```

### Confidence

```text
Medium confidence.
```

Reason: `NC = COI` is an inference only. The May `PDDIC` extracts did not provide an authoritative `TYPE_CODE` dictionary proving that `NC` means current COI.

### Important Validation Note

Prior findings showed:

```text
PPBEN.UV_CURR_COI_RATE = .00000 for all ISWL rows
```

Therefore, policy-level `PPBEN` COI fields are unusable as the source for current COI.

### Required Cursor Action

```text
1. Inspect PAAGE/PAAGERAT TYPE_CODE=NC rows for proven ISWL coverage IDs.
2. Determine rate shape:
   - coverage
   - age
   - duration, if any
   - sex
   - underwriting class
   - band
   - value scale
3. Compare against any U6 segment references in PCOVRSGT/PSEGT.
4. Determine whether the U6 segment points to NC rows or another source.
5. Flag NC as inferred until SME confirms TYPE_CODE meaning.
6. Do not emit final QUIKCOI from NC without SME confirmation or stronger source proof.
```

---

## 5.3 Guaranteed COI Factors

### QLAdmin Target

```text
QUIKGCOI
```

### LifePRO Documentation Source Candidate

```text
U5 = Guaranteed COI Rates Segment
PDAGE / PAAGE / PAAGERAT = possible rate sources
```

### Cursor ZIP Finding

Cursor found a candidate in `PAAGERAT`:

```text
PAAGERAT TYPE_CODE = U6
ISWL rows = 800
Appears only for:
658 CEN I
659 CEN II
```

### Confidence

```text
Medium confidence.
```

Reason: `U6 = guaranteed COI` is an inference only in this source-data analysis. It is also potentially confusing because LifePRO documentation uses segment `U6` for current COI, while Cursor found `TYPE_CODE=U6` as a candidate for guaranteed COI. These may not be the same concept.

### Important Validation Note

Prior findings showed:

```text
PPBEN.UV_GUAR_COI_RATE = .00000 for all ISWL rows
```

Therefore, policy-level `PPBEN` guaranteed COI fields are unusable as the source.

### Required Cursor Action

```text
1. Do not confuse LifePRO segment type U6 with rate table TYPE_CODE=U6.
2. Inspect PSEGT/PCOVRSGT for U5 guaranteed COI segment references.
3. Determine what rate table/type those U5 segments point to.
4. Compare that linkage to PAAGERAT TYPE_CODE=U6.
5. Validate whether TYPE_CODE=U6 is truly guaranteed COI.
6. Flag as blocked until TYPE_CODE dictionary or SME confirmation is received.
```

---

## 5.4 Gross Premiums

### QLAdmin Target

```text
QUIKGPS
```

### LifePRO Documentation Source Candidates

```text
PR = Premium Segment
GP = Guaranteed Premiums Segment
UG = Universal Life Minimum Premium Segment
UH = Universal Life Target Premium Rates Segment
UX = Minimum Premium Assembly Rules
UY = Target Premium Assembly Rules
UZ = Guideline Premium Rules
MP = Minimum Premium Factors Segment
PMODE = Premium Mode Rules
```

### Cursor ZIP Finding

Cursor found:

```text
PAAGERAT TYPE_CODE = BP
ISWL rows = 1,164
```

Cursor also confirmed:

```text
Rate_Table PR has zero ISWL rows
PAAGERAT PR has zero ISWL rows
PDAGE PR has zero ISWL rows
```

Therefore, `PR` is disproven as the gross-premium source for ISWL in this data set.

### Confidence

```text
Medium confidence for BP as gross premium candidate.
Low/none for PR as ISWL gross premium source.
```

Reason: `BP = gross premium` is inferred, not proven. Need TYPE_CODE reference or segment linkage.

### Required Cursor Action

```text
1. Do not use PR as the ISWL gross-premium source unless new evidence appears.
2. Inspect PAAGERAT TYPE_CODE=BP by ISWL coverage.
3. Determine whether BP rows match expected gross premium dimensions.
4. Trace premium-related segments in PCOVRSGT/PSEGT:
   - PR
   - GP
   - UG
   - UH
   - UX
   - UY
   - UZ
   - MP
5. Determine whether any segment points to BP.
6. Validate against policy-level premium fields:
   - PPBEN.ANN_PREM_PER_UNIT
   - PPBEN.MODE_PREMIUM
   - PPRBNUL.ANN_PREM
   - PPRBNUL.GUAR_ANN_PREM
   - PPRBNUL.BILL_PREM_ANNUAL
   - PPRBNUL.BILL_PREM_MODAL
7. Flag BP as inferred until confirmed by TYPE_CODE dictionary, segment linkage, or SME.
```

---

## 5.5 Interest Values

### QLAdmin Target

```text
QUIKUINT
```

### LifePRO Documentation Source Candidates

```text
A1 = Current Interest Rate Segment
G1 = Guaranteed Interest Rate Segment
LN = Loan Interest Rates Segment, if applicable
PDINT / PDINTTBL = Declared Interest Rate tables
PRBENINT = BenefitRatesINT, possible interest-rate candidate
PPBEN.FV_GUAR_RATE = policy-level guarantee evidence
```

### Cursor ZIP Finding

Cursor found:

```text
PPBEN.FV_GUAR_RATE = 4.50 for 2,159 ISWL rows
PRBENINT exists and is a candidate for QUIKUINT
CSO crosswalk also supports 4.50% guarantee
```

Cursor also found:

```text
QUIKUINT field mapping remains unknown.
```

### Confidence

```text
Supported for guaranteed interest rate = 4.50%.
Unknown for exact QUIKUINT column mapping.
Unknown for current credited rate.
Unknown for loan credited/charged rate.
```

### Required Cursor Action

```text
1. Inspect PRBENINT for ISWL-related rows.
2. Inspect PCOVRSGT/PSEGT for A1, G1, and LN segments.
3. Determine whether interest values are stored as:
   - constant values in PSEGT
   - declared interest table pointers
   - PRBENINT rows
   - policy-level PPBEN evidence only
4. Map guaranteed rate separately from current credited rate.
5. Search for loan-rate behavior using LN, PLOAN, PFNDD.LOAN_INTEREST_RATE, or related loan setup tables.
6. Do not finalize QUIKUINT until the QLAdmin QUIKUINT schema/field mapping is confirmed.
```

---

## 5.6 Surrender Charges

### QLAdmin Target

```text
QUIKISSC
```

### LifePRO Documentation Preferred Source Path

```text
SR = Full Surrender Segment
SL = Full Surrender Load Segment
```

### LifePRO Fallback/Older Source Path

```text
U7 = Full Surrender Load / Fees
U8 = Full Surrender Load / Percentages
SA = Full Surrender Amortization
U4 = Rate Amortization
```

LifePRO documentation indicates that `U7` and `U8` are older original-monthaversary segments and were replaced by `SL` through the `SR` segment.

### Cursor ZIP Finding

Cursor found new possible candidates:

```text
PDAGE TYPE_CODE = TP
ISWL rows = 2,128

PDAGE TYPE_CODE = TX
ISWL rows = 2,128
```

### Confidence

```text
Low confidence.
```

Reason: `TP`/`TX` as surrender charge source is inference only. There is no authoritative TYPE_CODE dictionary proving this.

### Required Cursor Action

```text
1. Inspect PCOVRSGT/PSEGT for SR and SL segment references.
2. If SR/SL exists, treat that as preferred surrender source path.
3. If no SR/SL exists, inspect U7/U8/SA/U4.
4. Compare any discovered segment linkage to PDAGE TYPE_CODE=TP/TX.
5. Validate against policy-level fields:
   - PPBENTYP.BF_CURR_SURR_LOAD
   - PPRBNUL.SURR_LOAD
   - PPRBNUL.LAPSE_SURR_LOAD
   - PFNDD.SURRENDER_LOAD
6. Do not emit QUIKISSC from TP/TX without TYPE_CODE confirmation or clear segment linkage.
```

---

## 5.7 Expenses

### QLAdmin Target

Use existing QLAdmin product/rulebook pattern for:

```text
Monthly policy/admin fee
Percent premium load
Per-thousand expense load
```

### LifePRO Documentation Source Candidates

```text
UF = Per Policy Monthly Expense
U1 = Premium Collection Expense / Fee
U2 = Premium Collection Expense / Percentage of Premium
U3 = Per Thousand Expense Load
PCOVR.POLICY_FEE = possible policy fee candidate
PCOMP = possible component-level setup candidate
```

### Cursor ZIP Finding

Cursor found:

```text
No expense rate tables located.
Expenses remain unknown.
Possible candidates:
- PCOVR.POLICY_FEE
- PCOMP
```

### Confidence

```text
Unknown.
```

### Required Cursor Action

```text
1. Inspect PCOVR for POLICY_FEE or similar fields for proven ISWL coverages.
2. Inspect PCOMP for component-level fees or expense values.
3. Inspect PCOVRSGT/PSEGT for UF, U1, U2, and U3 segments.
4. If UF/U1/U2/U3 are absent, report that LifePRO source does not appear to provide explicit ISWL expense tables in this extract.
5. Request SME/client confirmation for:
   - monthly expense per policy
   - percent of premium load
   - per-$1,000 expense load
6. Do not infer expenses from policy premium or fund values.
```

---

# 6. Source-Data Confidence Summary

```text
QUIKCVS
Candidate source: PDAGE TYPE_CODE=CV
Evidence: 12,084 ISWL CV rows
Confidence: High for data existence; Medium for converter routing

QUIKCOI
Candidate source: PAAGERAT TYPE_CODE=NC
Evidence: 690 ISWL rows
Confidence: Medium; TYPE_CODE meaning unproven

QUIKGCOI
Candidate source: PAAGERAT TYPE_CODE=U6
Evidence: 800 ISWL rows for 658 CEN I and 659 CEN II only
Confidence: Medium; TYPE_CODE meaning unproven

QUIKGPS
Candidate source: PAAGERAT TYPE_CODE=BP
Evidence: 1,164 ISWL rows; PR has zero ISWL rows
Confidence: Medium; BP meaning inferred

QUIKUINT
Candidate source: PPBEN.FV_GUAR_RATE, PRBENINT, CSO crosswalk
Evidence: 2,159 ISWL rows with FV_GUAR_RATE = 4.50
Confidence: Supported for guaranteed rate; mapping still unknown

QUIKISSC
Candidate source: PDAGE TYPE_CODE=TP/TX
Evidence: 2,128 ISWL rows each
Confidence: Low; inference only

Expenses
Candidate source: PCOVR.POLICY_FEE, PCOMP, UF/U1/U2/U3 if present
Evidence: no expense rate tables located
Confidence: Unknown
```

---

# 7. Major Blockers / Open Items

## 7.1 Missing Authoritative TYPE_CODE Dictionary

The biggest blocker is that the May ZIP source analysis did not find a provable `TYPE_CODE` dictionary for:

```text
NC
U6
BP
TP
TX
```

Current inferences:

```text
NC = possible current COI
U6 = possible guaranteed COI rate table code
BP = possible gross premium
TP/TX = possible surrender charges
```

These must be confirmed through:

```text
LifePRO TYPE_CODE reference table
SME confirmation
or clear segment linkage from PCOVRSGT/PSEGT into rate tables
```

## 7.2 May ZIP Missing Rate_Table_Extract

The May ZIP does not include `Rate_Table_Extract`.

This creates a decision point for `QUIKCVS`:

```text
Use April Rate_Table source
or
Use May PDAGE TYPE_CODE=CV
```

Must perform parity validation before changing production routing.

## 7.3 QUIKUINT Mapping Unknown

The source supports a 4.50% guaranteed rate, but exact QLAdmin `QUIKUINT` field mapping remains unknown.

Need QLAdmin table/field spec for:

```text
guaranteed interest rate
current credited interest rate
loan credited/charged rate
effective dates
plan/coverage keys
```

## 7.4 Expenses Unknown

No explicit ISWL expense rate table was found. Need to inspect:

```text
PCOVR.POLICY_FEE
PCOMP
UF/U1/U2/U3 segments
```

If still missing, request client/SME confirmation.

## 7.5 Missing Requested MPLANs/Coverage IDs

The source evidence did not contain:

```text
MPLANs:
1668B1
1669B2
1678CS

Coverage IDs:
668 CEN I
678 CEN SEN
679 CEN SEN
```

Need client/SME clarification if those are expected in ISWL.

---

# 8. Required Rate-Shape Audit

Before emitting or modifying final QLAdmin ISWL product/rate output, create an audit by ISWL plan/coverage and table family.

Audit these segment/type families:

```text
A1 / G1 / LN
UF / U1 / U2 / U3
U5
U6
SR / SL / U7 / U8
PR / GP / UG / UH / UX / UY / UZ / MP
CV
PDAGE CV
PDAGE TP/TX
PAAGERAT NC
PAAGERAT U6
PAAGERAT BP
PRBENINT
```

For each family, report:

```text
Product ID
Product description
Component number
Component type
Coverage ID
Coverage description
Segment type
Segment ID
Key modifier
Constant vs rate-file source
Rate table source:
  PDAGE
  PAAGE/PAAGERAT
  PDINT/PDINTTBL
  PRBENINT
  PSEGT constant
TYPE_CODE, if applicable
Sex values present
UW classes present
Bands present
Ages present
Durations present
Monthly vs annual coding
Source row count
Output table target
Output row count, if already implemented
Missing structures
Mismatched structures
Assumptions
Business decisions needed
```

Purpose: catch cases where one table varies by underwriting class/band/duration but another table for the same plan does not.

---

# 9. Implementation Recommendation

Do not begin by rewriting product setup.

First perform a gap assessment against the current repo.

## 9.1 Required Gap Assessment

For each area, classify current state:

```text
Interest values -> QUIKUINT
Expenses
Current COI -> QUIKCOI
Guaranteed COI -> QUIKGCOI
Surrender charges -> QUIKISSC
Gross premiums -> QUIKGPS
Cash values -> QUIKCVS
```

For each area, report:

```text
Current implementation found or not found
Source tables currently read
Source tables that should be read
Existing output files/tables affected
Whether ISWL products are included
Whether dimensions are preserved:
  plan
  coverage
  sex
  UW class
  band
  age
  duration
Validation gaps
Recommended next step
Code change needed? Yes/No
Business decision needed? Yes/No
SME confirmation needed? Yes/No
```

## 9.2 Do Not Proceed Without Confirmation For

Do not emit final loaders for these until TYPE_CODE meanings or segment linkages are proven:

```text
QUIKCOI from PAAGERAT TYPE_CODE=NC
QUIKGCOI from PAAGERAT TYPE_CODE=U6
QUIKGPS from PAAGERAT TYPE_CODE=BP
QUIKISSC from PDAGE TYPE_CODE=TP/TX
```

## 9.3 May Proceed With Caution

May proceed with analysis/validation, not necessarily production emission, for:

```text
QUIKCVS from PDAGE TYPE_CODE=CV
- Requires parity validation against April Rate_Table CV

QUIKUINT guaranteed rate = 4.50%
- Supported by PPBEN.FV_GUAR_RATE rows and CSO crosswalk
- Requires QLAdmin QUIKUINT field mapping
```

---

# 10. Questions to Request from Client / SME

Ask for the following:

```text
1. LifePRO TYPE_CODE reference table:
   What do NC, U6, BP, TP, and TX mean for UL/ISWL?

2. Confirmation whether May PDAGE TYPE_CODE=CV replaces the prior April Rate_Table CV source.

3. Authoritative surrender charge source or TYPE_CODE for ISWL.

4. Expense/fee setup location:
   - monthly policy/admin charge
   - percent premium load
   - per-$1,000 monthly expense

5. QLAdmin QUIKUINT field mapping:
   - guaranteed interest
   - current credited interest
   - loan credited/charged interest
   - effective-date handling

6. Clarification why Rate_Table_Extract was omitted from the May ZIP.

7. Clarification why requested MPLANs/coverages are not present:
   - 1668B1
   - 1669B2
   - 1678CS
   - 668 CEN I
   - 678 CEN SEN
   - 679 CEN SEN
```

---

# 11. Next Cursor Task

Use this document as the ISWL master reference.

Do not code yet.

First inspect the repo and produce a gap report showing what is already implemented and what remains.

Use this report format:

```text
Area:
Current state:
Source evidence:
QLAdmin target:
Implemented already?
Current source table used:
Expected source table:
Dimensions preserved?
Validation gap:
TYPE_CODE confirmed?
SME confirmation needed?
Recommended next action:
Code change needed? Yes/No
Business decision needed? Yes/No
```

Cover these areas:

```text
1. Interest values -> QUIKUINT
2. Expenses
3. Current COI -> QUIKCOI
4. Guaranteed COI -> QUIKGCOI
5. Surrender charges -> QUIKISSC
6. Gross premiums -> QUIKGPS
7. Cash values -> QUIKCVS
```

No code changes until the gap report is reviewed.

---

## Related Research Artifacts

| Document | Path |
|----------|------|
| May ZIP executive summary | `docs/research/ISWL_Zip_Research_Executive_Summary_20260530.md` |
| Prior finding revalidation | `docs/research/iswl_zip_prior_finding_revalidation_20260530.md` |
| Target source analysis | `docs/research/iswl_zip_target_source_analysis_20260530.md` |
| Forensic audit | `Issue_Log_Items/Issue_ISWL_Research/ISWL_Forensic_Audit_Trail.md` |
| Source discovery | `Issue_Log_Items/Issue_ISWL_Research/ISWL_Source_Discovery_Report.md` |
| ZIP analysis script | `tools/research/iswl_zip_source_analysis_20260530.py` |
