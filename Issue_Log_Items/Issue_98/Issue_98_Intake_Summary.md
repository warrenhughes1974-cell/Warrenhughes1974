# Issue #98 — Intake Summary

**Issue:** #98 — CV Endpoint Off By One (follow-up to #41)  
**Date:** 2026-07-22  
**Framework stage:** Intake complete (G0)  
**Status:** Proceed to Planning  
**Owner:** Conversion (Warren) · Client reporter: Eric  
**Business status:** No-Go (client) — reopen / residual of Issue #41 family

---

## Client / business symptom (verbatim)

> CV Endpoint Off By One — CV Factor off by one duration (issue 41). Example Policy 010398471C, duration factor should be between 674.69 and 688.11 (As of 7/2/26, factor in LifePRO was 684.76). It appears CV factor of .06 should start in year 3, year 86 should be 1000 and year 85 should be 975.61. Email sent with LifePRO CV factor screenshots. 7/22/2026 No-Go Eric Warren

---

## Normalized finding

This is **not** a stale-UAT false reopen of Issue #41’s `1960PO` proof case. Eric’s new example is **policy `010398471C` / plan `17085M`** (inherited CV from `670 GL85-8`, Issue #40), Male issue age **14**.

Current full `QLA_Migration/Output/rates/QuikCvs.csv` for `17085M` / M / 14:

| Point | Current QLA | Eric expected | Result |
|-------|------------:|--------------:|--------|
| First `.06` | duration **4** | duration **3** | **FAIL** |
| Neighbors 674.69 / 688.11 | durations **55 / 56** | **54 / 55** | **FAIL** |
| 975.61 | duration **86** (terminal) | duration **85** | **FAIL** |
| 1000 | **missing** (truncated) | duration **86** | **FAIL** |

LifePRO source extract for `670 GL85-8` CV M/14 has `.06` at source duration 2, `975.61` at 84, and **`1000` at 85**. The Issue #37/#41 remap applies `cv_lifepro_first_duration(M,14)=4` with `fnz=2`, shifting by **+2**, which:

1. Places every factor **one duration late** vs Eric’s LifePRO screen convention, and  
2. Pushes terminal `1000` to QL duration 87, which is dropped by `last_duration = 100 - issue_age` (= 86).

So the visible “off by one” and “ends at 975.61 instead of 1000” are the **same remap defect**.

`684.76` is **not** a discrete table cell (table neighbors are 674.69 / 688.11); Eric cites it as LifePRO’s as-of-7/2/26 factor between those neighbors — likely interpolated / duration-in-force, not a missing source row.

---

## Example policy

| Field | Value |
|-------|-------|
| Policy | `010398471C` (LP `9010398471`) |
| Base plan | `17085M` (`670 GL85-M`) |
| CV rate owner | `670 GL85-8` → plan `170858` / inherited to `17085M` (#40) |
| Sex / issue age | M / **14** (DOB 1957-10-08, issue 1971-10-01) |
| As-of cited | 2026-07-02 |

---

## Suspected domain

**Rates — QuikCvs duration remap** (`qla_core/rate_factor_loader.py` · `cv_remap_ql_duration` / `cv_lifepro_first_duration`)

Not: policy fee, Names modal, memo, quikridr (those are #97 on the same policy).

---

## Related issues

| Issue | Relationship |
|-------|--------------|
| **#37** | Introduced CV LifePRO grid remap + `cv_lifepro_first_duration` from **960 PO** proof matrix |
| **#41** | Changed CV remap to keep age-100 endpoint (`ql_duration = lp_duration`); validated on `1960PO` M/26 — **still PASS** under current rules |
| **#40** | Loaded inherited CV for `17085M` from `670 GL85-8`; values match owner at same QL index, so inheritance is fine — **placement** is wrong |
| **#97** | Same example policy, different symptom (fee/Names/memo) — out of scope here |

---

## In scope / out of scope

| In scope | Out of scope |
|----------|--------------|
| QuikCvs CV duration placement for ages where first-duration heuristic over-shifts | Changing CV numeric source values |
| Restoring terminal `1000` at attained age 100 for affected slices | Non-CV rate families |
| Re-proof of #37/#41 anchors after any remap change | #97 fee/memo package questions |
| Fleet impact of first-duration / endpoint remap | Rewriting rate loader architecture |

---

## Artifact inventory

| Artifact | Status |
|----------|--------|
| Client email description | **Present** (tracking row) |
| LifePRO CV screenshots | Referenced (“email sent”) — **not yet filed** in `Issue_98/` |
| Current Output QuikCvs | **Present** — `17085M` 1,002 keys |
| Source Rate_Table | **Present** — `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv` |
| Trace evidence | **Created** — `evidence/issue98_010398471C_cv_trace.csv` (5/5 FAIL) |

---

## Immediate blockers at intake

| Item | Owner | Notes |
|------|-------|-------|
| Optional: file Eric’s LifePRO screenshots under `Issue_98/evidence/` | Warren / Eric | Strong confirmation, but numeric expectations already actionable |
| Confirm fix strategy: adjust `cv_lifepro_first_duration` for young ages vs endpoint-anchored remap | Conversion | Must not regress #37/#41 `1960PO` proofs |

---

## G0 gate

- [x] Issue folder created  
- [x] Client symptom documented  
- [x] Relationship to #37/#40/#41 documented  
- [x] Current Output vs Eric expectations measured  
- [x] No code or output changes made  

**Next stage:** Planning → Dependency Gate → Risk (Pre-Development Auto-Chain).
