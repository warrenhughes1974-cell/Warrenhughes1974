# Issue #136 — Validation Report

**Issue ID:** #136  
**Framework stage:** Validation  
**Date:** 2026-08-02  
**Engine:** v58.62  
**Result:** **PASS** (focused Validation; rate tables unchanged — `quikplan` re-enriched)

---

## What was validated

1. Unit tests: `tests/test_#136_real_rate_only_flags.py`, `tests/test_gp_variation_regression.py`, `Issue_Log_Items/Issue_A/scripts/test_issue_a11_a3_rules.py` — **16 passed**
2. Re-enrich `QLA_Migration/Output/quikplan.csv` via `integrate_quikplan_file` against `Output/rates` — validation blockers **0**
3. Gold plan **1658C1** against locked acceptance criteria
4. Fleet scan of Band / State / DV flags
5. Published `Test_Validation/quikplan.csv`; rebuilt/deployed `quikplan.dbf` → `Q:\CSO\CSO_Test_6_30_2026`

---

## 1658C1 gold (PASS)

| Flag group | Result |
|------------|--------|
| Band (`BDVARY*`) | all **N** |
| State (`STVARY*`) | all **N** |
| DV (`*VARYDV`) | all **N** |
| DB (`*VARYDB`) | all **N** (no QuikDbs) |
| GP Gender/UW | **Y** / **Y** (real QuikGps F/M × NS/PR/SM) |
| CV/TV Gender/UW | **Y** where factor grids support |
| `PLANVALOPT` | **Y** (legitimate Gender/UW remain) |
| `PAR` | **0** |

---

## Fleet snapshot (141 plans)

| Metric | Count |
|--------|------:|
| Plans with any `BDVARY*=Y` | **0** |
| Plans with any `STVARY*=Y` | **0** |
| Plans with any `*VARYDV=Y` | **20** (real QuikDvs present) |

---

## Code changes validated

- `derive_plan_flags()` — Band/State require multi-value real differentiation
- `apply_factor_table_pvo_enablement()` — no longer forces Band/Gender from mere CV/TV presence
- `apply_family_factor_presence_gate()` — clears family VARY when factor table empty
- `analyze_rate_segmentation()` — prefers Output/rates CSV keys over stale `emitted_dbf` (prevented false Band from BAND=01 DBF + BAND=00 CSV)

---

## Notes / stop point

- Rate key/factor CSVs were **not** regenerated this Validation (flags only).
- Full conversion rebatch not required for #136 flag materialization; `quikplan` re-enrich is sufficient for UAT of Plan Values Options.
- **Regression / Closure not started** — awaiting user after Luna review / UAT spot-check.
- Backup: `QLA_Migration/Output/quikplan.csv.pre_#136`
