# Issue #31 — Phase 2 QUIKGPS Implementation Notes

**Date:** 2026-06-30  
**PR:** PR-2 Phase 2 — QUIKGPS  
**Authority:** `docs/research/ISWL_Implementation/`  
**Prerequisite:** PR-1 Phase 1 QUIKCVS approved

---

## Summary

Phase 2 adds ISWL billable premium rates via **PAAGERAT TYPE=BP → QuikGps** using the existing attained-age scalar pattern (VARGP=3). PR stream remains for non-ISWL plans; PR is **suppressed** on the four ISWL BP MPLANs so BP is billable-premium authority.

**Transform:**

```text
PAAGERAT (TYPE=BP) → SegmentResolver → QuikGps
  SEQ → AGE, CNTL=00, VALUE_INFO → GP0, GP1–GP9 blank
  VARGP=3
```

---

## Files modified

| File | Change |
|------|--------|
| `qla_core/paagerat_pr_loader.py` | Extracted `transform_paagerat_attained_age()`; PR suppress on ISWL BP MPLANs when Phase 2 enabled |
| `qla_core/rate_pipeline.py` | Wire BP stream; track `paagerat_bp_status`; union BP plans into VARGP=3 set |
| `qla_core/rate_validation.py` | Added `BP` to `TYPE_FAMILY`; `ISWL_BP_MPLANS` constant |
| `qla_core/rate_factor_loader.py` | Added `quikgps_keys_by_plan()` helper |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | Added `iswl_phase2` block |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.example.json` | Synced `iswl_phase2` |
| `tools/validators/iswl_common.py` | Phase 2 paths, `ISWL_BP_MPLANS`, `GPS_BASELINE_PATH` |

**Not modified:**

- Phase 1 QUIKCVS path / PDAGE routing
- `rate_dbf_schema.py` (BP uses existing QuikGps table via PAAGERAT path)
- `QLA_Migration/app.py`
- Phase 3/4 (QUIKCOI / QUIKGCOI)

---

## New files

| File | Purpose |
|------|---------|
| `qla_core/paagerat_bp_loader.py` | PAAGERAT TYPE=BP loader for ISWL QUIKGPS |
| `tools/validators/iswl_quikgps_reconcile.py` | V-GPS-01–04 + regression |
| `Issue_Log_Items/Issue_31/iswl_quikgps_regression_baseline.json` | Non-ISWL QuikGps regression baseline |
| `Issue_Log_Items/Issue_31/Phase2_QUIKGPS/*` | Validation artifacts |

---

## Validation results

| ID | Check | Result |
|----|-------|--------|
| V-GPS-01 | 100% BP segment resolution (ISWL) | **PASS** (1,164/1,164; 0 unresolved) |
| V-GPS-02 | BP scope ISWL only; 1,164 IN_SCOPE | **PASS** |
| V-GPS-03 | Hub `659 CEN II` → `1679CS` via `679 CEN SD` | **PASS** (330 hub rows) |
| V-GPS-04 | VALUE_INFO > 0 for all BP rows | **PASS** |
| Phase 1 regression | QUIKCVS unchanged | **PASS** |
| Non-ISWL QuikGps regression | **PASS** |

Pipeline: `blocker_count=0`, `emit_ready=true`, V03=0

---

## Row counts

**PAAGERAT BP source (ISWL):**

| MPLAN | Source BP rows | QuikGps distinct keys |
|-------|---------------:|----------------------:|
| 1658CS | 444 | 294 |
| 1659CS | 152 | 152 |
| 1669SR | 172 | 172 |
| 1679CS | 396 | 330 |
| **Total** | **1,164** | **948** |

Grid keys ≤ source rows (dedupe via segment-tier / duplicate-key rules). Global QuikGps plans: 86 (VARGP=3 set: 77).

---

## Run commands

```text
python tools/validators/iswl_quikgps_reconcile.py
python tools/validators/iswl_quikcvs_reconcile.py
python tools/validators/iswl_psegt_cv_gate.py
```

---

## Known issues

None blocking Phase 2.

- 948 grid keys from 1,164 source rows — expected dedupe (segment-tier precedence, shared segmentation tuples).
- 172 non-ISWL BP source rows excluded by MPLAN allowlist (by design).

---

## Deferred

| Item | Reason |
|------|--------|
| Phase 3 QUIKCOI (U6) | Out of Phase 2 scope |
| Phase 4 QUIKGCOI (U5) | Out of Phase 2 scope |
| DBF emit | Dry-run + validators only |
| `app.py` integration | Out of scope |

---

## Recommended next step

Phase 3 — QUIKCOI per `ISWL_Development_Order.md` after PR-2 review approval.
