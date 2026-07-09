# Issue #41 — Intake Summary

**Issue:** #41 — CV Age/Duration Endpoint Off by One  
**Date:** 2026-07-06  
**Framework stage:** Intake complete (G0)  
**Status:** Approved -> Planning  
**Owner:** Conversion (Warren) · **Business status:** No-Go for Development until dependency gate confirms target duration convention

---

## Client / business symptom

Client reports that **Age/Duration cash value rates are still one duration early** in QLAdmin after the prior CV placement fix.

Reported example:

| Field | Value |
|-------|-------|
| LifePRO product / plan | `960 PO` / QLAdmin `1960PO` |
| Rate type | `CV` cash value |
| Sex | Male |
| Issue age | `26` |
| Band | `01` |
| UW class | `00` |
| Client-observed value | `784.65` |
| LifePRO placement | Duration **57** |
| QLAdmin placement | Duration **56** |

The client also notes the visible endpoint problem: **rates are ending at age 99 in QLAdmin instead of age 100**. Other issue ages show the same pattern.

---

## Normalized finding

This is not a rate-value mismatch. The numeric sequence appears to be the same sequence, but the **QLAdmin duration index / terminal duration is one year short**.

Issue #37 corrected a previous CV duration placement defect by rebuilding LifePRO-style CV grids and truncating each issue-age slice at:

```text
last_duration = 100 - issue_age
```

The new client evidence indicates the QLAdmin target must include the **age-100 endpoint**, meaning the final displayed QLAdmin duration should be inclusive of age 100. For issue age `26`, the current grid stops one duration too soon, causing late-duration values to display under the prior duration and leaving the table ending at age 99.

---

## Current suspected root cause

**Category:** Follow-up defect from Issue #37 endpoint rule

The Issue #37 implementation intentionally used a fleet CV maturity rule of `100 - issue_age`. That was approved from the original proof matrix, but the client's new screenshots show that QLAdmin's visible duration convention requires one additional terminal duration for age-100 parity.

Likely correction direction:

1. Preserve the Issue #37 LifePRO grid alignment and leading-zero handling.
2. Re-evaluate only the **CV terminal duration / QLAdmin display-duration convention**.
3. Change the maturity endpoint from an age-99 effective endpoint to an **age-100 inclusive endpoint**, if confirmed by Dependency Gate.

Do **not** treat this as a new source-rate extraction issue unless validation proves source rows are missing.

---

## Relationship to existing issues

| Issue | Relationship |
|-------|--------------|
| **#37** | Direct predecessor. Fixed CV duration placement but used `last_duration = 100 - issue_age`; Issue #41 challenges that endpoint rule. |
| **#40** | Separate missing inherited-CV load issue for plans such as `17085M`; Issue #41 applies to CV rows that already exist, including `1960PO`. |
| **#31** | QuikCvs / ISWL regression baseline must be rechecked if CV grid endpoint changes. |
| **#25 / #26** | Must not regress MPOLICY padding or MPREM behavior. |

---

## Domain and scope

| In scope | Out of scope |
|----------|--------------|
| QuikCvs / QuikPlCv CV duration endpoint behavior | Non-CV rate families unless separately proven affected |
| Product `1960PO` / `960 PO` proof case | Rewriting rate-loader architecture |
| Fleet scan for other issue ages showing the same one-duration terminal shift | Issue #40 inherited-rate source selection |
| Validation of age-100 inclusive endpoint | Changing rate values |

---

## Blockers visible at intake

| Blocker | Owner | Notes |
|---------|-------|-------|
| Confirm QLAdmin duration convention for CV table display | Conversion + Client / QLAdmin SME | Need final answer on whether displayed duration 57 corresponds to policy year 57 / age 100 inclusive endpoint. |
| Confirm corrected endpoint formula | Conversion | Candidate: age-100 inclusive endpoint, likely one more terminal slot than current rule. |
| Re-run Issue #37 proof matrix with new age-26 example | Conversion | Must preserve first-rate placement while fixing terminal duration. |
| Regression rebaseline | Conversion | QuikCvs row/key counts may change intentionally. |

---

## G0 gate

- [x] Issue folder created
- [x] Client symptom documented
- [x] Relationship to Issue #37 documented
- [x] No code or output changes made

**Next stage:** Planning Agent -> Dependency Gate -> Risk Agent before development.
