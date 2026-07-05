# Issue 30 — Planning Report

**Issue:** 30 — Policies with Missing Owner/Insured Names  
**Framework stage:** Planning Agent  
**Status:** Ready for Risk Review  
**Date:** 2026-07-05  
**Owner:** Conversion  

---

## Problem Statement

Converted policies can have blank `quikmstr.MPRIMID` and/or `quikmstr.MOWNRID` even though the LifePRO RNA source includes owner, insured, and payor relationship rows. The failure occurs when the RNA policy key is held in `IDENTIFYING_ALPHA` rather than `POLICY_NUMBER`.

---

## Source and Target Mapping

| Source | Target | Rule |
|---|---|---|
| `RelationshipNameAddress_Extract_20260530.csv.NAME_ID` | `quikclid.MCLIENTID`, `quikclnt.MCLIENTID` | Preserve LifePRO name ID |
| `RELATE_CODE=IN` | `quikclid.MRELATION`, `quikmstr.MPRIMID` | Emit as relationship and populate primary insured |
| `RELATE_CODE=PO` | `quikclid.MRELATION`, `quikmstr.MOWNRID` | Emit as relationship and populate owner |
| `RELATE_CODE=PA` | `quikclid.MRELATION`, `quikmstr.MPAYRID` | Emit as relationship and populate payor |
| `BENEFIT_SEQ_NUMBER` | `quikclid.MPHASE` | Default blank/0 to phase `1` |
| `POLICY_NUMBER` or `IDENTIFYING_ALPHA` | `quikclid.MPOLICY` | Prefer `POLICY_NUMBER`; when blank, derive policy from `IDENTIFYING_ALPHA` |

`IDENTIFYING_ALPHA` format observed for policy relationships: `03` + LifePRO policy number. Example: `039010150910` maps to LifePRO policy `9010150910`, then crosswalks to `010150910C`.

---

## Planned Fix

1. Add a small RNA policy-key resolver in the converter.
2. Use it when `quikclid.MPOLICY` would otherwise be blank.
3. Preserve existing `Master_Crosswalk.csv` behavior and Issue 25 MPOLICY formatting.
4. Deduplicate `quikclid` output by `MCLIENTID + MPOLICY + MPHASE + MRELATION`.
5. Add an Issue 30 validator that compares expected RNA roles from `IDENTIFYING_ALPHA` to emitted `quikclid`, `quikclnt`, and `quikmstr`.

---

## Explicit Non-Goals

- Do not infer relationships from policy master alone.
- Do not assign owners/insureds when RNA role rows are absent or blank.
- Do not change unrelated rulebook schemas or target field ordering.
- Do not alter Issue 25 MPOLICY padding or Issue 26 MPREM behavior.

---

## Open Questions

None blocking. The source extract needed for remediation is present in `QLA_Migration/Source/`.

---

## Planning Decision

**G1 — Planning complete:** PASS

Proceed to Dependency Gate.
