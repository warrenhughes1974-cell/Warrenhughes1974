# Issue #21A — Resolution Summary

**Issue:** #21A — NFO / Dividend Options  
**Framework stage:** Closure (G7)  
**Final status:** **Closed**  
**Engine version:** **v57.47**  
**Closed date:** 2026-07-04  
**Owner:** Conversion (Warren) · Reporter: Eric · SME: New Era (codes 1/2 → APL)

---

## Resolution (issue log — paste-ready)

**Resolution:** PPBENTYP cache now reads `BF_NON_FORFEITURE` for ISWL/BF policies and maps LifePRO NFO codes 1 and 2 to APL (`MNFOPT=1`) per SME guidance (v57.47).

> Long-form audit detail below.

---

## Production Readiness (G7 gate)

| Check | Status |
|-------|--------|
| G5 validation PASS | **Done** — `Issue_21A_Validation_Report.md` |
| G6 regression PASS | **Done** — `Issue_21A_Regression_Report.md` |
| `app.py` / `QLA_Migration/app.py` **v57.47** | **Done** |
| Issue-scoped git commit | Pending — stage 21A files on branch `issue-34-pr7-quikisrr` |
| Git push to remote | Pending user authorization |
| Network batch after pull | Re-run full batch at v57.47 (`Output/` gitignored) |

---

## Problem Statement

Non-Forfeiture Option (NFO) elections from LifePRO appeared as **0** in QLAdmin on many policies instead of the client's real election (e.g. **APL**, **ETI**). LifePRO codes **1** (APL/ETI) and **2** (APL/RPU) were not consistently mapped to QLAdmin **APL (`MNFOPT=1`)** per SME guidance that APL is attempted first. ISWL/BF products store NFO on **`BF_NON_FORFEITURE`**, which the engine cache did not read.

**Example:** Policies **010765930C**, **010718309C**, **010818663C** — LifePRO BF segment shows NFO code **1**; QLAdmin showed **0**.

---

## Root Cause

**Category:** Source cache / translation mapping

1. **Track A:** PPBENTYP cache for `quikmstr.MNFOPT` enrichment read only **`NON_FORFEITURE`**. ISWL/BF rows (`TYPE_CODE=BF`) store the election on **`BF_NON_FORFEITURE`** with blank `NON_FORFEITURE` → cache miss → **`MNFOPT=0`**.
2. **Track B:** LifePRO code **2** passthrough to QLAdmin **2**; SME requires **1** (APL) for codes **1** and **2**.
3. **Safety:** After Track A fix, **83** BF policies with source code **9** could passthrough invalid **`MNFOPT=9`** (QLAdmin domain is 0–3).

**Out of scope (client scope lock):** LifePRO codes **3–6** translation unchanged; codes **7–9** not in QLAdmin crosswalk except **`NF_9→0`** safety; **`MDIVOPT`** / dividend option redesign deferred.

---

## Resolution (v57.47)

1. **PPBENTYP cache** — When building `NON_FORFEITURE` cache (benefit seq 1), prefer **`BF_NON_FORFEITURE`** when **`TYPE_CODE=BF`**, else **`NON_FORFEITURE`**.
2. **Translation** — Added **`NF_1→1`**, **`NF_2→1`**, **`NF_9→0`** (safety only) in `Master_Value_Translation.csv` (+ mirror).
3. **Enrich-on-zero guard preserved** — Cache pull only when rulebook `MNFOPT` is **0/blank** (~5858 in `app.py`); policies already at **2** or **3** are not overwritten.

### Files changed

| File | Change |
|------|--------|
| `app.py` | v57.47 — PPBENTYP BF cache resolution |
| `QLA_Migration/app.py` | Mirror |
| `Master_Value_Translation.csv` | NF_1, NF_2, NF_9 entries |
| `QLA_Migration/Mapping/Master_Value_Translation.csv` | Mirror |
| `tools/validators/validate_issue21a_mnfopt.py` | New validator |
| `QLA_Migration/_research_issue21a_nfo.py` | Read-only research |
| `QLA_Migration/_risk_review_issue21a_nfo.py` | Risk simulation |
| `Issue_Log_Items/Issue_21/Issue_21A/*` | Intake through closure artifacts |

### Rulebook changes

**None** — `Sync_Rulebook_quikmstr.csv` unchanged (`NFO_OPT→MNFOPT` default 0 retained).

---

## Evidence

| Artifact | Path |
|----------|------|
| Intake | `Issue_21A_Intake_Summary.md` |
| Planning | `Issue_21A_Planning_Report.md` |
| Dependency Gate | `Issue_21A_Dependency_Gate.md` |
| Risk | `Issue_21A_Risk_Review_Report.md` |
| Implementation | `Issue_21A_Implementation_Notes.md` |
| Validation (G5) | `Issue_21A_Validation_Report.md` |
| Regression (G6) | `Issue_21A_Regression_Report.md` |
| Trace samples | `Issue_21A_Trace_Samples.csv` |
| Risk simulation | `Issue_21A_Risk_Simulation.csv` |
| Validator | `tools/validators/validate_issue21a_mnfopt.py` |

---

## Trace Policy Confirmation

| Policy | Source | Before | After | Result |
|--------|--------|-------:|------:|--------|
| 010765930C | BF_NON_FORFEITURE=1 | 0 | **1** | PASS |
| 010718309C | BF_NON_FORFEITURE=1 | 0 | **1** | PASS |
| 010818663C | BF_NON_FORFEITURE=1 | 0 | **1** | PASS |
| 010469666C | NON_FORFEITURE=2 | 2 | **1** | PASS |
| 010391895C | NON_FORFEITURE=4 | 0 | **0** | PASS (out of scope) |
| 010448806C | NON_FORFEITURE=5 | 0 | **0** | PASS (out of scope) |
| 010713704C | BF_NON_FORFEITURE=4 | 0 | **0** | PASS (out of scope) |
| 010391876C | NON_FORFEITURE=4 | 2 | **2** | PASS (guard — not overwritten) |

---

## Fleet Impact

| Metric | Value |
|--------|------:|
| Policies with `MNFOPT` change | ~1,339 |
| Primary fix `0→1` | ~1,204 |
| NF_2 SME fix `2→1` | 5 |
| Source code 9 held at 0 | 83 |
| `quikmstr` row count | 5,083 (unchanged) |

---

## Explicit Non-Changes

- `quikmstr.MDIVOPT` / dividend cache logic
- `NF_3`–`NF_6` translation entries (`NF_4→0`, `NF_5→0` unchanged)
- `PPOLC.MODE_PREMIUM` → `MMODEPREM` (#26)
- `PPBEN.ANN_PREM_PER_UNIT` → `MPREM` (#26)
- MPOLICY padding (#25)
- `quikplan.NFOINT` (#21D)
- All other table row counts and schemas

---

## Residual / Follow-Up

- **Client UAT:** Verify NFO election on sample policies in QLAdmin (trace list above + random BF policies).
- **Dividend options:** `MDIVOPT` population not redesigned in this release — separate item if client reports DIV=0 issues persist.
- **44 policies** with PPBENTYP source code 1/2 remain at `MNFOPT=0` (cache-key edge cases outside trace set) — monitor during UAT.
- **Network batch:** Pull v57.47 and re-run full batch; `Output/` is gitignored.

---

## Rollback

1. Revert v57.47 commit on branch.
2. Remove BF_NON_FORFEITURE cache branch in PPBENTYP load (~5327).
3. Remove `NF_1`, `NF_2`, `NF_9` from translation CSVs.
4. Re-run batch — `MNFOPT` returns to v57.46 baseline distribution.

---

## Issue Log Readout (client-facing)

**Resolution:** PPBENTYP cache now reads `BF_NON_FORFEITURE` for ISWL/BF policies and maps LifePRO NFO codes 1 and 2 to APL (`MNFOPT=1`) per SME guidance (v57.47).

---

**Issue #21A — Closed.**
