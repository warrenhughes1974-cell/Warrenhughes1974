# Issue #31 — ISWL Rate Table Implementation Completion Report

**Date:** 2026-06-30  
**Status:** **CLOSED — Implementation Complete**  
**Resolution:** Original source dependency resolved. ISWL rate-table implementation (PR-1 through PR-4) completed, validated, CSV test package emitted. Ready for UAT.

---

## Executive Summary

Issue #31 began as a **source dependency blocker** (PSEGT, PDINT, PDINTTBL extracts) for ISWL segment hierarchy research. Client extracts were delivered and validated (2026-06-29). The follow-on **ISWL Rate Table implementation** delivered four QLAdmin rate factor tables across four approved PRs:

| PR | Table | Source | Status |
|----|-------|--------|--------|
| PR-1 | QUIKCVS | Rate_Table CV | ✓ Complete |
| PR-2 | QUIKGPS | PAAGERAT BP | ✓ Complete |
| PR-3 | QUIKCOI | PAAGERAT U6 | ✓ Complete |
| PR-4 | QUIKGCOI | PAAGERAT U5 | ✓ Complete |

All phase validators pass. Regression is clean. CSV test package emitted to `QLA_Migration/Output/rates/`. **Recommendation: READY FOR UAT.**

Final validation verdict: **APPROVE WITH NOTES** (PDAGE parity partial; partial MPLAN PAAGERAT coverage documented).

---

## Scope Completed

### In scope (delivered)

- ISWL QUIKCVS validation on existing Rate_Table → QuikCvs path (8/8 MPLANs)
- ISWL QUIKGPS via PAAGERAT TYPE=BP → QuikGps (VARGP=3 attained-age scalar)
- ISWL QUIKCOI via PAAGERAT TYPE=U6 → QuikCoi (attained-age scalar, VALUE_INFO → QX0)
- ISWL QUIKGCOI via PAAGERAT TYPE=U5 → QuikGcoi (shared UL loader core)
- Phase validators V-CVS through V-GCOI
- Regression baselines and CSV test emit

### Out of scope (not delivered — separate epics)

- QUIKUINT (interest rates)
- QUIKISSC (surrender charges)
- Expense table setup (UF/U1–U3/G2/G3/GF)
- PDAGE source switch (blocked pending SME; Rate_Table remains authoritative)
- DBF production emit / `app.py` integration
- Full-fleet PAAGERAT U5/U6 for all 8 ISWL MPLANs (documented gaps)

---

## Development Phases Completed

### PR-1 — QUIKCVS

- **Path:** Rate_Table TYPE=CV → QuikCvs / QuikPlCv (VARGP=2)
- **MPLANs:** 8/8 ISWL fleet
- **Key outcome:** No new CV loader required; validation gates added

### PR-2 — QUIKGPS

- **Path:** PAAGERAT TYPE=BP → QuikGps (SEQ→AGE, VALUE_INFO→GP0, VARGP=3)
- **Source:** 1,164 BP IN_SCOPE rows
- **Output:** 948 QuikGps keys across 4 MPLANs

### PR-3 — QUIKCOI

- **Path:** PAAGERAT TYPE=U6 → QuikCoi (SEQ→AGE, CNTL=00, VALUE_INFO→QX0)
- **Source:** 800 U6 IN_SCOPE rows
- **Output:** 792 QuikCoi factor rows (1658CS, 1679CS)

### PR-4 — QUIKGCOI

- **Path:** PAAGERAT TYPE=U5 → QuikGcoi (shared attained-age scalar loader)
- **Source:** 200 U5 IN_SCOPE rows
- **Output:** 198 QuikGcoi factor rows (1679CS only)

---

## Validation Summary

| Validator | Phase | Result |
|-----------|-------|--------|
| `iswl_psegt_cv_gate.py` | 1 | PASS — PSEGT CV 8/8 |
| `iswl_quikcvs_reconcile.py` | 1 | PASS |
| `iswl_quikcvs_parity.py` | 1 | PASS (exit 0) — V-CVS-05 **PARTIAL / NEEDS REVIEW** (10.44%) |
| `iswl_quikgps_reconcile.py` | 2 | PASS |
| `iswl_quikcoi_reconcile.py` | 3 | PASS |
| `iswl_quikgcoi_reconcile.py` | 4 | PASS |

**Pipeline gate:** `blocker_count=0`, `emit_ready=true` (all phases)

---

## Regression Summary

| Check | Result |
|-------|--------|
| Phase 1 unchanged after Phases 2–4 | PASS |
| Phase 2 unchanged after Phases 3–4 | PASS |
| Phase 3 unchanged after Phase 4 | PASS |
| Non-ISWL fleet regression | PASS |
| V03 duplicate-cell collisions | 0 |

Regression baselines: `Issue_Log_Items/Issue_31/output/baselines/`

---

## CSV Emit Summary

**Command:**

```text
python plan_analysis/phase_r5_rate_loader/rate_loader_emit.py --csv-only
```

**Location:** `QLA_Migration/Output/rates/`  
**Gate:** `blocker_count=0` — emit succeeded  
**Verdict:** **READY FOR TESTING**

Required factor CSVs confirmed present. Emit used current pipeline implementation (not `QLA_Migration/Archive/rates/`).

Detail: `Issue_Log_Items/Issue_31/output/Issue_31_ISWL_Rate_Table_CSV_Emit_Report.md`

---

## Final Row Counts

### ISWL factor rows (from emitted CSVs)

| Table | CSV | Total rows | ISWL rows | ISWL MPLANs |
|-------|-----|----------:|----------:|-------------|
| QUIKCVS | QuikCvs.csv | 25,717 | 7,789 | 8/8 |
| QUIKGPS | QuikGps.csv | 12,567 | 948 | 4/8 |
| QUIKCOI | QuikCoi.csv | 792 | 792 | 2/8 |
| QUIKGCOI | QuikGcoi.csv | 198 | 198 | 1/8 |

### ISWL rows by MPLAN

**QuikCvs:** 1658C1 (1947), 1658CS (979), 1659C2 (1045), 1659CR (1045), 1659CS (997), 1659SR (1047), 1669SR (264), 1679CS (465)

**QuikGps:** 1658CS (294), 1659CS (152), 1669SR (172), 1679CS (330)

**QuikCoi:** 1658CS (396), 1679CS (396)

**QuikGcoi:** 1679CS (198)

---

## Deliverables Produced

See **Deliverables Inventory** (`Issue_31_Deliverables_Inventory.md` in this folder) for the full file list.

### Summary by category

| Category | Location |
|----------|----------|
| Core loaders / pipeline | `qla_core/` (paagerat_bp_loader, paagerat_ul_coi_loader, rate_pipeline, etc.) |
| Config | `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` |
| Validators | `tools/validators/iswl_*.py` |
| Validation artifacts | `Issue_Log_Items/Issue_31/output/` |
| CSV test package | `QLA_Migration/Output/rates/` |
| Implementation docs | `Issue_Log_Items/Issue_31/Issue_31_Phase*_*.md` |
| Research / design authority | `docs/research/ISWL_Implementation/` |

---

## Remaining Out-of-Scope Items

| Item | Status | Notes |
|------|--------|-------|
| PDAGE CV source switch | Open — SME | V-CVS-05 10.44% shared-key match; Rate_Table authoritative |
| 6/8 MPLANs without U6 PAAGERAT | Documented | PSEGT U6 on 8/8; PAAGERAT on 2 MPLANs only |
| 7/8 MPLANs without U5 PAAGERAT | Documented | PSEGT U5 on 8/8; PAAGERAT on 1679CS only |
| QUIKUINT | Not started | Next logical ISWL epic |
| QUIKISSC | Not started | SR/SL rate pointer SME blocked |
| Expenses | Not started | UF/U1–U3 model undecided |
| DBF emit / app.py | Not started | CSV dry-run complete; production integration separate |

---

## Recommendation

**Issue #31 — CLOSED.**

The ISWL Rate Table implementation sequence (PR-1 through PR-4) is complete. CSV test package is ready for UAT at `QLA_Migration/Output/rates/`. Route follow-on work to new issues for QUIKUINT, QUIKISSC, expenses, PDAGE parity closure, and production DBF/`app.py` integration.

**UAT focus:** Validate QuikCvs, QuikGps, QuikCoi, QuikGcoi CSV content against QLAdmin load requirements for the 8 ISWL MPLAN fleet.
