# Issue #42 — Implementation Notes

**Issue:** #42 — Missing Rate Extract Rows (L01/L10)  
**Framework stage:** Development complete → Ready for Validation  
**Version:** v57.79  
**Date:** 2026-07-13  
**Agent:** Composer 2.5 (Development)

---

## Summary

Implemented **Option A — PDAGE miss-fill** so QLA loads age/duration rates present in CSO’s 2026-07-13 PDAGE extract but absent from `Rate_Table_Extract_Txt.txt`. Segment-only coverage IDs (e.g. `L01 10Y`, `L10 LP9595`) resolve to issuing plans via PCOVRSGT. Rows that would collide with existing parent Rate_Table keys are skipped for direct emit and remain available for **non-CV inheritance** to child plans.

---

## Files changed

| File | Change |
|------|--------|
| `qla_core/pdage_missfill.py` | **New** — PDAGE→Rate_Table merge, mappable-row filter, staging cache |
| `qla_core/rate_pipeline.py` | Merge PDAGE into staging source; segment resolver; summary fields |
| `qla_core/rate_factor_loader.py` | Segment resolve when parent lacks direct RT rows; reject unmapped class tuples |
| `qla_core/plan_source_paths.py` | Prefer PAAGERAT/PDAGE **20260713** |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | Enable `issue42_pdage_missfill`; PAAGERAT 20260713 |
| `Issue_Log_Items/.../approved_first_pass_scope.csv` | Add `L10 LP9595` to L10 child-plan inheritance segments |
| `QLA_Migration/_validate_issue42_pdage_missfill.py` | **New** validation script |
| `app.py` / `QLA_Migration/app.py` | v57.79 |

**Staging artifact:** `QLA_Migration/Staging/rate_table_pdage_missfill_merged.csv` (+ `.sig` cache)

---

## Behavior

1. **Merge:** Copy Rate_Table; append ~68,675 PDAGE rows for `(coverage, type)` keys missing from Rate_Table. Skip when parent policy form already has direct Rate_Table rows (avoids `1L1095` LP95/LP9595 collision).
2. **Segment resolve:** Unmapped segment IDs resolve to plan via PCOVRSGT→crosswalk when parent has no direct RT rows.
3. **Inheritance:** L10 child plans (`1L10OD`, etc.) inherit `L10 LP9595` NP/RV from merged source (manifest updated).
4. **Unmappable PDAGE rows:** Skipped when SEX/BAND/UWCLS don’t map (e.g. L17 `SEX=1` joint rows — 960 rows deferred).

---

## Validation results (`_validate_issue42_pdage_missfill.py`)

| Source segment | Type | Target plan | Table | Grid keys |
|----------------|------|-------------|-------|----------:|
| `L01 10Y` | NP | `5L0110` | QuikNps | 424 |
| `L01 10Y` | RV | `5L0110` | QuikTvs | 424 |
| `L10 LP9595` | NP | `1L10OD` | QuikNps | 3,000 |
| `L10 LP9595` | RV | `1L10OD` | QuikTvs | 3,096 |
| `960 LP85-8` | NP | `196085` | QuikNps | 284 |
| `960 LP85-8` | RV | `196085` | QuikTvs | 284 |
| `L17` | NP | `1L17SP` | QuikNps | 38 |
| `L17` | RV | `1L17SP` | QuikTvs | 38 |

**Rate pipeline:** 0 rate-grid blockers (pre-existing QuikUint PDINT blocker unchanged).

Evidence: `Issue_Log_Items/Issue_42/evidence/issue42_*.csv/json`

---

## Still not loaded (source absent or unmappable)

- `L17` CV, `960 LP85-8` CV — not in PDAGE (CSO still pursuing)
- `0824 P DTH` NP, `L10 GPO OL` NP — not in extracts
- `667 ART 95` — no PCOVRSGT parent mapping
- L17 `SEX=1` joint-classification rows — PDAGE encoding not mapped

---

## Regression guards

- Issue #25 MPOLICY padding — not touched  
- Issue #26 MPREM — not touched  
- Issue #40/#41 CV paths — not touched  
- Existing Rate_Table keys unchanged (miss-fill only)

---

## Next step

**Validation Agent (Grok 4.5)** — full rate emit + regression; publish modified rate tables to `Output/Test_Validation/` on PASS.
