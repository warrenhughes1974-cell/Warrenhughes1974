# QLAdmin Functional Test Script (R6B)

Tester-friendly execution script for sandbox functional validation after import.
Record all results in `rate_import_validation_matrix.csv` and factor traces in
`qladmin_lookup_trace_template.csv`.

**Environment:** QLAdmin sandbox only  
**Prerequisite:** Full 16-table import completed per `qla_sandbox_import_execution_guide.md`

---

## How to use this script

1. Complete import verification tests **R6B-001 through R6B-016** during load.
2. Run structural check **R6B-017** after all tables are loaded.
3. Work through Sections 1–5 below for functional tests **R6B-018 through R6B-060**.
4. Enter `ACTUAL_RESULT`, `PASS_FAIL` (PASS/FAIL/N/A), `TESTER`, `TEST_DATE`, and `NOTES`.
5. For factor lookups (R6B-044 onward), also complete `qladmin_lookup_trace_template.csv`.

---

## Section 0 — Import verification (during load)

| TEST_ID | Table | Pass criteria |
|---|---|---|
| R6B-001 | QuikPlGd | Import succeeds; 110 rows |
| R6B-002 | QuikPlUw | Import succeeds; 80 rows |
| R6B-003 | QuikPlBd | Import succeeds; 66 rows |
| R6B-004 | QuikPlSt | Import succeeds; 64 rows |
| R6B-005 | QuikPlNb | Import succeeds; 64 rows |
| R6B-006 | QuikPlGp | Import succeeds; 13 rows |
| R6B-007 | QuikPlDv | Import succeeds; 20 rows |
| R6B-008 | QuikPlDb | Import succeeds; 12 rows |
| R6B-009 | QuikPlCv | Import succeeds; 70 rows |
| R6B-010 | QuikPlTv | Import succeeds; 112 rows |
| R6B-011 | QuikGps | Import succeeds; 1,123 rows |
| R6B-012 | QuikDvs | Import succeeds; 3,978 rows |
| R6B-013 | QuikDbs | Import succeeds; 1,380 rows |
| R6B-014 | QuikCvs | Import succeeds; 25,717 rows |
| R6B-015 | QuikTvs | Import succeeds; 26,097 rows |
| R6B-016 | QuikNps | Import succeeds; 26,650 rows |
| **R6B-017** | **ALL** | No orphan PLANs; EFFDATE=19000101; no import errors |

---

## Section 1 — Member table display

| Step | TEST_ID | Action | Pass criteria |
|---:|---|---|---|
| 1.1 | R6B-022 | Open plan `130JEB` → gender M | MALE displays |
| 1.2 | R6B-023 | Open plan `130JEB` → gender F | FEMALE displays |
| 1.3 | R6B-024 | Open plan `7687J3` → gender J | JOINT displays |
| 1.4 | R6B-025 | Open plan `1658C1` → UW PR | PREFERRED displays |
| 1.5 | R6B-026 | Open plan `1L14SC` → UW NS | NON-SMOKER displays |
| 1.6 | R6B-027 | Open plan `1L1095` → UW ST | STANDARD displays |
| 1.7 | R6B-028 | Open plan `5L01MA` → band 02 | BAND 2 displays |
| 1.8 | R6B-029 | Open plan `5L01MA` → band 03 | BAND 3 displays |
| 1.9 | R6B-030 | Open plan `130JEB` → state/country | `0000/00` ALL (OTHER) displays |
| 1.10 | R6B-031 | Open plan `130JEB` → new business | EFFDATE=19000101, TERMDATE open |
| 1.11 | R6B-032 | Open plan `2665ST` → BDLOWVAL | Value=0; PLACEHOLDER_DEFERRED |

---

## Section 2 — Plan lookup

| Step | TEST_ID | Plan | Pass criteria |
|---:|---|---|---|
| 2.1 | R6B-018 | `130JEB` | Plan opens in plan maintenance |
| 2.2 | R6B-019 | `2665ST` | Large-factor plan selectable |
| 2.3 | R6B-020 | `A96DAR` | Large CV plan selectable |
| 2.4 | R6B-021 | `1L10OD` | AGE-cap scenario plan selectable |

---

## Section 3 — Rate key recognition

| Step | TEST_ID | Table | Pass criteria |
|---:|---|---|---|
| 3.1 | R6B-033 | QuikPlGp | Gross premium keys visible |
| 3.2 | R6B-034 | QuikPlDv | Dividend keys visible |
| 3.3 | R6B-035 | QuikPlDb | Death benefit keys visible |
| 3.4 | R6B-036 | QuikPlCv | Cash value keys visible |
| 3.5 | R6B-037 | QuikPlTv | Terminal reserve / NP keys visible |

Verify `EFFDATE = 19000101` on each key row inspected.

---

## Section 4 — Factor retrieval by family

### 4.1 Gross Premium

| Step | TEST_ID | Plan | Lookup | Expected |
|---:|---|---|---|---|
| 4.1a | R6B-038 | `2665ST` | smoke test | Factor retrieval succeeds |
| 4.1b | R6B-044 | `2665ST` | M/01/00 AGE 00 DUR 1 | **222.22** |
| 4.1c | R6B-045 | `5L01MA` | M/01/SM AGE 15 DUR 1 | **1.39** |

### 4.2 Dividend

| Step | TEST_ID | Plan | Lookup | Expected |
|---:|---|---|---|---|
| 4.2a | R6B-039 | `130JEB` | smoke test | Factor retrieval succeeds |
| 4.2b | R6B-046 | `130JEB` | M/01/00 AGE 00 DUR 1 | **.00** |
| 4.2c | R6B-047 | `130JEB` | M/01/00 AGE 00 DUR 6 | **2.80** |

### 4.3 Death Benefit

| Step | TEST_ID | Plan | Lookup | Expected |
|---:|---|---|---|---|
| 4.3a | R6B-040 | `2665ST` | smoke test | Factor retrieval succeeds |
| 4.3b | R6B-048 | `1659SR` | M/01/SM AGE 00 DUR 1 | **300.00** |
| 4.3c | R6B-049 | `17CSI3` | M/01/00 AGE 46 DUR 1 | **4.00** |

### 4.4 Cash Value

| Step | TEST_ID | Plan | Lookup | Expected |
|---:|---|---|---|---|
| 4.4a | R6B-041 | `130JEB` | smoke test | Factor retrieval succeeds |
| 4.4b | R6B-050 | `130JEB` | M/01/00 AGE 00 DUR 1 | **.00** |
| 4.4c | R6B-051 | `1658C1` | F/01/PR AGE 00 DUR 6 | **11.00** |

### 4.5 Terminal Reserve

| Step | TEST_ID | Plan | Lookup | Expected |
|---:|---|---|---|---|
| 4.5a | R6B-042 | `130JEB` | smoke test | Reserve retrieval succeeds |
| 4.5b | R6B-052 | `130JEB` | F/01/00 AGE 00 DUR 6 | **164.19** |
| 4.5c | R6B-053 | `1658C1` | F/01/PR AGE 00 DUR 1 | **1.00** |

### 4.6 Net Premium

| Step | TEST_ID | Plan | Lookup | Expected |
|---:|---|---|---|---|
| 4.6a | R6B-043 | `130JEB` | smoke test | Factor retrieval succeeds |
| 4.6b | R6B-054 | `130JEB` | F/01/00 AGE 00 DUR 1 | **22.03** |
| 4.6c | R6B-055 | `1658C1` | F/01/PR AGE 00 DUR 6 | **11.00** |

> Net premium resolves through shared rate key **QuikPlTv**.

---

## Section 5 — Special scenarios

### 5.1 AGE 99 scenario (`1L10OD`)

| Step | TEST_ID | Lookup | Expected |
|---:|---|---|---|
| 5.1 | R6B-056 | M/01/ST AGE **99** DUR 1 | CV = **1000.00** |

### 5.2 Large factor — `2665ST`

| Step | TEST_ID | Lookup | Expected |
|---:|---|---|---|
| 5.2a | R6B-057 | M/01/00 AGE 00 DUR 1 | DB = **28134.0** |
| 5.2b | R6B-058 | M/01/00 AGE 00 DUR 6 | DB = **28134.0** |

### 5.3 Large factor — `A96DAR`

| Step | TEST_ID | Lookup | Expected |
|---:|---|---|---|
| 5.3a | R6B-059 | M/01/00 AGE 00 DUR 41 | CV = **9723.28** |
| 5.3b | R6B-060 | M/01/00 AGE 00 DUR 46 | CV = **12164.9** |

---

## Section 6 — Negative / integrity checks

Record findings as NOTES on **R6B-017**:

| Check | Pass criteria |
|---|---|
| Orphan factor rows | None |
| Missing factor retrieval | None for tested plans |
| Valuation lookup failure | None for tested CV/TV/NP (may be partial due to deferred assumptions) |
| Premium calculation failure | None for tested GP/NP |
| Re-open after restart | All 16 tables accessible |

---

## Completion checklist

- [ ] R6B-001 through R6B-060 executed.
- [ ] `rate_import_validation_matrix.csv` fully populated.
- [ ] `qladmin_lookup_trace_template.csv` completed (17 rows).
- [ ] `sandbox_import_manifest.csv` IMPORT_STATUS filled.
- [ ] Results forwarded to project lead.

---

## Regenerate test artifacts

```bash
python plan_analysis/phase_r6b_sandbox_import_execution/_build_r6b_package.py
```
