# PSUBSSEG Rate Substitution — Implementation & Validation Report

**Date:** 2026-09-01
**Engine:** v59.06 (APP_VERSION bumped in root `app.py` and `QLA_Migration/app.py`)
**Stage:** Development + Validation complete; full batch and DBF package in progress.

---

## 1. What shipped

| Piece | Path |
|---|---|
| Scope builder | `Issue_Log_Items/PSUBSSEG_Rate_Substitution/tools/build_psubsseg_scope.py` |
| Scope manifest (reviewed) | `Issue_Log_Items/PSUBSSEG_Rate_Substitution/psubsseg_substitution_scope.csv` — 50 entries (42 EXTRACT / 8 PLAN_COPY) |
| Loader | `qla_core/psubsseg_substitution_loader.py` — streams IN_SCOPE cells from merged PDAGE with full page expansion; applies PLAN_COPY post-grid |
| Pipeline wiring | `qla_core/rate_pipeline.py` — config-gated (`psubsseg_substitution.enabled`), passes manifest (PLAN, EFFDATE) pairs to validation |
| Validation exemption | `qla_core/rate_validation.py` — V07 skips only manifest-listed (PLAN, EFFDATE) generations; everything else still must be 19000101 |
| Config | `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` → `psubsseg_substitution` block |
| Fail-closed validator | `tools/validators/validate_psubsseg_substitution.py` |
| Release smoke | Registered in `SMOKE_JOBS` (`validate_release_closed_issues.py` v2.0), guide high-risk row **PSUB** |

## 2. Source data (0831 package)

`QLA_Migration/Source/LifePRO_Extracts_20260831.zip` delivered all 13 previously-missing segments:

- **PDAGE 0831** (strictly additive, 22 new (coverage,type) pairs — NP/RV for 11 segments): `619 DT 95`, `619CHPU95`, `619DTCH95`, `619DTSP95`, `619SPPU95`, `670 GL858`, `670GL858NL`, `L01 10Y 95`, `L05 10Y 95`, `L07 5Y 95`, `L10 CDT 95`.
- **PAAGE/PAAGERAT 0831** (strictly additive): `667 ART 95` NP (304 rows, attained-age as New Era said) + `991 PWL73` PR (51 rows — no PCOVRSGT SEQ-1 owner, does not emit; noted for Eric).

## 3. Validation results (rates emit, pre-full-batch)

- Emit: **SUCCESS, 0 blockers**, 23 tables / 253,610 rows.
- **A/B isolation** (loader ON vs loader OFF on identical source/code): additions only —
  QuikTvs +37,016; QuikNps +34,114; QuikCvs +1,464 (L17 children); QuikPlTv +68/−2 (the −2 are 5667AT/719CDT placeholder 19000101 key rows correctly replaced by real 19950101/19910101 generations); first-time plan key rows for 5667AT and 719CDT. **QuikGps untouched by the loader.**
- **Fail-closed validator: PASS** — 633,044 expected cells independently recomputed from merged PDAGE, 633,044 matched; PLAN_COPY generations byte-match base; key rows present per generation. 1,056 BAD_VALUE = known joint-life L17 NP rows (SEX=1/BAND=S) the standard pipeline also skips — question logged for Eric.
- **Release smoke gate:** new PSUB job **PASS**; #106 updated to pin the 19000101 generation (era generations share PLAN; 19000101 rows proven byte-identical).

## 4. Regression findings (important, not caused by this change)

Comparing against the 8/30 snapshot exposed **81 QuikGps rows changing across 6 plans** (`1L10OD`, `1L10PR`, `5L0110`, `5L0510`, `5L075Y`, `7686S3`). Root cause proven by control run (loader disabled, diffs persist) and file forensics:

1. These plans have **sibling PAAGERAT PR segments under the same parent carrying different values** for the same grid cells.
2. `build_factor_grid` resolves that contention by **stream order — first row wins** (`rate_factor_loader.py` sibling-PAAGERAT branch).
3. New Era **re-sorted the 0831 PAAGERAT extract**, so a different sibling now comes first and contended cells flipped.

Only my three files changed since the snapshot build and all are no-ops with the loader off — this is a **pre-existing order-sensitivity** exposed by the extract re-sort, not a PSUBSSEG defect. The six coverages are the same era-variant families PSUBSSEG describes; the proper fix is era-banding PR the same way (Tranche follow-up / Eric guidance), or a deterministic tiebreak. **Flagged to Warren — do not treat snapshot GP values as authoritative for these 6 plans.**

Pre-existing release-gate failure also observed (predates this work): **#59 MSTATUS** — Output `quikmstr.csv` built 8/30 shows 23 status changes vs the validator's 0630 expectations (e.g. 50→53 death-claim rows, 22→55). Re-check after the fresh full batch; if it persists it needs its own investigation (possibly intentional Issue #133-era status work with a stale #59 baseline).

## 5. Open items for Eric

1. Joint-life NP rates (L17 NP rows with SEX=1/BAND=S) — 264 source rows skipped by both the standard pipeline and this loader.
2. `991 PWL73` PR page (new in 0831) has no PCOVRSGT SEQ-1 owner and therefore does not emit — which plan should own it?
3. PR-side era banding for the six sibling-contended plans above (PSUBSSEG lists PR sequences too; current scope is CV/RV/NP only).
