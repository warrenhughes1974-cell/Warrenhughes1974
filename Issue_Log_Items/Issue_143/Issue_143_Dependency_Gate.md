# Issue #143 — Dependency Gate

**Issue:** #143 — Units Incorrect (RPU)  
**Framework stage:** Dependency Gate (G2)  
**Generated:** 2026-08-18  
**Status:** **PASS**

---

## Checklist

### Source data

| Check | Met? |
|---|---|
| Required LifePRO extract(s) present | **Met** — PPOLC, PPBEN, PPBENTYP `*_20260630.csv` |
| Extract row count > 0 | **Met** — 304 RU; 105 BF seq-1 |
| Column headers documented | **Met** — DD = `BF_CURRENT_DB` (col 108) |
| Extract date/version matches batch under test | **Met** — 20260630 Source + current Output |
| Re-extract required? | **N/A** — re-count on 7/31 at Development if that cut is next |

### Field definitions

| Check | Met? |
|---|---|
| QLAdmin target table confirmed | **Met** — `quikridr.MUNIT` |
| QLAdmin target field semantics confirmed | **Met** — units of coverage; Amount Ins = `MUNIT × MVPU` |
| LifePRO source field semantics confirmed | **Met** — units vs `BF_CURRENT_DB` (research + SME) |
| Transformation notes identified | **Met** — `MUNIT = DD / VPU` when mismatch > 0.01 |

### Client clarification

| Check | Met? |
|---|---|
| Scope boundary agreed | **Met** — BF RPU mismatch only; BA and aligned BF out |
| Business rule for edge cases | **Met** — SME 2026-08-18 on `9010757606` |
| Retention / filtering | **N/A** |
| UAT acceptance criteria stated | **Met** — Amount Ins = Column DD on the 23; controls unchanged |

### Evidence

| Check | Met? |
|---|---|
| Example policies identified | **Met** — 23 candidates + aligned/BA controls |
| Screenshots | **N/A** — Source + Output measurable |
| Before-state measurable | **Met** — all 23 Output `MUNIT` still equal unreduced source units |

### Regression guards

| Check | Met? |
|---|---|
| Plan preserves Issue #2 MPOLICY | **Met** |
| Plan preserves Issue #26 MPREM | **Met** — out of write set |
| Plan preserves Issue #55 floor / emit | **Met** — run after remap |
| Plan preserves Issue #108A MSAVE blank | **Met** — do not write `MSAVEUNIT` |
| Plan does not alter unrelated rulebooks | **Met** |

---

## Gate result

**PASS** — Framework auto-chain continues to Risk in this session.

Accepted assumptions:

1. Remap all 23 (status 45 / 53 / 55), not in-force 45 only.  
2. `VALUE_PER_UNIT` remains $1,000; formula is still `DD / VPU`.  
3. QuikIswl `MDB` may move on the next ISWL seed because #124 uses `MUNIT × 1000`. That follows #124; it does not undo it.

## Blockers

None.

## Recommended tracking status

**Dependency Gate PASS → Risk Complete (pending Dev approval)**
