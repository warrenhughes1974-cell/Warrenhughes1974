# Issue 30 — Intake Summary

**Issue:** 30 — Policies with Missing Owner/Insured Names  
**Framework stage:** Intake Agent  
**Status:** Planning  
**Date:** 2026-07-05  
**Owner:** Conversion  

---

## Client Report

A small population of converted policies shows blank or comma-only owner and/or insured names. Earlier Issue 30 analysis classified the population as missing LifePRO RNA relationship source data, but client review indicates relationship rows are visible in LifePRO for the affected policies. Policy `010150910C` was provided as a trace example.

---

## Initial Evidence

The prior report in `Issue_30_Missing_Name_Report.md` stated that affected policies lacked `IN` and/or `PO` rows in RNA. Re-examination against `QLA_Migration/Source/RelationshipNameAddress_Extract_20260530.csv` found the relationships are present but keyed by `IDENTIFYING_ALPHA`, while `POLICY_NUMBER` is blank.

Trace for `010150910C`:

| Field | Value |
|---|---|
| Converted policy | `010150910C` |
| LifePRO policy | `9010150910` |
| RNA identifying alpha | `039010150910` |
| Source `IN` | `NAME_ID=590268` |
| Source `PO` | `NAME_ID=590268` |
| Source `PA` | `NAME_ID=590268` |
| Source name | `HAROLD SWANSON` |
| Current `quikmstr.MPRIMID` | blank |
| Current `quikmstr.MOWNRID` | blank |

---

## Affected Population

The prior Issue 30 population remains the starting scope: 18 policies listed in `Issue_30_Missing_Name_Policies.csv`.

The recheck found source RNA relationship rows for all 18 when matching through `IDENTIFYING_ALPHA` instead of `POLICY_NUMBER`.

---

## Intake Decision

**G0 — Intake complete:** PASS

Proceed to Planning. The issue is no longer a pure client-data blocker; it is a controlled converter remediation for RNA policy-key derivation and relationship dedupe.
