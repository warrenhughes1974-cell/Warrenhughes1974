# Issue #42 — Dependency Gate

**Issue:** #42 — Missing Rate Extract Rows (L01/L10)  
**Framework stage:** Dependency Gate (G2)  
**Generated:** 2026-07-13  
**Model:** Cursor Grok 4.5  

---

## Gate verdict

**BLOCKED for Development** — Issue #42 source rows now exist in `PDAGE_…_20260713.csv`, but the file the converter loads for age/duration (`Rate_Table_Extract_Txt.txt`) still has **0** rows for `L01 10Y` and `L10 LP9595`. Choose Option A (PDAGE miss-fill) or Option B (CSO Rate_Table refresh) before Risk→Development.

**Conditional pass for Risk Agent** is allowed to size Option A vs B only (no coding).

---

## Dependency Checklist

### Source data

| Check | Met? | Notes |
|-------|------|-------|
| Required LifePRO extract(s) present in `QLA_Migration/Source/` | **Met (PDAGE)** / **Missing (Rate_Table keys)** | PDAGE + PAAGERAT + PAAGE dated 20260713 present |
| Extract row count > 0 for #42 IDs | **Met in PDAGE** | L01 10Y NP/RV 2544; L10 LP9595 NP/RV 6192 |
| Column headers documented | **Met** | COVERAGE_ID, TYPE_CODE, AGE, SEX, BAND, UWCLS, DURATION, VALUE1… |
| Extract date/version matches batch under test | **Partial** | New files 20260713; loader still on Rate_Table_Txt + PAAGERAT 20260630 |
| Re-extract required? | **Yes if Option B** | Rate_Table twin must include L01 10Y + L10 LP9595 |

### Field definitions

| Check | Met? | Notes |
|-------|------|-------|
| QLAdmin target table confirmed | **Met** | QuikNps (NP), QuikTvs (RV) |
| QLAdmin target field semantics confirmed | **Met** | Existing rate emit schema |
| LifePRO source field semantics confirmed | **Met** | Age/duration; STORAGE_FORMAT D; VALUE1 |
| Transformation notes identified | **Met** | UWCLS↔UNDERWRITING_CLASS; VALUE1→VALUE |

### Client clarification

| Check | Met? | Notes |
|-------|------|-------|
| Scope boundary agreed (in / out) | **Partial** | #42 NP/RV in; inventing 0824/GPO NP out; L17/LP85-8 CV = separate CSO track |
| Business rule for edge cases | **Met** | Do not invent missing NP/CV |
| Retention / filtering rules | **N/A** | |
| UAT acceptance criteria stated | **Partial** | Need: QuikNps/QuikTvs non-zero for 5L0110 + L10 LP9595 after load |

### Evidence

| Check | Met? | Notes |
|-------|------|-------|
| Example policies identified | **N/A** | Plan-level extract gap |
| Screenshots or docx support client claim | **Met** | Prior L01/L10 docx + Segment References |
| Before-state measurable from current output | **Met** | 0 Rate_Table rows; prior QuikNps 5L0110=0 |

### Regression guards

| Check | Met? | Notes |
|-------|------|-------|
| Plan preserves Issue #25 MPOLICY padding | **Met** | Rates-only |
| Plan preserves Issue #26 MPREM mapping | **Met** | Rates-only |
| Plan does not alter unrelated rulebooks | **Met** | Path/merge only if Option A |

---

## Open blockers (must clear before Development)

1. **Path decision:** Option A (QLA PDAGE miss-fill) vs Option B (CSO Rate_Table re-extract).  
2. **Residual CSO (not #42 load blockers but client-visible):** `L17` CV, `960 LP85-8` CV still missing from PDAGE.  
3. Optional: bump PAAGERAT resolver to 20260713 (PR additions; not required for #42 NP/RV).

---

## Eric reply facts (for Warren)

| Item | QLA finding |
|------|-------------|
| L01 10Y NP / L10 LP9595 NP+RV | **Now in PDAGE 20260713** — QLA must wire/load |
| L17 CV | Still **missing** — keep with New Era |
| 960 LP85-8 CV | Still **missing** — keep with New Era |
| 960 LP85-8 NP/RV | **Present** in PDAGE (1128 each) — clarify with Eric if he meant only CV |
| 0824 P DTH NP | **Absent** — agree with New Era |
| L10 GPO OL NP | **Absent** — agree with New Era (PR now in PAAGERAT) |

---

## Next agent

- **Risk Agent (Grok 4.5)** — Option A vs B impact / go-no-go  
- Do **not** start Development until Option chosen and this gate re-run to **PASS**
