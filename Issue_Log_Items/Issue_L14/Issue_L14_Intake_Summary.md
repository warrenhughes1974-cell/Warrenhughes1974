# Issue L14 — Intake Summary

**Issue:** L14 — Cash Value Duration Off-by-One (QuikCvs)  
**Framework stage:** Intake Agent (G0)  
**Status recommendation:** Intake Complete → Planning → Dependency Gate → Risk  
**Generated:** 2026-08-06  
**Owner:** Conversion  
**Priority:** Go-No Go (rates UAT — LifePRO vs QLAdmin CV grid)

---

## Client symptom (verbatim + normalized)

**Normalized:** L14 / plan `1L14SC` cash-value factors are one duration **late** vs LifePRO. LifePRO Dur2 lands at QLAdmin Dur3; LifePRO terminal Dur31=`1000` is missing from QL Dur31.

Gold (screenshots + Rate_Table 2026-08-05): Coverage `L14` / Type CV / F / age 69 / UW N vs QLAdmin `1L14SC` / F / 69 / NS / Band 00.

| LifePRO Dur | Value | Current QuikCvs Dur |
|------------:|------:|--------------------:|
| 1 | 0.00 | 1 = 0 / also leading zeros |
| 2 | **14.73** | **3** = 14.73 (late) |
| 3 | 52.91 | 4 |
| 30 | 916.71 | 31 |
| 31 | **1000** | absent (truncated) |

## Example policies / keys

| Anchor | Key |
|--------|-----|
| Primary gold | `1L14SC` F/69 NS — Dur2=`14.73`, Dur31=`1000` |
| Second proof | `1L14SC` F/45 NS — Dur2=`8.37`, terminal `1000` at last LifePRO dur |
| Regression | #98 `17085M` M/14 — `.06` @ Dur3; Dur86=`1000` |

## Suspected domain

Rates — QuikCvs CV duration remap (`qla_core/rate_factor_loader.py` · `cv_remap_ql_duration` / `cv_lifepro_first_duration`).

Root cause: fleet CV remap uses `source_d + first_duration(sex,age) − fnz`. For L14 slices, `first=3` and `fnz=2` → **+1 late** vs LifePRO screen / Rate_Table DURATION labels (identity). Terminal `1000` then falls past `100 − issue_age` and is dropped.

## In scope (first pass)

- L14 / `1L14SC` QuikCvs: LifePRO Dur N → QL Dur N (identity for this coverage).
- Second L14 age/sex proof.
- Durable L14 validator + release-smoke row.
- Prove #98 GL85 CV unchanged.
- Rates re-emit only (no policy rebatch unless approved).

## Out of scope (first pass)

- #106 QuikTvs RV duration (closed).
- #118 UW class remap.
- Reinsurance (ON HOLD).
- Recreating DBFs (Append Tool APPEND only).
- Changing GL85 / PO first-duration matrix globally.

## Related issues

| ID | Relationship |
|----|----------------|
| **#37 / #41** | Closed fleet CV duration placement — L14 missed member |
| **#98** | Closed GL85 CV endpoint — **regression control** |
| **#106** | Closed QuikTvs RV — different table |

## Immediate blockers

None for Intake. Source Rate_Table + PDAGE present; gold proven.

## Gate (G0)

- [x] Issue folder  
- [x] Intake summary  
- [x] Example keys  
- [x] Owner / priority  
- [x] No code changes at Intake  
