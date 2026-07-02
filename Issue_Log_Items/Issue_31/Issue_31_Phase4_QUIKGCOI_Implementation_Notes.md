# Issue #31 — Phase 4 QUIKGCOI Implementation Notes

**Date:** 2026-06-30  
**PR:** PR-4 Phase 4 — QUIKGCOI  
**Prerequisite:** PR-3 Phase 3 QUIKCOI approved

---

## Summary

Phase 4 adds ISWL guaranteed COI rates via **PAAGERAT TYPE=U5 → QuikGcoi** (VARGP=3 attained-age scalar). Reuses the Phase 3 UL COI loader core with a minimal U5 extension.

**Transform:**

```text
PAAGERAT (TYPE=U5) → SegmentResolver → QuikGcoi
  SEQ → AGE, CNTL=00, VALUE_INFO → QX0, QX1–QX9 blank
```

---

## Files modified

| File | Change |
|------|--------|
| `qla_core/paagerat_ul_coi_loader.py` | Refactored shared `transform_paagerat_ul_scalar()`; added U5/`transform_paagerat_u5()`; GCOI plan-set helpers |
| `qla_core/rate_dbf_schema.py` | Confirmed QuikGcoi/QuikPlGcoi in FAMILY, PREFIX, KEY_TABLE (QX CHAR(10)) |
| `qla_core/rate_factor_loader.py` | `quikgcoi_keys_by_plan()` |
| `qla_core/rate_pipeline.py` | U5 stream; `paagerat_gcoi_*` tracking; summary block |
| `qla_core/rate_validation.py` | U5 in TYPE_FAMILY; ISWL_GCOI_MPLANS |
| `qla_core/paagerat_pr_loader.py` | Union GCOI plans into VARGP=3 set when phase4 enabled |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | `iswl_phase4` block |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.example.json` | Synced `iswl_phase4` |
| `tools/validators/iswl_common.py` | Phase 4 paths, ISWL_GCOI_MPLANS, GCOI_BASELINE_PATH |

**Not modified:** Phase 1 QUIKCVS; Phase 2 QUIKGPS; Phase 3 U6 loader behavior (thin wrapper preserved).

---

## New files

| File | Purpose |
|------|---------|
| `tools/validators/iswl_quikgcoi_reconcile.py` | V-GCOI-01–04 + Phase 1–3 regression |
| `Issue_Log_Items/Issue_31/iswl_quikgcoi_regression_baseline.json` | QuikGcoi baseline |
| `Issue_Log_Items/Issue_31/Phase4_QUIKGCOI/*` | Validation artifacts |

---

## Validation results

| ID | Check | Result |
|----|-------|--------|
| V-GCOI-01 | U5 vs U6 separation; NC/U6 excluded from GCOI stream | **PASS** |
| V-GCOI-02 | 200 U5 rows; segment `659 CEN II` → MPLAN `1679CS` only | **PASS** |
| V-GCOI-03 | Schema CNTL=00; PSEGT U5 8/8 | **PASS** |
| V-GCOI-04 | VALUE_INFO authoritative; QX1–QX9 blank | **PASS** (200/200 source) |
| SEQ=100 cap | 2 age caps, 2 cap collisions (expected) | **PASS** |
| Phase 1 QUIKCVS | **PASS** |
| Phase 2 QUIKGPS | **PASS** |
| Phase 3 QUIKCOI | **PASS** (792 rows unchanged) |

Pipeline: `blocker_count=0`, `emit_ready=true`

---

## Row counts

| MPLAN | PAAGERAT U5 source | QuikGcoi factor rows |
|-------|-------------------:|---------------------:|
| 1679CS | 200 | 198 |
| **Total** | **200** | **198** |

198 = 200 − 2 SEQ=100→AGE=99 cap collisions (2 gender tuples × SEQ=100).

Non-ISWL U5 rows (`668 SPWL` → `1668SP`, 217 rows) excluded by MPLAN allowlist.

---

## Run commands

```text
python tools/validators/iswl_quikgcoi_reconcile.py
python tools/validators/iswl_quikcoi_reconcile.py --write-baseline
python tools/validators/iswl_quikcoi_reconcile.py   # Phase 3 regression
python tools/validators/iswl_quikgps_reconcile.py    # Phase 2 regression
python tools/validators/iswl_quikcvs_reconcile.py   # Phase 1 regression
```

---

## Known issues

None blocking emit.

---

## Deferred items

| Item | Notes |
|------|-------|
| QUIKUINT | Phase 5 — not in scope |
| QUIKISSC | Phase 6 — not in scope |
| Expense tables | Out of scope |
| 7 MPLAN PSEGT-only U5 gap | PSEGT declares U5 on 8/8 coverages; PAAGERAT U5 only on `1679CS` — SME/client confirmation per validation strategy |

---

## PR-4 review recommendation

**Ready for review.** All V-GCOI checks pass; Phase 1–3 regression unchanged; output row count within expected 198–200 range.
