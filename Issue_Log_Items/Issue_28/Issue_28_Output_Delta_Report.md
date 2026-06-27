# Issue #28 — Output Delta Report (v57.34 → v57.35)

**Validation date:** 2026-06-27  
**Baseline:** `Issue_Log_Items/Issue_28/evidence/v57.34_quikplan.csv` (pre-batch snapshot)  
**Current:** `QLA_Migration/Output/` (v57.35 batch)

---

## Row count comparison

| Table | v57.34 | v57.35 | Delta | Status |
|-------|-------:|-------:|------:|--------|
| quikplan.csv | 141 | 141 | 0 | PASS |
| quikridr.csv | 7002 | 7002 | 0 | PASS |
| quikmstr.csv | — | 5083 | — | Unchanged vs #21M baseline |
| quikclid.csv | — | 46753 | — | Unchanged vs #21M baseline |
| quikclnt.csv | — | 13846 | — | Unchanged vs #21M baseline |
| quikprmh.csv | — | 205577 | — | Unchanged vs #21M baseline |
| quikmemo.csv | — | 4380 | — | Unchanged vs #21M baseline |

Protected issue validators confirm row counts match established baselines for all regression tables.

---

## quikplan PLAN field delta

| Metric | Value |
|--------|------:|
| Total rows | 141 |
| PLAN field changes | **33** |
| Expected corrections | 33 |
| Unexpected PLAN changes | **0** |
| FORM changes on affected rows | **0** |
| DESCR changes on affected rows | **0** |

Evidence: `Issue_Log_Items/Issue_28/evidence/v57.35_quikplan_plan_diff.csv`

---

## quikridr MPLAN delta

| Metric | Value |
|--------|------:|
| Total rows | 7002 |
| MPLAN field changes | **262** |
| Row count change | 0 |

MPLAN changes are confined to rows whose source PLAN_CODE maps to one of the 33 corrected catalog entries (plus DISCHO family split).

---

## Unchanged output domains

The following were verified unchanged by protected-issue validators and row-count checks:

- quikmstr / quikclid / quikclnt / quikprmh row counts
- quikmemo population (4380 rows, 4380 unique MEMOKEY)
- MPOLICY width (#25)
- MPREM mapping (#26)
- quikplan FORM and DESCR on all 141 rows (only PLAN changed on 33 rows)

---

## Tables not in scope for delta

Claims tables (quikclmp, quikclms), accounting (quikactg), and rate DBF outputs were not part of Issue #28 scope. No Issue #28 code paths touch these converters.

---

## Decision

**Output delta: PASS** — exactly the expected 33 PLAN corrections; no unintended output drift.
