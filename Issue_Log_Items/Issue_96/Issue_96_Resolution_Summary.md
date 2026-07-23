# Issue #96 — Resolution Summary

**Issue:** #96 — CSO valuation cannot use SAL MULTPL / L17 RV rates  
**Framework stage:** Closure Agent (G7)  
**Final status:** **Closed ✓**  
**Engine version:** v58.26 (PVO/CSO) / v58.27 (durable `1SALMI` M/F keys)  
**Closed date:** 2026-07-22  
**Owner:** Conversion (Warren)

---

## Resolution (issue log — paste-ready)

**Resolution:** CSO valuation now enables Plan Values Options when QuikTvs/Cvs exist for SAL MULTPL and L17 RV plans, and `1SALMI` carries the same M/F QuikPlCv/QuikPlTv keys as `1SALOL`.

> Copy the line above into tracking sheets and client readouts. Long-form detail follows.

---

## Problem Statement

CSO valuation could not use SAL MULTPL / L17 RV rate tables because Plan Values Options / gender variation flags and QuikPl* keys were not wired for those plans (`1SALMI` missing from CSO setup; PVO not set when factor tables were present).

---

## Root Cause

**Category:** Mapping / plan setup wiring

Missing `1SALMI` CSO valuation setup row, incomplete post-rate PVO enablement, and non-durable female companion keys for `1SALMI` PlCv/PlTv.

---

## Resolution (long-form)

v58.26 added `1SALMI` to CSO setup, durable PVO enablement when QuikTvs/Cvs exist (with annuity A8e clear), and post-rate quikplan integrate. v58.27 made `1SALMI` M/F PlCv/PlTv companion keys durable in the rate pipeline and re-emitted rates.

### Output accountability gate (G7)

| Check | Status |
|-------|--------|
| `validate_issue96_cso_pvo.py` | **PASS** |
| Accountability `#96` | **IN_DATA** |
| Test_Validation | `quikplan` + rates QuikTvs/PlTv/PlCv (and #98 QuikCvs publish) |

---

## Trace confirmation

| Plan | PLANVALOPT | QuikTvs | PlTv | PlCv |
|------|:----------:|--------:|-----:|-----:|
| 1SALOL / 1SALMI / 1SALML | Y | 508 | 2 | 2 |
| 1L17SP + L17 children | Y | 38 | 2 | 2 |

---

## Explicitly Not Changed

- Track 2 RV holds
- QuikUint / Issue #95
- Non-focus plan rate formulas

---

## Residual risks / follow-ups

None for this issue. Network machines must re-run rate emit / product setup integrate after pull (`Output/` gitignored).

---

## Git release

| Field | Value |
|-------|-------|
| Close package | v58.27 rate release (`0b12298` / later session commits) |
| Branch | `issue-34-pr7-quikisrr` |
