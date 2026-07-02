# Issue #32 — Phase 5 QUIKUINT Implementation Notes

**Date:** 2026-06-28  
**PR:** PR-5 Phase 5 — QUIKUINT  
**Prerequisite:** Issue #31 PR-1–PR-4 (QUIKCVS, QUIKGPS, QUIKCOI, QUIKGCOI) closed

---

## Summary

Phase 5 adds ISWL declared interest rates via **PDINT/PDINTTBL (CENII, TYPE=A1) → QuikUint** plan-level rows. Historical tiers use **union_merge** across DINT_RULE 0 and 3 with tie-break preferring Rule 3 at duplicate START_DATE.

**Transform:**

```text
PDINT / PDINTTBL
  IDENT = CENII
  TYPE_CODE = A1
  DINT_RULE in {0, 3}
    ↓ union_merge by START_DATE (tie-break: Rule 3)
  QuikUint (MPLAN × MEFFDATE)
    MCURRATE = PDINTTBL.DECLARED_RATE
    MGTDRATE = MCURRATE (mirror)
```

Loan interest is **not** emitted to QuikUint (deferred to QuikPlan/QuikPlSt track).

---

## 1. Files modified

| File | Change |
|------|--------|
| `qla_core/rate_dbf_schema.py` | Added `QuikUint` to member table fields; `quikuint_fields()` |
| `qla_core/rate_dbf_writer.py` | `write_quikuint_table()`, `write_quikuint_csv()` |
| `qla_core/rate_pipeline.py` | Wired `quikuint_loader`; `quikuint_rows`, `quikuint_status`, `quikuint_enabled` on `PipelineResult`; summary block |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | `iswl_phase5` block; PDINT/PDINTTBL extract paths |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.example.json` | Synced `iswl_phase5` |
| `plan_analysis/phase_r5_rate_loader/rate_loader_emit.py` | Prefer `rate_loader_config.json`; emit QuikUint DBF/CSV |
| `tools/validators/iswl_common.py` | Phase 5 paths, `ISWL_UINT_MPLANS`, `EXPECTED_UINT_ROWS=32` |

**Not modified:** Phase 1–4 loader behavior (QUIKCVS, QUIKGPS, QUIKCOI, QUIKGCOI); Issue #31 rate-table loaders beyond shared config/pipeline wiring.

---

## 2. New files created

| File | Purpose |
|------|---------|
| `qla_core/quikuint_loader.py` | PDINTTBL load, union_merge tiers, build QuikUint rows |
| `tools/validators/iswl_quikuint_reconcile.py` | V-UINT-01 through V-UINT-10 |
| `QLA_Migration/Output/rates/QuikUint.csv` | Phase 5 emit output (32 rows) |
| `Issue_Log_Items/Issue_32/output/Phase5_QUIKUINT/iswl_quikuint_reconcile_summary.json` | Validator summary |
| `Issue_Log_Items/Issue_32/output/Phase5_QUIKUINT/iswl_quikuint_rates_by_mplan.csv` | Per-MPLAN tier breakdown |
| `Issue_Log_Items/Issue_32/output/baselines/iswl_quikuint_regression_baseline.json` | UINT regression baseline |

---

## 3. Implementation summary

### Source

- **PDINTTBL extract:** `QLA_Migration/Source/PDINTTBL_Extract_20260629.csv`
- **Filter:** IDENT=`CENII`, TYPE_CODE=`A1`, DINT_RULE in `{0, 3}`
- **6 raw source tiers** (3 per rule) before union merge

### Union merge schedule (per MPLAN)

| MEFFDATE (START_DATE) | MCURRATE / MGTDRATE | Winning DINT_RULE |
|----------------------:|--------------------:|:-----------------:|
| 19800101 | 11.0000 | 3 (tie-break over Rule 0 @ 7.0000) |
| 19890101 | 9.0000 | 3 |
| 19990101 | 5.0000 | 0 (Rule 3 has no row) |
| 20020101 | 4.5000 | 3 (same rate as Rule 0) |

### Output mapping

| QuikUint field | Source |
|----------------|--------|
| MPLAN | Each of 8 ISWL MPLANs from allowlist |
| MEFFDATE | PDINTTBL.START_DATE |
| MCURRATE | PDINTTBL.DECLARED_RATE (N(8.4) percent literal) |
| MGTDRATE | Same value as MCURRATE |

### Config (`iswl_phase5`)

```json
{
  "quikuint_enabled": true,
  "pdint_ident": "CENII",
  "type_code": "A1",
  "dint_rules": ["0", "3"],
  "emit_mode": "union_merge",
  "dint_rule_tiebreak": "3",
  "g1_mode": "mirror_a1",
  "mplan_allowlist": ["1658C1","1658CS","1659C2","1659CR","1659CS","1659SR","1669SR","1679CS"]
}
```

### Fallback

If PDINTTBL historical tiers are unavailable, loader emits **current tier only** (20020101 @ 4.5000) for all 8 MPLANs.

---

## 4. Validation results

| ID | Check | Result |
|----|-------|--------|
| V-UINT-01 | Schema: MPLAN, MEFFDATE, MGTDRATE, MCURRATE | **PASS** |
| V-UINT-02 | CENII / A1 source rows used | **PASS** (6 source tiers) |
| V-UINT-03 | union_merge dates 19800101, 19890101, 19990101, 20020101 | **PASS** |
| V-UINT-04 | Row count = 32 | **PASS** |
| V-UINT-05 | 8/8 ISWL MPLANs emitted | **PASS** |
| V-UINT-06 | MGTDRATE = MCURRATE on every row | **PASS** |
| V-UINT-07 | Percent literals (11.0000 not 0.1100) | **PASS** |
| V-UINT-08 | No loan interest on QuikUint | **PASS** |
| V-UINT-09 | Unique index (MPLAN + MEFFDATE) | **PASS** (0 dupes) |
| V-UINT-10 | Phase 1–4 outputs unchanged | **PASS** |

PSEGT gates: A1 8/8, G1 8/8, LN 8/8 — all **PASS**.

Pipeline: `blocker_count=0`, `emit_ready=true`

---

## 5. Row counts

| MPLAN | Tiers | Notes |
|-------|------:|-------|
| 1658C1 | 4 | Shared CENII/A1 schedule |
| 1658CS | 4 | Shared CENII/A1 schedule |
| 1659C2 | 4 | Shared CENII/A1 schedule |
| 1659CR | 4 | Shared CENII/A1 schedule |
| 1659CS | 4 | Shared CENII/A1 schedule |
| 1659SR | 4 | Shared CENII/A1 schedule |
| 1669SR | 4 | Shared CENII/A1 schedule |
| 1679CS | 4 | Shared CENII/A1 schedule |
| **Total** | **32** | 8 MPLANs × 4 effective dates |

**Output file:** `QLA_Migration/Output/rates/QuikUint.csv`

---

## 6. Regression results

| Validator | Result |
|-----------|--------|
| `iswl_quikcvs_reconcile.py` (Phase 1) | **PASS** — blockers=0, V-X-01 regression PASS |
| `iswl_quikgps_reconcile.py` (Phase 2) | **PASS** — blockers=0, non-ISWL regression PASS |
| `iswl_quikcoi_reconcile.py` (Phase 3) | **PASS** — 792 QuikCoi rows unchanged |
| `iswl_quikgcoi_reconcile.py` (Phase 4) | **PASS** — 198 QuikGcoi rows unchanged |
| `iswl_quikuint_reconcile.py` (Phase 5) | **PASS** — all V-UINT checks |

---

## 7. Known issues

None blocking emit.

---

## 8. Deferred items

| Item | Notes |
|------|-------|
| Loan interest on QuikUint | Explicitly excluded — separate QuikPlan/QuikPlSt track (Issue #32 loan scope) |
| QUIKISSC | Phase 6 — not started |
| Expense setup | Out of scope |
| Per-MPLAN PDINT IDENT variation | SME confirmed CENII for all 8 MPLANs; no per-plan override implemented |
| G1 declared rate stream | PSEGT G1 gate validated (8/8); G1 rows not emitted to QuikUint (A1-only emit) |

---

## 9. PR-5 review recommendation

**Ready for review.**

All V-UINT checks pass. Phase 1–4 regression unchanged. Output matches expected 32-row union_merge schedule with correct percent literals and MGTDRATE mirror behavior.

---

## Run commands

```text
python tools/validators/iswl_quikuint_reconcile.py --write-baseline --emit-csv
python tools/validators/iswl_quikcvs_reconcile.py
python tools/validators/iswl_quikgps_reconcile.py
python tools/validators/iswl_quikcoi_reconcile.py
python tools/validators/iswl_quikgcoi_reconcile.py
python tools/validators/iswl_quikuint_reconcile.py
```
