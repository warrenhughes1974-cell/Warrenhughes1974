# Issue #31 — Phase 1 QUIKCVS Implementation Notes

**Date:** 2026-06-30 (updated — V-CVS-05 PDAGE parity closure)  
**PR:** PR-1 Phase 1 — QUIKCVS  
**Version baseline:** v57.39 (no `app.py` change — R5 dry-run path only)  
**Authority:** `docs/research/ISWL_Implementation/`

---

## Summary

Phase 1 wires ISWL QUIKCVS validation onto the **existing R5 Rate_Table → QuikCvs → QuikPlCv** pipeline. No new loader or emit path was required: `TYPE_CODE=CV` was already mapped to `QuikCvs` in `rate_dbf_schema.py`. Work focused on config, validation helpers, and gate scripts.

**Authoritative source for Phase 1 emit:** `Rate_Table_Extract_20260427.csv` (not PDAGE).

---

## Files modified

| File | Change |
|------|--------|
| `qla_core/rate_factor_loader.py` | Added `ISWL_COVERAGE_IDS`, `quikcvs_keys_by_plan()` for Phase 1 validation (no emit filter) |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | **New** — R5 config with PSEGT, PDAGE, CSO crosswalk, ISWL Phase 1 metadata |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.example.json` | Synced ISWL Phase 1 keys (PSEGT, PDAGE, CSO, `iswl_phase1`) |

**Not modified (not required):**

- `qla_core/rate_pipeline.py` — existing `transform_source()` + CSO assumptions already emit QuikCvs/QuikPlCv
- `QLA_Migration/app.py` — no integration change in Phase 1

---

## New files

| File | Purpose |
|------|---------|
| `tools/validators/iswl_common.py` | Shared config paths, ISWL coverage set, Phase 1 output dir |
| `tools/validators/iswl_psegt_cv_gate.py` | V-CVS-01 — PSEGT CV 8/8 gate |
| `tools/validators/iswl_quikcvs_parity.py` | V-CVS-05 — Rate_Table vs PDAGE parity (non-blocking) |
| `tools/validators/iswl_quikcvs_reconcile.py` | V-CVS-02–04, V-X-01, V-X-03 — pipeline reconcile + regression |
| `Issue_Log_Items/Issue_31/iswl_quikcvs_regression_baseline.json` | Non-ISWL regression baseline (36 QuikCvs plans) |
| `Issue_Log_Items/Issue_31/Phase1_QUIKCVS/*` | Validation artifacts (see below) |

---

## Validation results

### Checklist

| ID | Check | Result |
|----|-------|--------|
| V-CVS-01 | PSEGT CV 8/8 | **PASS** |
| V-CVS-02 | Rate_Table CV rows for 8 coverages | **PASS** (72,271 ISWL CV rows) |
| V-CVS-03 | Zero grid collisions | **PASS** (V03 = 0) |
| V-CVS-04 | CSO crosswalk 8/8 MPLANs | **PASS** |
| V-CVS-05 | PDAGE parity | **PARTIAL / NEEDS REVIEW** — 8/8 MPLANs covered; 10.44% shared-key match (threshold 99.5%); Rate_Table authoritative |
| V-X-01 | Non-ISWL regression | **PASS** |
| V-X-03 | QuikPlNb EFFDATE = 19000101 | **PASS** (0 blockers) |

### ISWL QuikCvs distinct keys by MPLAN

| MPLAN | Distinct keys |
|-------|---------------|
| 1658C1 | 1,947 |
| 1658CS | 979 |
| 1659C2 | 1,045 |
| 1659CR | 1,045 |
| 1659CS | 997 |
| 1659SR | 1,047 |
| 1669SR | 264 |
| 1679CS | 465 |
| **Total ISWL** | **7,789** |

Pipeline dry-run: `blocker_count=0`, `emit_ready=true`, global QuikCvs distinct keys = 25,717 (36 plans).

### Artifacts

| Path | Content |
|------|---------|
| `plan_analysis/phase_r5_rate_loader/dryrun_summary.json` | Full R5 dry-run summary |
| `plan_analysis/phase_r5_rate_loader/dryrun_validation_issues.csv` | All validation issues |
| `plan_analysis/phase_r5_rate_loader/age_cap_audit.csv` | AGE cap audit |
| `Issue_Log_Items/Issue_31/Phase1_QUIKCVS/iswl_quikcvs_reconcile_summary.json` | Phase 1 reconcile summary |
| `Issue_Log_Items/Issue_31/Phase1_QUIKCVS/iswl_quikcvs_keys_by_mplan.csv` | MPLAN key counts |
| `Issue_Log_Items/Issue_31/Phase1_QUIKCVS/iswl_psegt_cv_gate_report.csv` | PSEGT CV gate detail |
| `Issue_Log_Items/Issue_31/Phase1_QUIKCVS/iswl_quikcvs_parity_report.md` | PDAGE parity report (V-CVS-05) |
| `Issue_Log_Items/Issue_31/Phase1_QUIKCVS/iswl_quikcvs_parity_by_coverage.csv` | Per-MPLAN parity metrics |

### Run commands

```text
python tools/validators/iswl_psegt_cv_gate.py
python tools/validators/iswl_quikcvs_reconcile.py
python tools/validators/iswl_quikcvs_parity.py
python plan_analysis/phase_r5_rate_loader/rate_loader_dryrun.py
```

---

## Regression

Baseline captured in `Issue_Log_Items/Issue_31/iswl_quikcvs_regression_baseline.json`:

- Global `blocker_count` must remain 0
- Non-ISWL plan QuikCvs key counts must be unchanged (36 plans tracked)

Reconcile re-run without `--write-baseline`: **PASS**.

---

## V-CVS-05 — PDAGE parity closure (2026-06-30)

PDAGE delivered to `QLA_Migration/Source/PDAGE_AgeDuration_Rates_Extract_20260530.csv`.

| Metric | Value |
|--------|------:|
| Rate_Table ISWL CV keys | 72,271 |
| PDAGE ISWL CV keys | 12,084 |
| Shared keys | 12,084 |
| Keys only Rate_Table | 60,187 |
| Keys only PDAGE | 0 |
| Matched values (shared keys) | 1,262 (10.44%) |
| Mismatched values | 10,822 |
| Max delta | 968.0 |
| MPLANs with PDAGE rows | 8/8 |

**Verdict:** **PARTIAL / NEEDS REVIEW** — parity study complete; match rate well below 99.5% SME threshold. **Rate_Table remains authoritative.** No loader change required.

---

## Known issues

None blocking Phase 1.

- 705 WARNING-level dry-run issues (V10 precision reduced, V15 assumption deps, AGE cap audits) — pre-existing R5 behavior, non-blocking.
- PDAGE vs Rate_Table systematic value divergence on shared keys — SME review required before any CV source switch (not a Phase 1 blocker).

---

## Deferred

| Item | Reason |
|------|--------|
| PDAGE as CV source | Parity 10.44% on shared keys — below 99.5% threshold; SME decision required |
| PDAGE source switch | Blocked until SME explains divergence / confirms alternate mapping |
| `app.py` rate CSV emit integration | Phase 1 scope = R5 dry-run + validators only |
| Optional QuikCvs.csv / QuikPlCv.csv in Output | Not emitted in Phase 1 (dry-run in-memory only) |

---

## Regression risk

**Low.** Changes are additive:

- Validation helpers and scripts only inspect pipeline output
- No change to `transform_source()` logic, TYPE routing, or grid pivot
- No ISWL emit filter on global dry-run (allowlist used for validation reporting only)

---

## Recommended next step

**Phase 2 — QUIKGPS:** Extend PAAGERAT attained-age loader for `TYPE_CODE=BP` → `QuikGps` / `QuikPlGp` per `ISWL_Development_Order.md`. Do not begin until Phase 1 is approved.

V-CVS-05 parity study is **closed** (PDAGE on disk; report generated). Obtain SME sign-off on Rate_Table authority before PR-1 merge. Do not switch CV routing to PDAGE without SME resolution of 10.44% match rate.
