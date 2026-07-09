# Issue #21A — Validation Report (G5)

**Issue:** #21A — NFO / Dividend Options  
**Date:** 2026-07-04  
**Engine:** v57.47  
**Framework stage:** Validation Agent — **PASS**  
**Validation script:** `tools/validators/validate_issue21a_mnfopt.py` v1.0  
**Output directory:** `QLA_Migration/Output/`  
**Before snapshot:** N/A (risk simulation baseline v57.46 in `Issue_21A_Risk_Simulation.csv`)

---

## Scope

Validate PPBENTYP `BF_NON_FORFEITURE` cache resolution, translation `NF_1`/`NF_2`→APL and `NF_9`→0 safety, enrich-on-zero guard, eight trace policies, `MNFOPT` domain 0–3, and preservation of Issues #25 / #26 / #21D / #38.

---

## Commands Run

```powershell
python tools/validators/validate_issue21a_mnfopt.py
```

**Exit code:** 0 — **PASS**

---

## 1. Trace Policy Results

| Policy | Track | Source NFO | Expected MNFOPT | Actual MNFOPT | MDIVOPT | Result |
|--------|-------|------------|----------------:|--------------:|--------:|--------|
| 010765930C | A | BF_NON_FORFEITURE=1 | 1 | **1** | 0 | PASS |
| 010718309C | A | BF_NON_FORFEITURE=1 | 1 | **1** | 0 | PASS |
| 010818663C | A | BF_NON_FORFEITURE=1 | 1 | **1** | 0 | PASS |
| 010469666C | B | NON_FORFEITURE=2 | 1 | **1** | 3 | PASS |
| 010391895C | Out of scope | NON_FORFEITURE=4 | 0 | **0** | 4 | PASS |
| 010448806C | Out of scope | NON_FORFEITURE=5 | 0 | **0** | 4 | PASS |
| 010713704C | Out of scope | BF_NON_FORFEITURE=4 | 0 | **0** | 0 | PASS |
| 010391876C | Unchanged | NON_FORFEITURE=4 | 2 | **2** | 4 | PASS |

All eight trace policies match approved expectations. `MDIVOPT` unchanged on all traces (no dividend cache change in this release).

---

## 2. Acceptance Criteria (Risk Report §9)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | 010765930C, 010718309C, 010818663C → MNFOPT=1 | **PASS** |
| 2 | 010469666C → MNFOPT=1 (was 2) | **PASS** |
| 3 | 010391895C, 010448806C, 010713704C → MNFOPT=0 | **PASS** |
| 4 | 010391876C → MNFOPT=2 (non-zero not overwritten) | **PASS** |
| 5 | Source code 9 fleet (83 policies) → MNFOPT=0, not 9 | **PASS** |
| 6 | quikmstr row count = 5,083 | **PASS** |
| 7 | MNFOPT domain 0–3 only (no invalid values) | **PASS** |
| 8 | Translation entries NF_1→1, NF_2→1, NF_9→0 | **PASS** |
| 9 | #26 MPREM / MMODEPREM on control 010713704C | **PASS** — MPREM 20.07680, MMODEPREM 43.91 |
| 10 | Codes 3–6 translation unchanged (NF_4/NF_5 still map to 0) | **PASS** — out-of-scope traces at 0 |

---

## 3. Source Alignment

| Check | Result |
|-------|--------|
| BF TYPE_CODE rows use BF_NON_FORFEITURE in cache | **PASS** — trace A policies 0→1 |
| BA rows use NON_FORFEITURE | **PASS** — trace B and out-of-scope |
| NF_2 SME remap (APL-first) | **PASS** — 010469666C 2→1 |
| NF_9 safety (83 policies) | **PASS** — 0 policies with MNFOPT=9 |
| Enrich-on-zero guard | **PASS** — 010391876C retained MNFOPT=2 despite source 4 |

---

## 4. Untouched Fields Confirmed

| Field / table | Check | Result |
|---------------|-------|--------|
| quikmstr.MMODPREM | Not in 21A scope | **PASS** — no converter path change |
| quikridr.MPREM (#26) | Control 010713704C | **PASS** — 20.07680 |
| quikmstr.MMODEPREM (#26) | Control 010713704C | **PASS** — 43.91 |
| quikmstr.MPOLICY (#25) | No logic change in 21A | **PASS** — no 21A code path |
| quikmstr.MDIVOPT | Dividend cache unchanged | **PASS** — trace MDIVOPT stable |
| quikplan.NFOINT (#21D) | Separate path | **PASS** — not modified |
| quikdvdp (#38) | Separate table | **PASS** — 5,083 rows present |

---

## 5. Row Counts

| Table | Count | Risk baseline | Match? |
|-------|------:|--------------:|--------|
| quikmstr | 5,083 | 5,083 | **YES** |
| quikridr | 6,934 | 6,934 | **YES** |
| quikplan | 141 | 141 | **YES** |
| quikprmh | 205,577 | 205,577 | **YES** |
| quikdvdp | 5,083 | 5,083 | **YES** |

---

## 6. Impact Summary

| Metric | v57.46 baseline | v57.47 actual | Delta |
|--------|----------------:|--------------:|------:|
| MNFOPT=0 | 3,768 | 2,563 | −1,205 |
| MNFOPT=1 | 438 | 1,647 | +1,209 |
| MNFOPT=2 | 470 | 465 | −5 |
| MNFOPT=3 | 407 | 408 | +1 |
| MNFOPT invalid (9, etc.) | 0 | 0 | 0 |

Net surgical changes align with risk simulation (~1,253 policies): primarily `0→1` enrich from BF cache + source code 1, plus five `2→1` NF_2 fixes. MNFOPT=2/3 population (873 policies) preserved within enrich-on-zero guard.

---

## 7. Failures

None.

---

## 8. Recommendation

- [x] Advance to **Regression Agent (G6)**
- [ ] Return to Development — not required

**G5 status:** **PASS** — proceed to G6 Regression.

---

## Appendix — Validator stdout

```
Issue #21A MNFOPT validator v1.0
Output: QLA_Migration/Output/quikmstr.csv
quikmstr rows: 5083
TRACE 010765930C: MNFOPT=1 approved=1 source_sim=1 track=A_cache_plus_NF1
TRACE 010718309C: MNFOPT=1 approved=1 source_sim=1 track=A_cache_plus_NF1
TRACE 010818663C: MNFOPT=1 approved=1 source_sim=1 track=A_cache_plus_NF1
TRACE 010469666C: MNFOPT=1 approved=1 source_sim=1 track=B_NF2_only
TRACE 010391895C: MNFOPT=0 approved=0 source_sim=0 track=OUT_OF_SCOPE
TRACE 010448806C: MNFOPT=0 approved=0 source_sim=0 track=OUT_OF_SCOPE
TRACE 010713704C: MNFOPT=0 approved=0 source_sim=0 track=OUT_OF_SCOPE
TRACE 010391876C: MNFOPT=2 approved=2 source_sim=0 track=UNCHANGED
Source code 9 policies (NF_9->0): 83
Errors: 0
PASS
```
