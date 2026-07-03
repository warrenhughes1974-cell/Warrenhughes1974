# Issue #37 — Status Record

**Issue:** Age/Duration Rate Placement — CV / QuikCvs (fleet-wide)  
**Last updated:** 2026-07-03  
**Package:** `Issue_Log_Items/Issue_37/`

---

## Current Status

| Stage | Status |
|-------|--------|
| **Intake (G0)** | **Complete** |
| **Planning (G1)** | **Complete** |
| **Dependency Gate (G2)** | **Complete** — client LifePRO screenshots authoritative |
| **Phase 2 proof matrix** | **Complete** (analysis only) |
| **Risk (G3)** | **Conditional Go — APPROVED** (2026-07-03) |
| **Development (G4)** | **Complete** (2026-07-03) |
| **Validation (G5)** | **PASS** (2026-07-03) |
| **Regression (G6)** | **PASS** (2026-07-03) |
| **Closure (G7)** | **Closed** (2026-07-03) · **v57.43** production-ready |

**Framework status:** **Closed**

---

## G6 Regression Record

| Item | Value |
|------|-------|
| Completed | 2026-07-03 |
| Verdict | **PASS** |
| Report | `Issue_37_Regression_Report.md` |
| Issue #31 baseline | Rebaselined (`iswl_quikcvs_reconcile.py --write-baseline`) |
| Issue #25 / #26 | **PASS** (MPOLICY width + MPREM validators) |

---

## Next Action

None — issue **closed**. Network batch: run suite at **v57.43**; **GENERATE RATE TABLES** refreshes `QuikCvs.csv`.

---

## G7 Closure Record

| Item | Value |
|------|-------|
| Closed | 2026-07-03 |
| Engine | **v57.43** (`QLA_Migration/app.py`) |
| Production | QuikCvs emit + validators PASS |
| Summary | `Issue_37_Resolution_Summary.md` |

---

## G5 Validation Record

| Item | Value |
|------|-------|
| Completed | 2026-07-03 |
| Verdict | **PASS** |
| Proof ages | 8/8 PASS (960 PO / 1960PO) |
| Report | `Issue_37_Validation_Report.md` |
| Evidence | `evidence/g5_validation_matrix.csv` |

---

## G4 Development Record

| Item | Value |
|------|-------|
| Completed | 2026-07-03 |
| Scope | `qla_core/rate_factor_loader.py` + `rate_pipeline.py` (CV grid only) |
| Validation script | `QLA_Migration/_validate_issue37_quikcvs_placement.py` |
| Emit | `QuikCvs.csv` re-generated via `rate_loader_emit.py --csv-only` |

---

## G3 Approval Record

| Item | Decision |
|------|----------|
| **Verdict** | **Conditional Go** |
| **Approved by** | Project lead (2026-07-03) |
| **Scope** | Fleet-wide **QuikCvs / CV** duration placement in Phase R5 rate pipeline |
| **Maturity rule** | **`last_duration = 100 − issue_age`** for all CV products (103 not used as fleet rule) |
| **Values** | Unchanged — placement / zero-padding only |
| **Untouched** | `app.py`, QuikPlan, NP/GP/DB/DV/TV rate tables, Issues #25 / #26 |

---

## Conditions Carried Into Development

1. **Variable start offset** by issue age (not constant +3) — per 960 PO proof matrix.
2. **960 PO proof ages** must pass before fleet emit: M **0, 18, 20, 22, 24, 29, 33** and F **0**.
3. **Truncate policy** — **9,616** CV source rows dropped past maturity (`100 − issue_age`).
4. **12 PCOVR products** with `MAX_BENEFIT_AGE ≠ 100` — G3 override to maturity **100** accepted unless SME reverses.

**Reference:** `Issue_37_Validation_Report.md`, `Issue_37_Implementation_Notes.md`, `Issue_37_Risk_Review_Report.md`
