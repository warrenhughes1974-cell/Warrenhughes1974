# R5 — Rate Loader Implementation Plan

Implementation has begun. The `qla_core` rate modules are built and exercised end-to-end by a
**dry run that emits no DBFs**. Both R5 business clarifications are incorporated: overflow plans
are not blocked (see `physical_field_validation.md`) and actuarial assumptions are deferred,
configurable placeholders (not blockers).

## Modules delivered (`qla_core/`)

| Module | Responsibility | Key surface |
|---|---|---|
| `rate_dbf_schema.py` | Canonical schemas + crosswalks + CHAR(7) formatter | `factor_table_fields`, `key_table_fields`, `format_factor`, `map_sex/band/uwclass`, `duration_to_cntl_col`, `TYPE_TO_TABLE`, `KEY_TABLE` |
| `rate_factor_loader.py` | Crosswalk load, transform, pivot to grid, materialize rows | `load_plan_crosswalk`, `transform_source`, `build_factor_grid`, `grid_to_factor_rows`, `LoaderConfig` |
| `rate_key_setup.py` | Derive `QuikPlxx` keys; externalized assumptions | `build_key_rows`, `AssumptionProvider` |
| `rate_validation.py` | R4 validation matrix as gated checks | `validate`, `blockers` |
| `rate_dbf_writer.py` | Rollback-safe DBF emit (R5+; **not invoked in dry run**) | `write_factor_table`, `write_key_table` |

## Confirmed structures the loader emits

**Factor tables** (`QuikGps/QuikCvs/QuikDbs/QuikDvs/QuikNps/QuikTvs`), field order:
```
PLAN(C6) AGE(C2) CNTL(C2) <PFX>0..<PFX>9(C7 each) GENDER(C1) UWCLASS(C2) BAND(C2)
ISSCNTRY(C4) ISSUEST(C2) EFFDATE(D8)
```
**Rate-key tables**: `PLAN GENDER UWCLASS BAND ISSCNTRY ISSUEST EFFDATE` (+ `QuikPlCv`: MORT,
ETIMORT, NFOINT, INTMETHCV; + `QuikPlTv`: MORT, RSVINT, RSVMETH, INTMETHTV, STOREMEANS, CALCMIDS;
`QuikPlTv` shared by NP).

## Transformation (all validated in R3, now codified)
PLAN via crosswalk (col A→C) · SEX F/M/J · BAND 1/2/3→01/02/03 · UWCLASS 0/N/S/P/B→00/NS/SM/PR/ST ·
`QL_DURATION = SOURCE_DURATION − 1` · `CNTL = QL_DURATION//10`, column `= QL_DURATION%10` · long→wide
pivot into the `xx0..xx9` grid · `format_factor` writes the 7-char text (adaptive precision, no scaling).

## Validation strategy (gated; zero BLOCKERs required before emit)
Driven by `rate_emit_validation_matrix.csv` (R4). Severities: **BLOCKER** (must pass) / **WARNING**
(reported, non-blocking). Per clarification #2, deferred assumptions (`V15`) and placeholder EFFDATE
(`V07`) are WARNINGS. Capacity (`V10`) blocks only `DOES_NOT_FIT` (currently **0**); precision
reduction is a WARNING. Other gates: PLAN authority/space (V01/V02), duplicate factor & key rows
(V03/V04), orphan/empty keys (V05/V06), AGE/CNTL validity (V08/V09), segmentation present (V11),
crosswalk domains (V12), excluded-not-emitted (V14, by construction).

## Sample execution flow (dry run — no DBFs)
```
python plan_analysis/phase_r5_rate_loader/rate_loader_dryrun.py
```
1. Load externalized config (`rate_loader_config.example.json`) + authoritative crosswalk.
2. `transform_source` → classify (IN_SCOPE / EXCLUDED / rejected) + apply crosswalks/paging.
3. `build_factor_grid` → pivot to keyed grid; `grid_to_factor_rows` → 7-char-formatted rows.
4. `build_key_rows` → distinct `QuikPlxx` keys with externalized (possibly blank) assumptions.
5. `validate` → issue list + summary. Writes `dryrun_summary.json` + `dryrun_validation_issues.csv`.
6. **No DBF written.** `rate_dbf_writer` is the single audited path reserved for the emit step.

### Latest dry-run result
- IN_SCOPE **774,400**; EXCLUDED **354,584** (7 codes inventoried).
- Factor rows: GP 1,123 · DV 3,978 · DB 1,380 · CV 25,720 · TV 26,097 · NP 26,650.
- Key tables: QuikPlGp 13 · QuikPlDv 20 · QuikPlDb 12 · QuikPlCv 70 · QuikPlTv 112 (TV+NP shared).
- Validation: **3 BLOCKERs**, the rest WARNINGS. `format does_not_fit = 0`, `precision_reduced = 260`.

## AGE > 99 capping (business rule — implemented, audited)
QLAdmin `AGE` is `C2` (0–99). Business decision: **AGE > 99 → 99**, applied during factor-row
generation with preserved lineage (`original_age` retained), classified as WARNING
`AGE_CAPPED_TO_99` (never a blocker, rows never discarded). Audit: `age_cap_audit.csv`
(PLAN, TYPE_CODE, ORIGINAL_AGE, EMITTED_AGE, ROW_COUNT).

Capping can collide with genuine AGE-99 data. Collision precedence (implemented in
`build_factor_grid`): **genuine (non-capped) data always wins**; the colliding capped cell is
dropped and audited (`AGE_CAP_COLLISION_RESOLVED`, `age_cap_collision_audit.csv`). Two genuine
cells colliding remains a real `V03` blocker. Observed: plan `1L10OD` — 3 capped cells (terminal
CV=0.00) collided with genuine AGE-99 (CV=1000.00); genuine values retained (verified in emit).

## Guarded emit (implemented)
`rate_loader_emit.py` writes factor + rate-key DBFs **only when `BLOCKER_COUNT == 0`**, to an
isolated rollback-safe directory (`emitted_dbf/`) via `rate_dbf_writer` (temp + atomic replace);
source/reference DBFs are never touched. Current gate: **0 blockers → emit proceeds**, writing 11
tables (6 factor + 5 key), 85,172 rows. EFFDATE is fixed at `19000101`; ISSCNTRY/ISSUEST +
actuarial assumptions remain configurable placeholders. Run `--dry-run` to validate without writing.

## EFFDATE standard (R5.1 — authoritative)
- **`EFFDATE = 19000101` everywhere** (all factor + key tables). Single rate generation; no
  effective-date / alternate / plan-specific variants. The `00000000` placeholder is removed.
- Validation `V07` is now a **BLOCKER** when `EFFDATE != 19000101` (factor and key rows).
- Post-emit `effdate_verification.py` confirms every emitted table has
  `DISTINCT_EFFDATE_VALUES = 19000101`, 0 blanks, 0 zeros (all 11 tables PASS).

## Deferred / configurable dependencies (non-blocking per clarification #2)
- **ISSCNTRY/ISSUEST** defaults (`0000`/`00`) — confirm or override per state/country variation.
- **Actuarial assumptions** (MORT/RSVINT/RSVMETH/INTMETH*/ETIMORT/NFOINT/STOREMEANS/CALCMIDS) —
  loaded later via `AssumptionProvider` from the completed assumption mapping CSV; blank placeholders
  until then. CV/TV/NP keys generate now and absorb assumptions when supplied.

## Recommended emit order (R5 emit step, after blockers cleared)
1. **PR / QuikGps** → 2. **DV / QuikDvs** → 3. **DB / QuikDbs** → 4. **CV / QuikCvs** →
5. **RV / QuikTvs** → 6. **NP / QuikNps** (via shared `QuikPlTv`). Each emit gated on zero BLOCKERs
for that family and routed through `rate_dbf_writer` (rollback-safe atomic publish).
