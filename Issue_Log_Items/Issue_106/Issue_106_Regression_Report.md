# Issue #106 — Regression Report

**Issue:** #106 — RV Rates Off by One Duration  
**Framework stage:** Regression (G6)  
**Date:** 2026-07-24  
**Version:** v58.31  
**Result:** **PASS**

---

## Guards

| Guard | Result | Evidence |
|-------|--------|----------|
| CV #98 anchor `17085M` M/14 | **PASS** | QuikCvs Dur3=`.06`, Dur86=`1000.00` (unchanged LifePRO CV grid) |
| NP still `source − 1` | **PASS** | `170858` M/17 QuikNps has Dur0 populated (`1.58`) — not identity |
| RV identity only | **PASS** | QuikTvs proofs Dur labels match LifePRO |
| Issue #40 inherited CV verify | **PASS** | Rate emit log: PASS 10 plans |

---

## Blast

| Table | Expected change |
|-------|-----------------|
| QuikTvs | All durations +1 vs pre-v58.31 Output |
| QuikCvs / QuikNps / QuikDvs / QuikDbs / QuikGps | Unchanged indexing rules |

---

## Defect #2

Not in regression scope. `1L1095` still sourced from L10 LP95.
