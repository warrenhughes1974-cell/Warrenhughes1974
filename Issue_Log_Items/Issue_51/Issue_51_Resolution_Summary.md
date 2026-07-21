# Issue #51 — Resolution Summary

**Issue:** #51 — Missing Interest Table (A60MIR / A96DAR) — Projected Values Crash Loop  
**Framework stage:** Closure Agent (G7)  
**Final status:** **Ready for Client UAT**  
**Engine version:** **v57.76**  
**Closed date:** 2026-07-11  
**Owner:** Conversion (Warren) · **Reporter:** Client UAT (QLAdmin Projected Values)

---

## Resolution (issue log — paste-ready)

**Resolution:** Added QuikAint interest-rate stubs for closed riders A60MIR and A96DAR so QLAdmin Projected Values no longer fails looking up a missing interest table.

> Copy the line above into tracking sheets and client readouts. Long-form detail follows.

---

## Problem Statement

Opening **Projected Values** in QLAdmin for policies carrying rider plans **A60MIR** (Monthly Income Rider) or **A96DAR** (Deposit Annuity Rider) raised *"Interest table not found for A60MIR, cannot calculate balance"* (or A96DAR equivalent) and entered an **endless OK-loop** requiring Task Manager to quit. The error occurred even when the rider was **status 56 (terminated)**. Example policy: **010348734C** (LifePRO `9010348734`) — Ph2 A60MIR MPHSTAT=56.

---

## Root Cause

**Category:** [x] Scope gap  [x] QLAdmin behavior  [ ] Mapping error  [ ] Source extract defect  [ ] Client definition

A-prefix annuity plans **A60MIR** and **A96DAR** are governed by PLAN-023 / Data Governance to require **QuikAint** (Annuity Interest Rates, QLAdmin Help §7.31). The rate load package had **no `QuikAint.csv`** and no rows for these plans. QLAdmin Projected Values walks rider MPLANs and SEEKs `QuikAint` by plan + effective date; missing table → error dialog → endless loop. All six fleet MIR/DAR riders are status 56; PPBEN `FV_GUAR_RATE` authority is **.00** on forms 863/896.

---

## Resolution (detail)

Emitted exactly **2** QuikAint stub rows at `MEFFDATE=19000101`, `MINTRATE/MINTRATE1=0.0000` per PPBEN authority. Wired into rate emit path (`qla_core/rate_emit.py`, rate loader mirror). No QuikUint expansion, no quikridr status changes, no #21D / #25 / #26 / #32 changes.

### Files changed

| File | Change |
|------|--------|
| `qla_core/rate_dbf_schema.py` | QuikAint fields + `quikaint_fields()` (Help §7.31) |
| `qla_core/rate_dbf_writer.py` | `write_quikaint_table()` / `write_quikaint_csv()` |
| `qla_core/quikaint_closed_riders.py` | **New** — stub builder + `emit_issue51_quikaint()` |
| `qla_core/rate_emit.py` | Hook QuikAint emit on CSV/DBF rate package write |
| `plan_analysis/phase_r5_rate_loader/rate_loader_emit.py` | Mirror QuikAint emit for CLI rate loader |
| `app.py` / `QLA_Migration/app.py` | **v57.76** |
| `tools/validators/validate_issue51_quikaint.py` | **New** — issue validator |
| `QLA_Migration/_validate_issue51_quikaint.py` | **New** — thin wrapper |
| `QLA_Migration/Output/rates/QuikAint.csv` | **Produced** — 2 stub rows |
| `QLA_Migration/Output/rates/rate_csv_manifest.csv` | Added QuikAint entry |
| `QLA_Migration/Output/Test_Validation/rates/QuikAint.csv` | Partial UAT publish |

### QuikAint.csv contents

```
MPLAN,MEFFDATE,MINTRATE,MINTRATE1
A60MIR,19000101,0.0000,0.0000
A96DAR,19000101,0.0000,0.0000
```

### Rulebook changes

None.

### Engine changes

Rate-package surgical emit only — new QuikAint table writer + closed-rider stub module.

---

## Evidence

| Artifact | Path |
|----------|------|
| Intake | `Issue_51_Intake_Summary.md` |
| Planning | `Issue_51_Planning_Report.md` |
| Dependency Gate | `Issue_51_Dependency_Gate.md` |
| Risk | `Issue_51_Risk_Review_Report.md` — Conditional Go |
| Implementation | `Issue_51_Implementation_Notes.md` |
| Validation | `Issue_51_Validation_Report.md` — **PASS** |
| Regression | `Issue_51_Regression_Report.md` — **PASS** |
| Validator | `tools/validators/validate_issue51_quikaint.py` — **PASS** |
| Evidence CSVs | `evidence/issue51_*.csv` |

---

## Trace Policy Confirmation

| Policy | Phase | Rider | Expected | Emitted | Match |
|--------|------:|-------|----------|---------|-------|
| **010348734C** | 2 | A60MIR | QuikAint @ 0.0000 | Present @ 0.0000 | **Yes** |
| **010335095C** | 2 | A60MIR | QuikAint @ 0.0000 | Present @ 0.0000 | **Yes** |
| **010510671C** | 4 | A96DAR | QuikAint @ 0.0000 | Present @ 0.0000 | **Yes** |
| **010511203C** | 2 | A96DAR | QuikAint @ 0.0000 | Present @ 0.0000 | **Yes** |
| **010538650C** | 2 | A96DAR | QuikAint @ 0.0000 | Present @ 0.0000 | **Yes** |
| **010549966C** | 2 | A96DAR | QuikAint @ 0.0000 | Present @ 0.0000 | **Yes** |

---

## Explicitly Not Changed

- [x] quikridr MIR/DAR rows (6 × MPHSTAT=56 — unchanged)
- [x] QuikUint — no A60MIR/A96DAR rows (#32 ISWL-only path preserved)
- [x] Issue #25 MPOLICY padding
- [x] Issue #26 quikridr.MPREM mapping
- [x] Issue #21D quikdvdp.MDEPINT
- [x] quikmstr / quikplan / quikprmh policy tables (0 row delta)
- [x] QuikGps / factor / key rate tables (other rates unchanged)

---

## Fleet Impact

| Metric | Value |
|--------|------:|
| QuikAint rows added | **2** |
| Policy table rows changed | **0** |
| QuikUint MIR/DAR pollution | **0** |
| quikridr MIR/DAR fleet | **6** (all status 56, unchanged) |

---

## Production Readiness + Git Release (G7)

| Check | Status |
|-------|--------|
| Validators PASS (G5 + G6) | **PASS** |
| `app.py` version bumped | **v57.76** (both copies) |
| Issue-scoped git commit | **Pending** — user has not requested commit this session |
| **`git push` to remote** | **Skipped** — pending user approval |
| Network batch note | `Output/` gitignored — after pull + commit, load `QuikAint.csv` (or DBF) with rate package; re-emit rates if needed via rate loader or GENERATE RATE TABLES |

---

## Client UAT

| Item | Status |
|------|--------|
| Load `QuikAint.csv` into QLAdmin rate package | **Pending** |
| Projected Values on **010348734C** (A60MIR) — no endless loop | **Pending** |
| Projected Values on A96DAR sample (e.g. **010510671C**) | **Pending** |
| Client sign-off | Pending |

**UAT steps:**

1. Pull engine **v57.76** (after commit/push when approved).
2. Ensure `QLA_Migration/Output/rates/QuikAint.csv` is in the rate load package (or use `Output/Test_Validation/rates/QuikAint.csv` for partial reload).
3. Load QuikAint with other rate tables into QLAdmin.
4. Open **Projected Values** on **010348734C** — expect no "Interest table not found" endless loop.
5. Retest an A96DAR policy sample.
6. If loop persists after QuikAint is confirmed loaded, escalate **QuikAing/QuikAinf** stubs at same 0% rate per Risk Conditional Go fallback E.

---

## Residual Risks / Follow-ups

| Item | Owner | Notes |
|------|-------|-------|
| QLAdmin endless-loop clearance proof | Client | Requires QuikAint load + Projected Values retest |
| QuikAing/QuikAinf stubs if UAT still fails | Conversion | Risk-authorized fallback at 0% |
| Client question: why terminated riders in projection | Client / QLAdmin | Documented in Intake — QLAdmin walks rider MPLANs regardless of status 56 |

---

## Rollback

1. Revert `qla_core/quikaint_closed_riders.py`, QuikAint hooks in `rate_emit.py` / `rate_loader_emit.py`, and schema/writer additions.
2. Remove `Output/rates/QuikAint.csv` and manifest entry.
3. Restore `APP_VERSION` to v57.75 in both `app.py` copies.
4. Re-run rate emit; confirm validators pass on prior version.

---

## Issue Log Entry (paste-ready)

> **Issue #51 — Missing Interest Table (A60MIR / A96DAR) — Ready for Client UAT (2026-07-11).**  
> **Resolution:** Added QuikAint interest-rate stubs for closed riders A60MIR and A96DAR so QLAdmin Projected Values no longer fails looking up a missing interest table.  
> **Evidence:** Validation and regression PASS; six trace policies confirmed @ 0.0000. **Preserved:** MPOLICY padding (#25), MPREM mapping (#26), quikridr status-56 rows, QuikUint ISWL-only (#32), #21D MDEPINT. **UAT:** Load QuikAint; retest Projected Values on 010348734C. **Follow-ups:** Client UAT sign-off; QuikAing/QuikAinf fallback if loop persists. **Git:** commit/push pending user request.

---

## Framework Checklist

- [x] Intake (G0)
- [x] Planning (G1)
- [x] Dependency Gate PASS (G2)
- [x] Risk — Conditional Go (G3)
- [x] Development v57.76 (G4)
- [x] Validation PASS (G5)
- [x] Regression PASS (G6)
- [x] Closure — **`Resolution:`** one-line + long-form summary (G7)
- [ ] Git commit + push — **pending user request**

**Recommended tracking sheet status:** `Ready for Client UAT` (set to **Closed** after client Projected Values sign-off)
