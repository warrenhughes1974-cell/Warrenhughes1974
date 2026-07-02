# Issue #31 — Phase 3 QUIKCOI Implementation Notes

**Date:** 2026-06-30  
**PR:** PR-3 Phase 3 — QUIKCOI  
**Prerequisite:** PR-2 Phase 2 QUIKGPS approved

---

## Summary

Phase 3 adds ISWL current COI rates via **PAAGERAT TYPE=U6 → QuikCoi** (VARGP=3 attained-age scalar). One source row → one QuikCoi row with rate in **QX0** only.

**Transform:**

```text
PAAGERAT (TYPE=U6) → SegmentResolver → QuikCoi
  SEQ → AGE, CNTL=00, VALUE_INFO → QX0, QX1–QX9 blank
```

---

## Files modified

| File | Change |
|------|--------|
| `qla_core/rate_dbf_schema.py` | QuikCoi/QuikPlCoi; QX prefix CHAR(10) |
| `qla_core/rate_factor_loader.py` | `factor_field_len(table)`; `quikcoi_keys_by_plan()` |
| `qla_core/rate_pipeline.py` | U6 stream; `paagerat_coi_*` tracking; summary includes CURRENT_COI |
| `qla_core/rate_validation.py` | U6 in TYPE_FAMILY; ISWL_COI_MPLANS |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | `iswl_phase3` block |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.example.json` | Synced `iswl_phase3` |
| `tools/validators/iswl_common.py` | Phase 3 paths and constants |

**Not modified:** Phase 1 QUIKCVS path; Phase 2 BP loader logic (only shared vargp3 union in pr_loader).

---

## New files

| File | Purpose |
|------|---------|
| `qla_core/paagerat_ul_coi_loader.py` | PAAGERAT U6 → QuikCoi |
| `tools/validators/iswl_quikcoi_reconcile.py` | V-COI-01–07 + regression |
| `Issue_Log_Items/Issue_31/iswl_quikcoi_regression_baseline.json` | QuikCoi baseline |
| `Issue_Log_Items/Issue_31/Phase3_QUIKCOI/*` | Validation artifacts |

---

## Validation results

| ID | Check | Result |
|----|-------|--------|
| V-COI-01 | PSEGT U6 8/8 + segment resolution | **PASS** |
| V-COI-02 | NC/U5 excluded from COI stream | **PASS** |
| V-COI-03 | U6 segments `658 CEN I`, `659 CEN II` only | **PASS** |
| V-COI-04 | Schema CNTL=00 | **PASS** |
| V-COI-05 | VALUE_INFO authoritative | **PASS** (800/800) |
| V-COI-06 | QX1–QX9 blank | **PASS** |
| V-COI-07 | SEQ=100 cap handling | **PASS** (8 caps, 8 collisions) |
| Phase 1/2 regression | **PASS** |

Pipeline: `blocker_count=0`, `emit_ready=true`

---

## Row counts

| MPLAN | PAAGERAT U6 source | QuikCoi factor rows |
|-------|-------------------:|-------------------:|
| 1658CS | 400 | 396 |
| 1679CS | 400 | 396 |
| **Total** | **800** | **792** |

792 = 800 − 8 SEQ=100→AGE=99 cap collisions (expected per validation strategy).

---

## Run commands

```text
python tools/validators/iswl_quikcoi_reconcile.py
python tools/validators/iswl_quikcvs_reconcile.py
python tools/validators/iswl_quikgps_reconcile.py
```

---

## Known issues

None blocking Phase 3.

- **6/8 ISWL MPLANs** have PSEGT U6 capability but zero PAAGERAT U6 rows — documented partial fleet (by design).
- 8 rows lost to SEQ=100 AGE cap — audited, non-blocking.

---

## Deferred

| Item | Reason |
|------|--------|
| Phase 4 QUIKGCOI (U5) | Out of scope |
| QuikGcoi schema/loader | Phase 4 |
| DBF emit / app.py | Out of scope |

---

## Recommended next step

Phase 4 — QUIKGCOI after PR-3 review approval.
