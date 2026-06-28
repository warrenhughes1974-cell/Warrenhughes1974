# Issue #21J — Rollback Regression Results

**Version:** v57.38  
**Date:** 2026-06-28  
**Baseline compared:** v57.37 (rolled back) vs v57.36 quikmemo behavior (restored)

---

## QUIKMEMO restoration

| Check | v57.37 | v57.38 | Result |
|-------|--------|--------|--------|
| Row count | 5,083 | 4,380 | **PASS** (#21M baseline) |
| Unique MEMOKEY | 5,083 | 4,380 | **PASS** |
| `[CONVERSION]` prefix rows | 5,083 | 0 | **PASS** |
| PNOTE emit | 6,003 | 6,003 | **PASS** |
| PENSE emit | 23,276 | 23,276 | **PASS** |
| Segment rows (pre-merge) | 29,279 | 29,279 | **PASS** |

Sample `010713704C` memo: starts with `[PNOTE]` (no `[CONVERSION]` prefix) — **PASS**.

---

## Unrelated table row counts

| Table | Count | v57.36 baseline | Result |
|-------|-------|-----------------|--------|
| quikmstr.csv | 5,083 | 5,083 | PASS |
| quikridr.csv | 7,002 | 7,002 | PASS |
| quikplan.csv | 141 | 141 | PASS |
| quikclnt.csv | 13,514 | 13,514 | PASS |
| quikprmh.csv | 205,577 | 205,577 | PASS |

---

## Premium field spot checks

| Policy | Field | Value | Result |
|--------|-------|-------|--------|
| 010713704C | quikmstr.MMODEPREM | 43.91 | PASS (unchanged) |
| 010713704C | quikridr.MPREM (phase 1) | 20.07680 | PASS (unchanged) |
| 010713704C | quikplan 1659C2 ANNL | 100.0000 | PASS (unchanged) |

---

## Conclusion

**PASS** — Rollback restores pre-v57.37 quikmemo behavior with no premium or unrelated table regressions detected.
