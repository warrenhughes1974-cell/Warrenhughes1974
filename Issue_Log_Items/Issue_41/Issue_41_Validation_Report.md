# Issue #41 — Validation Report

**Issue:** CV Age/Duration Endpoint Off by One  
**Date:** 2026-07-06  
**Validation result:** PASS for CV endpoint and source-vs-QLA examples  
**Generated evidence:** `Issue_Log_Items/Issue_41/evidence/issue41_quikcvs_endpoint_examples.csv`

---

## 1. Validation summary

| Check | Result |
|-------|--------|
| Issue #37 placement proof cases | **PASS** |
| Issue #41 source-vs-QLA examples | **PASS** — 5 / 5 |
| 10 additional plan source-vs-QLA validation | **PASS** — 30 / 30 |
| Regenerated `QuikCvs.csv` row count | **26,495** |
| `1960PO` M/26 client anchor | **PASS** |
| `1960PO` M/26 age-100 endpoint | **PASS** |
| Non-CV rate grids still populated | **PASS** — `QuikNps` 26,650 keys; `QuikGps` 12,567 keys |
| Full guarded R5 emit | **Blocked** by unrelated `V-UINT-PDINT` / `QuikUint` dependency |

---

## 2. Client anchor proof

`960 PO` / `1960PO` / CV / Male / issue age `26` / UW `00` / band `01`:

| Source coverage | Source duration | Source value | QLA plan | QLA duration index | QLA field | QLA value | Result |
|-----------------|----------------:|-------------:|----------|-------------------:|-----------|----------:|--------|
| `960 PO` | 56 | 784.65 | `1960PO` | **57** | `CNTL=05` / `CV7` | 784.65 | **PASS** |

This directly addresses the client-reported example: `784.65` is no longer one QL duration early in the regenerated `QuikCvs.csv`.

---

## 3. Age-100 endpoint proof

| Source coverage | QLA plan | Sex | Issue age | Source duration | Source value | QLA duration index | Attained age | QLA field | QLA value | Result |
|-----------------|----------|-----|----------:|----------------:|-------------:|-------------------:|-------------:|-----------|----------:|--------|
| `960 PO` | `1960PO` | M | 26 | 73 | 1000.00 | **74** | **100** | `CNTL=07` / `CV4` | 1000.00 | **PASS** |
| `960 PO` | `1960PO` | M | 22 | 76 | 1000.00 | **78** | **100** | `CNTL=07` / `CV8` | 1000.00 | **PASS** |
| `960 OL` | `1960OL` | M | 22 | 76 | 963.83 | **78** | **100** | `CNTL=07` / `CV8` | 963.83 | **PASS** |
| `991 PWL` | `1991PL` | M | 22 | 76 | 982.00 | **78** | **100** | `CNTL=07` / `CV8` | 982.00 | **PASS** |

The additional plans prove the corrected endpoint mapping is not isolated to `1960PO`.

---

## 4. Issue #37 regression matrix

`Issue_Log_Items/Issue_37/evidence/g5_validation_matrix.csv` was regenerated:

| Metric | Result |
|--------|-------:|
| `1960PO` proof cases | 9 / 9 PASS |
| Fleet spot checks | 3 PASS, 1 pre-existing waived collision |
| QuikCvs keys | 26,495 |
| QuikCvs CSV rows | 26,495 |
| Failures | 0 |

New required proof case added:

| Plan | Sex | Age | First expected | First actual | Last expected | Last actual | Result |
|------|-----|----:|---------------:|-------------:|--------------:|------------:|--------|
| `1960PO` | M | 26 | 2.43 | 2.43 | 1000.00 | 1000.00 | **PASS** |

---

## 5. Expanded 10-plan validation

Additional evidence: `Issue_Log_Items/Issue_41/evidence/issue41_quikcvs_10_plan_validation.csv`

The expanded validator checked **10 additional plans** beyond the original `1960PO` anchor set. Each plan was validated at three points: first non-zero CV, mid-duration CV, and terminal age-100 endpoint CV.

| Plan | Coverage | Comparisons | Result |
|------|----------|------------:|--------|
| `130JEB` | `630 JEB` | 3 | **PASS** |
| `1658C1` | `658 CEN I` | 3 | **PASS** |
| `1658CS` | `658 CEN SD` | 3 | **PASS** |
| `1659C2` | `659 CEN II` | 3 | **PASS** |
| `1659CR` | `659 CEN SR` | 3 | **PASS** |
| `1659CS` | `659 CEN SD` | 3 | **PASS** |
| `1659SR` | `659 SR GD` | 3 | **PASS** |
| `1666WL` | `666 WL` | 3 | **PASS** |
| `1669SR` | `669 SR GD` | 3 | **PASS** |
| `1679CS` | `679 CEN SD` | 3 | **PASS** |

Summary:

| Metric | Result |
|--------|-------:|
| Additional plans validated | 10 |
| Source-to-QLA comparisons | 30 |
| Passed comparisons | 30 |
| Failed comparisons | 0 |

Example rows from the expanded proof:

| Plan | Source duration | Source value | QLA duration index | QLA field | QLA value | Result |
|------|----------------:|-------------:|-------------------:|-----------|----------:|--------|
| `130JEB` | 66 | 3815.95 | 71 | `CNTL=07` / `CV1` | 3815.95 | **PASS** |
| `1658C1` | 95 | 1000.00 | 100 | `CNTL=10` / `CV0` | 1000.00 | **PASS** |
| `1666WL` | 95 | 959.00 | 100 | `CNTL=10` / `CV0` | 959.00 | **PASS** |
| `1669SR` | 49 | 937.00 | 50 | `CNTL=05` / `CV0` | 937.00 | **PASS** |
| `1679CS` | 95 | 1000.00 | 100 | `CNTL=10` / `CV0` | 1000.00 | **PASS** |

---

## 6. Remaining risk / next steps

The CV fix is validated, but the full guarded rate emit still reports one unrelated blocker:

| Blocker | Required next step |
|---------|--------------------|
| `V-UINT-PDINT` — `QuikUint` has no `PDINTTBL` source rows while enabled | Resolve the `QuikUint` dependency or run a rate-table scope that excludes `QuikUint` before final full package emit. |

Client UAT should reload the regenerated `QLA_Migration/Output/rates/QuikCvs.csv` and verify the `1960PO` M/26 screen against the client screenshots.
