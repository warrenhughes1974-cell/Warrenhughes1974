# Issue #158 — Dependency Gate

**Issue:** #158 — PR rates attributed to the wrong QLAdmin plan
**Framework stage:** Dependency Gate (G2)
**Generated:** 2026-08-29
**Status:** **PASS**

---

## Checklist

### Source data

| Check | Met? |
|---|---|
| Required LifePRO extract present | **Met** — `PAAGERAT_AttainedAge_Rates_Extract_20260731.csv` |
| Segment list source present | **Met** — `plan_analysis/source_data/coverage/PCOVRSGT.csv` with `SEQ`, `SEGT_FLAG`, `SEGT_ID` |
| Parent coverage source present | **Met** — `PCOVR.csv` |
| Crosswalk present | **Met** — `plan_analysis/source_data/crosswalk/Policy_Form_Crosswalk.csv` |
| Corroborating source present | **Met** — `docs/New_Segments/PSUBSSEG_SubstituteSegment_Extract_20260821.csv` |
| Extract date matches Output under test | **Met** — 20260731 package aligned with current `Output/rates/QuikGps.csv` |
| Re-extract required? | **N/A** — the defect is in resolution, not in the data |

### Field definitions

| Check | Met? |
|---|---|
| QLAdmin target table confirmed | **Met** — `rates/QuikGps` + `QuikPlGp` keys, `quikplan.VARGP` |
| LifePRO source semantics confirmed | **Met** — `SEQ` = rate-type slot (1=PR, 2=CV, 12=RV, 13=NP) |
| Slot semantics independently corroborated | **Met** — New Era `PSSUBSSEG_SegtFlag_Query.sql` **and** PSUBSSEG `SEGT_FLAG=N` at SEQ 1 for `619 SPS PU` / `622 END85` |
| Transformation notes identified | **Met** — filter `SEQ=1`; return every owning coverage, not one |
| Fallback rule needed for unresolved segments | **N/A** — simulation shows 0 of 91 PR segments lack a SEQ 1 owner |

### Client clarification

| Check | Met? |
|---|---|
| Scope boundary agreed | **Met** — Warren 2026-08-29: PR only first, CV/RV/NP as follow-up |
| Business rule for edge cases | **Met** — plans with no SEQ 1 segment correctly become `VARGP=4` |
| UAT acceptance criteria stated | **Met** — each of the 12 screenshots must reproduce on its own plan and be absent from the wrong one |
| Outstanding client questions | Q1–Q3 in Planning — **non-blocking**, corroborating only |

### Evidence

| Check | Met? |
|---|---|
| Example plans/segments identified | **Met** — 20 mis-attributed segments (14 moved + 6 fan-out), 18 gaining plans, 8 losing plans enumerated |
| Before-state measurable | **Met** — `evidence/issue158_slot_resolution_summary.json`, `issue158_segment_replan.csv` |
| Gold anchors from client | **Met** — 12 LifePRO screenshots, `docs/Rate_Validation/` |
| Discovery notes | **Met** |

### Regression guards

| Check | Met? |
|---|---|
| Plan preserves Issue #138 PR SEQ offset | **Met** — values untouched; only attribution moves |
| Plan preserves Issue #140 slot axis | **Met** |
| Plan preserves Issue #71 band collapse + priority | **Met** |
| Plan preserves Issue #118 form-aware UWCLASS | **Met** — same mapping, applied on the correct plan |
| Plan preserves PUA-CV Closed row | **Met** — CV path untouched; `261PUA`/`280PUA` keep inherited CV |
| Plan preserves ISWL BP path | **Met** — BP loader unchanged; `1658CS`/`1669SR` keep BP-sourced `QuikGps` |
| Plan leaves CV / RV / NP / COI / Rate_Table / PDAGE resolution unchanged | **Met** — new method, PR opt-in only |
| Plan preserves #25/#26 anchors | **Met** — rate path only, no `quikmstr`/`quikridr` writes |

---

## Gate result

**PASS** — Framework auto-chain continues to Risk in this session.

Accepted assumptions (documented for Risk/Dev):

1. `PCOVRSGT.SEQ=1` with `SEGT_FLAG=Y` is authoritative for premium-rate ownership. Two
   independent LifePRO sources support this; Eric confirmation is corroborating, not gating.
2. A plan with no `SEQ=1` segment legitimately has no premium rate table; `VARGP=4` is correct
   and the grid it shows today is another coverage's.
3. `170858` gaining a grid across 147 active policies is an intended correction, subject to UAT.
4. CV / RV / NP carry the same defect and stay untouched in this pass.

## Blockers

None.

## Recommended tracking status

**Dependency Gate PASS → Risk Complete (pending Dev approval)**
