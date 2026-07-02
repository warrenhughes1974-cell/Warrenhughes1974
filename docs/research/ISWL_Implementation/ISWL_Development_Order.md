# ISWL Development Order

**Project:** LifePRO → QLAdmin  
**Version baseline:** v57.39  
**Date:** 2026-06-30 (updated — QUIKCOI/QUIKGCOI transform finalized)  
**Mode:** Planning only

---

## Recommended build sequence

```text
Phase 0 — Prerequisites (no code)
  ├── Run PDAGE vs Rate_Table CV parity study
  └── SME/client sign-off on partial MPLAN emit (6/8 U6, 7/8 U5 gaps)

Phase 1 — QUIKCVS  ★ Current Development Agent target
  ├── ISWL allowlist gate in rate dry-run
  ├── CSO crosswalk QuikPlCv assumptions verified
  ├── PDAGE parity report (blocker for source switch only)
  └── Dry-run emit for 8 MPLANs via existing Rate_Table path

Phase 2 — QUIKGPS
  ├── Generalize paagerat_pr_loader → attained-age segment loader
  ├── Add TYPE_CODE=BP filter + QuikGps emit
  ├── Register ISWL MPLANs in VARGP=3 plan set
  └── Reconcile 1,164 BP rows / 4 MPLANs

Phase 3 — QUIKCOI  ★ Spec complete — ready after Phase 2
  ├── Add QuikCoi to rate_dbf_schema (Help §7.73: QX0–QX9 C10)
  ├── paagerat_ul_coi_loader: U6, attained-age scalar emit
  ├── Transform: SEQ→AGE, CNTL=00, VALUE_INFO→QX0, QX1–QX9 blank
  ├── PSEGT U6 hierarchy gate
  ├── Emit 1658CS + 1679CS (~792–800 rows from 800 source)
  └── Document 6 MPLAN PSEGT-only gap

Phase 4 — QUIKGCOI  ★ Spec complete — ready after Phase 3
  ├── Add QuikGcoi to rate_dbf_schema (Help §7.93)
  ├── Reuse loader core: TYPE_CODE=U5 → QuikGcoi
  ├── Emit 1679CS only (~198–200 rows from 200 source)
  └── Document 7 MPLAN PSEGT-only gap
```

---

## Rationale by phase

### Phase 0 — Prerequisites

| Item | Why first |
|------|-----------|
| CV parity | Wrong CV source corrupts 2,268 policies |
| Partial emit policy | 6/8 MPLANs lack PAAGERAT U6; 7/8 lack U5 — avoid silent omission |

**Removed prerequisite:** QuikCoi/QuikGcoi DBF schema — **confirmed** via QLAdmin Help §7.73 / §7.93.

### Phase 1 — QUIKCVS first

Unchanged — existing Rate_Table infrastructure, lowest regression risk.

### Phase 2 — QUIKGPS second

Validates PAAGERAT attained-age segment path (`SEQ`→`AGE`, scalar single-column) before UL COI tables.

### Phase 3 — QUIKCOI third

| Factor | Assessment |
|--------|------------|
| Schema | **Confirmed** — no longer blocked |
| Transform | **Final** — attained-age scalar; one row → QX0 |
| Rate completeness | Partial — 2/8 MPLANs (800 source → ~792–800 output) |
| Shared work | Attained-age loader core from Phase 2 |

### Phase 4 — QUIKGCOI last

| Factor | Assessment |
|--------|------------|
| Effort | Minimal incremental — same loader, `U5` filter |
| Rate completeness | Most sparse — 1/8 MPLAN (200 source → ~198–200 output) |
| Risk | Implement after U6 proven to avoid U5/U6 swap errors |

---

## Complexity summary

| Table | Complexity | Phase | Source rows | Output rows (v1) | MPLAN coverage |
|-------|------------|-------|-------------|------------------|----------------|
| QUIKCVS | Medium | 1 | ~72,271 CV | TBD pivot | 8/8 (expected) |
| QUIKGPS | Medium | 2 | 1,164 BP | ≤1,164 | 4/8 |
| QUIKCOI | Medium | 3 | 800 U6 | ~792–800 | 2/8 |
| QUIKGCOI | Medium | 4 | 200 U5 | ~198–200 | 1/8 |

---

## Files modified by phase (cumulative)

### Phase 3 — QUIKCOI

| File | Change type |
|------|-------------|
| `qla_core/rate_dbf_schema.py` | QuikCoi layout (`QX` prefix, CHAR(10)) |
| `qla_core/paagerat_ul_coi_loader.py` | **New** — U6 filter, VALUE_INFO, scalar emit |
| `qla_core/rate_pipeline.py` | Wire U6 stream + PSEGT gate |
| `tools/validators/iswl_quikcoi_reconcile.py` | **New** |

### Phase 4 — QUIKGCOI

| File | Change type |
|------|-------------|
| `qla_core/rate_dbf_schema.py` | QuikGcoi layout |
| `qla_core/paagerat_ul_coi_loader.py` | Extend for U5 |
| `qla_core/rate_pipeline.py` | Wire U5 stream |
| `tools/validators/iswl_quikgcoi_reconcile.py` | **New** |

---

## Parallelism constraints

| Can parallelize | Cannot parallelize |
|-----------------|-------------------|
| Phase 0 SME tasks | Phase 4 before Phase 3 loader core |
| CV parity script | COI/GCOI before QUIKGPS attained-age path proven |
| Documentation | Multiple pipeline refactors in one PR (avoid) |

**PR strategy:** One table per PR; each PR includes dry-run artifacts and validation CSV.

---

## Remaining risks (COI/GCOI)

| Risk | Notes |
|------|-------|
| SEQ=100 vs AGE C(2) | Cap at 99; SEQ 99 wins collision; ~10 row loss across U5+U6 |
| 6/8 MPLANs PSEGT U6, no PAAGERAT | Partial fleet; SME/client confirmation |
| 7/8 MPLANs PSEGT U5, no PAAGERAT | Partial fleet; SME/client confirmation |
| QX1–QX9 blank | Intentional for attained-age data; not a defect |
| Help "Issue age" label vs VARGP=3 | AGE stores attained age for ISWL COI/GCOI |

---

## Rollback safety

Each phase must:

1. Preserve existing non-ISWL rate emit (diff dry-run plan sets).
2. Use ISWL MPLAN allowlist from `cso_mortality_crosswalk.py`.
3. Not alter field order/types in existing QuikCvs/QuikGps for non-ISWL plans.
4. Pass `rate_pipeline` blocker count = 0 before DBF emit.

---

## Development Agent readiness

| Phase | Target | Prompt status |
|-------|--------|---------------|
| 1 | QUIKCVS | **Ready** — see [`ISWL_Next_Stage_Prompt.md`](ISWL_Next_Stage_Prompt.md) |
| 2 | QUIKGPS | Ready after Phase 1 (pattern documented in Table Design §2) |
| 3 | QUIKCOI | **Ready for coding** — transform finalized; see Table Design §3, Validation § QUIKCOI |
| 4 | QUIKGCOI | **Ready for coding** after Phase 3 — see Table Design §4 |

**First approved target:** QUIKCVS (Phase 1).
