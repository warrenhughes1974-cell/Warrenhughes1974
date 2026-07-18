# Plan Value Reference Schema Verification

**Inspected:** `Q:\CSO\CSO_Test_6_30_2025`  
**Date:** 2026-07-18  
**Tool:** dbfread (read-only)

## Source tables (plan-value)

| Logical table | File | Records | PLAN | GENDER | UWCLASS | BAND | ISSUEST | EFFDATE | MORT | ETIMORT |
|---------------|------|---------|------|--------|---------|------|---------|---------|------|---------|
| QuikPlCv | QuikPlCv.dbf | 230 | C(6) | C(1) | C(2) | C(2) | C(2) | D(8) | C(2) | C(2) |
| QuikPlTv | QuikPlTv.dbf | 280 | C(6) | C(1) | C(2) | C(2) | C(2) | D(8) | C(2) | — |
| QuikPlGp | QuikPlGp.dbf | 282 | C(6) | C(1) | C(2) | C(2) | C(2) | D(8) | — | — |
| QuikPlDb | QuikPlDb.dbf | 210 | C(6) | C(1) | C(2) | C(2) | C(2) | D(8) | — | — |
| QuikPlDv | QuikPlDv.dbf | 210 | C(6) | C(1) | C(2) | C(2) | C(2) | D(8) | — | — |

Notes:

- Source fields are **not** M-prefixed on these tables (PLAN, GENDER, UWCLASS, BAND, ISSUEST, EFFDATE, MORT, ETIMORT).
- **ETIMORT** exists only on QuikPlCv.
- **MORT** exists on QuikPlCv and QuikPlTv only.

## Reference tables

| Logical table | File | Key field(s) | Type/length | Uniqueness |
|---------------|------|--------------|-------------|------------|
| QuikQxs | QUIKQXS.DBF | **MORT** | C(2) | Unique on MORT (243/243) |
| QuikPlan | quikplan.dbf | **PLAN** | C(6) | Unique on PLAN (nonblank) |
| QuikPlGd | QuikPlGd.dbf | **PLAN + GDCODE** | C(6) + C(1) | Unique as composite; GDCODE alone is **not** unique |
| QuikPlUw | QuikPlUw.dbf | **PLAN + UWCODE** | C(6) + C(2) | Unique as composite; UWCODE alone is **not** unique |
| QuikPlBd | QuikPlBd.dbf | **PLAN + BDCODE** | C(6) + C(2) | Unique as composite; used for BAND |

## QuikPlVd

**Not found** in the inspected CSO data region. No `QuikPlVd.dbf` / `QUIKPLVD.DBF`.

The verified band-definition table present in the region is **QuikPlBd** with band code **BDCODE**.

**Implementation mapping for DG-PLANVALUES-006:**

| Business | Verified physical reference |
|----------|-----------------------------|
| BAND → setup | QuikPlBd.**BDCODE** scoped by source **PLAN** |

## Governance lookup mapping

| Rule | Source field | Reference | Lookup key |
|------|--------------|-----------|------------|
| 001 MORT | MORT | QuikQxs.MORT | normalized MORT |
| 002 ETIMORT | ETIMORT | QuikQxs.MORT | normalized ETIMORT |
| 003 PLAN | PLAN | QuikPlan.PLAN | normalized PLAN |
| 004 GENDER | GENDER | QuikPlGd.GDCODE | (source PLAN, GENDER) ↔ (PLAN, GDCODE); default `0` |
| 005 UWCLASS | UWCLASS | QuikPlUw.UWCODE | (source PLAN, UWCLASS) ↔ (PLAN, UWCODE); default `00` |
| 006 BAND | BAND | QuikPlBd.BDCODE | (source PLAN, BAND) ↔ (PLAN, BDCODE); default `00` |
| 007 ISSUEST | ISSUEST | (approved list) | `00` or US state / DC abbreviation |
| 008 EFFDATE | EFFDATE | date bounds | ≥ 1900-01-01 and ≤ run date + 12 calendar months |
