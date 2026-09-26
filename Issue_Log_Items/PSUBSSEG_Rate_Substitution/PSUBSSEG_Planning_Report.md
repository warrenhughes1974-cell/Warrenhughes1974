# PSUBSSEG Rate Substitution — Planning Report

**Date:** 2026-08-31
**Framework stage:** Planning (no code)
**Scope:** Tranche 1 only (data on hand). Tranche 2 reopens when New Era supplies the 13 missing segments.

---

## 1. Design

### New module: `qla_core/psubsseg_substitution_loader.py`

Manifest-gated, mirroring `cv_inheritance_loader.py` / `shared_rate_candidate_loader.py`
architecture (surgical, auditable, no broad PCOVRSGT walk):

1. Parse PSUBS + PSUBSSEG (SEQ slots 1=PR, 2=CV, 12=RV, 13=NP; SEGT_FLAG=Y;
   TYPE_FLAG 0 base; sex-specific bands override `@`).
2. Build per-(coverage, era) authoritative segment map; join PPBEN in-force issue
   dates to derive which eras are populated (only populated eras emit).
3. Emit a **substitution manifest CSV** (evidence artifact) of every
   (plan, rate_type, era, source_segment, effdate) the loader will produce.
4. Feed existing factor-grid machinery (`rate_factor_loader`, `rate_dbf_schema`)
   with the mapped source segments — reuse duration conventions as-is:
   RV identity (#106), CV native-first remap, NP `source_duration - 1`.

### Source data placement

Copy the two extracts into `QLA_Migration/Source/` with family-dated names
(`PSUBS_Substitution_Extract_20260821.csv`, `PSUBSSEG_SubstituteSegment_Extract_20260821.csv`)
so `plan_source_paths` conventions and future dated refreshes apply.
`docs/New_Segments/` stays as the received package.

### Emit plan (Tranche 1)

| # | Plan(s) | Table | EFFDATE band(s) | Source segment | Est. rows |
|---|---|---|---|---|---|
| E1 | `1L10OD` | QuikTvs/QuikNps | keep 19000101 (`L10 LP95`, unchanged); add 19950101 | `L10 LP9595` (PDAGE) | +12,384 |
| E2 | `1L10SO` | QuikTvs/QuikNps | replace 19000101 with `L10 LP95SR`; add 19950101 | `L10SR 95` (PDAGE) | 8,256 net |
| E3 | `10L171`,`10L172`,`117JPO`,`17MJPO` | QuikCvs/QuikNps | 19000101 only (single era) | `L17` (PDAGE) | ~3,936 |
| E4 | `5667AT` | QuikNps | 19000101 | `667 ART` (PAAGERAT) | ~288 src rows |
| E5 | premium-fill plans (12) | QuikGps | 19000101 | PSUBSSEG-confirmed owners (PAAGERAT) | ~2,850 src rows |

- E2 note: current `1L10SO` values match neither authoritative segment
  (overlap 0.08–0.37) — full replacement is intended, and is the reported change.
- `5667AT` RV intentionally not emitted (LifePRO 95-era RV genuinely zero); log in
  Implementation Notes and Completed Issues guide row.

### Key rows (QuikPl*)

Every new EFFDATE band gets companion key rows via `rate_key_setup.build_key_rows()`:
- `QuikPlTv` for RV/NP bands — **assumption fields (MORT/RSVINT/RSVMETH) for the
  19950101 band resolved from the CSO Valuation_Setup / mortality crosswalk**;
  if the crosswalk lacks the 95 basis, copy the existing band's fields and flag
  in the validation report (open item OI-1 below).
- `QuikPlCv` / `QuikPlGp` analogues for E3/E5.

### Config / wiring

- `plan_analysis/phase_r5_rate_loader/rate_loader_config.json`: new
  `psubsseg_substitution` block (paths + enable flag, default on).
- `qla_core/rate_pipeline.py`: invoke after existing inheritance loaders,
  before validation; collisions with #40/#42/#96 emits surface through the
  existing cell-collision BLOCKER gate. PSUBSSEG loader **skips** any
  (plan, table, key) already emitted (first-writer wins stays with shipped fixes;
  differences reported, not overwritten).
- `APP_VERSION` bump in **both** `app.py` (root) and `QLA_Migration/app.py`.

## 2. Validation plan (Stage 6)

Issue validator `_validate_psubsseg_tranche1.py` (issue folder; promoted to
`tools/validators/` at Closure):

1. For each E1–E5 row group: emitted values == source segment values at mapped
   durations (full-grid compare, not spot-check).
2. Era boundary: `1L10OD`/`1L10SO` have both EFFDATE bands; anchor policies'
   bands resolve correctly (9011088338→19000101, 9011103507→19950101, etc.).
3. Key-row completeness: every emitted (plan, gender, uwclass, band, effdate)
   grid has a matching QuikPl* key row (Issue #77 invariant).
4. No new blank/duplicate keys; schema/column order unchanged.

## 3. Regression plan (Stage 7)

- Full rate emit before/after: **byte-identical for every plan not in E1–E5**
  (hard requirement).
- `1L10OD`: existing 19000101 rows byte-identical; only additions.
- Release smokes: `validate_release_closed_issues.py --smoke-only` PASS
  (must not disturb #42/#96/#106/PUA-CV/DV-NATIVE smokes).
- A-checklist (`Issue_A_Conversion_Checklist.md`) evaluated on the batch used
  for validation.

## 4. Open items (non-blocking, resolve during Development)

| ID | Item | Default if unresolved |
|---|---|---|
| OI-1 | 19950101 QuikPlTv basis fields (MORT/RSVINT) for LP9595 / L10SR 95 | Copy existing band's fields; flag in validation report for Eric |
| OI-2 | `5667AT` RV zero handling | Leave absent (documented) |
| OI-3 | Premium-fill list E5 — confirm each plan's PSUBSSEG PR owner emits under correct VARGP mode | Emit only rows whose plan VarGP config accepts attained-age PR (skip + report others) |

## 5. Rollback safety

Loader is a single config-gated additive step; disable flag restores prior emit
exactly (except E2 replacement, which is restorable by disabling and re-running
rate emit). No schema, no field-order, no existing-loader changes.

## Gate criteria

- [x] Planning report published
- [x] Touched-file list explicit (loader, config, pipeline wire, 2× app.py)
- [x] Validation + regression strategy defined
- [x] No code changes made
