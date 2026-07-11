# Issue 21F — Tracking Sheet

| Field | Value |
|---|---|
| Issue | **21F** Truncated Premium History |
| Status | **CLOSED** — Ready for Client UAT (v57.73) |
| Resolution | Non-ISWL policies receive one additive Conversion Adjustment `quikprmh` row dated 12/31/2017 (`MSOURCE=CONV_ADJ`) when LifePRO Base+PUA+SU+SL total exceeds converted payment history; ISWL excluded; negatives in exception report only (v57.73). |
| Phase | 3 |
| Risk | Medium (large additive volume; bounded rules) |
| Owner | Conversion |
| Business confirm | Eric (all 7 items AGREED) |
| Engine | v57.73 |
| Closed | 2026-07-11 |

## Locked decisions (short)

1. Single conversion adjustment when LifePRO total > `quikprmh` sum  
2. LifePRO total = Base + PUA + Supplemental + Substandard  
3. Date = **12/31/2017**  
4. Classify as **Conversion Adjustment**  
5. Negatives → exception report only (no load)  
6. **Exclude ISWL** from phase 1  
7. Validation report required  

## Artifacts

| Doc | Path |
|---|---|
| Business decisions | `Issue_21F_Business_Decisions.md` |
| Intake | `Issue_21F_Intake_Summary.md` |
| Planning | `Issue_21F_Planning_Report.md` |
| Dependency Gate | `Issue_21F_Dependency_Gate.md` (**PASS**) |
| Risk Review | `Issue_21F_Risk_Review_Report.md` (**CONDITIONAL GO**) |
| Development Authorization | `Issue_21F_Development_Authorization.md` (**APPROVED**) |
| Development Report | `Issue_21F_Development_Report.md` (**IMPLEMENTED v57.72**; fix pass **v57.73**) |
| Implementation Notes | `Issue_21F_Implementation_Notes.md` |
| Validation Report | `Issue_21F_Validation_Report.md` (**PASS v57.73**) |
| Regression Report | `Issue_21F_Regression_Report.md` (**PASS v57.73**) |
| Resolution Summary | `Issue_21F_Resolution_Summary.md` (**CLOSED**) |

## Example

010310404C: LifePRO $17,040.05 − history $1,846.20 = adjustment **$15,193.85**

## UAT package

- `QLA_Migration/Output/Test_Validation/quikprmh.csv`
- `QLA_Migration/Reports/issue21f_premium_adjustment_validation.csv`
- `QLA_Migration/Reports/issue21f_premium_adjustment_exceptions.csv`
