# Issue #88 — Resolution Summary

**Issue:** #88 — ISWL QuikIssc / QuikUint empty in batch CSV package (D1 + D2)  
**Framework stage:** Closure Agent (G7)  
**Final status:** **Closed — Ready for Client UAT**  
**Release:** Rate emit path only — **no `app.py` version bump** (batch already calls `qla_core.rate_emit`)  
**Closed date:** 2026-07-21  
**Owner:** Conversion (Warren)  
**Model note:** Development + Closure completed under user **one-time Grok 4.5 override** (locked map: Composer 2.5)  
**Parent:** `Issue_ISWL` defects D1 / D2 (Sujitha email 2026-07-20)

---

## Resolution (issue log — paste-ready)

**Resolution:** Batch rate CSV emit now writes QuikIssc and QuikUint, and PDINT/PSEGT config paths point at the 20260630 Source extracts, restoring 8 ISWL surrender-charge rows and 32 credited-interest rows in the delivery package.

> Copy the line above into tracking sheets and client readouts. Long-form detail follows.

---

## Problem Statement

Sujitha reported missing QUIKISSC surrender charges for ISWL plans 1659CR, 1659SR, and 1669SR. Package review showed a larger failure: delivered `QuikIssc.csv` and `QuikUint.csv` were header-only (0 data rows) for the entire ISWL fleet, blocking ISWL CSO UAT.

---

## Root Cause

| Defect | Cause |
|--------|--------|
| **D1** | `qla_core/rate_emit.py` CSV branch never called `write_quikissc_csv` / `write_quikuint_csv` (DBF branch and R5 CLI already did) |
| **D2** | `rate_loader_config.json` still referenced missing `*_20260629` PDINT/PDINTTBL/PSEGT files; Source had `*_20260630` — `V-UINT-PDINT` fired and QuikUint stayed empty under partial emit |

LifePRO SL / PDINT source data and Issue #32/#33 loaders were already correct.

---

## Resolution (long-form)

| Area | Before | After |
|------|--------|-------|
| QuikIssc.csv | 0 rows | **8** (all ISWL MPLANs, hub SL schedule) |
| QuikUint.csv | 0 rows | **32** (4 tiers × 8 MPLANs) |
| Config PDINT/PSEGT | 20260629 (missing) | **20260630** (present) |
| Factor tables Coi/Gcoi/Gps/Cvs | — | **Unchanged** |

### Files changed

| File | Change |
|------|--------|
| `qla_core/rate_emit.py` | CSV writes for QuikUint + QuikIssc + RATE_LOG counts |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | 3 paths → 20260630 |
| `rate_loader_config.example.json` | same |

### UAT package

| File | Location |
|------|----------|
| QuikIssc.csv | `QLA_Migration/Output/rates/` and `Output/Test_Validation/rates/` |
| QuikUint.csv | same |

---

## Validation / Regression

| Stage | Verdict | Artifact |
|-------|---------|----------|
| Validation | **PASS** (25/25) | `Issue_88_Validation_Report.md` |
| Regression | **PASS** | `Issue_88_Regression_Report.md` |
| Issue #32 / #33 baselines | Match | Phase5 32 rows; Phase6 SCHG schedule |

---

## Client readout (Sujitha)

1. Surrender charges for **all eight** ISWL plans (including 1659CR / 1659SR / 1669SR) are restored — same hub schedule as Issue #33.  
2. ISWL credited interest (QuikUint) is restored — four historical tiers per plan.  
3. Reload from the corrected rate CSVs under `Output/rates/` (or `Test_Validation/rates/`).  
4. Open business questions (COI basis, GLP, loan credited rate, etc.) remain on **Issue_ISWL** — not part of #88.

---

## Network / pull instructions

After git push of this issue:

1. `git pull` on the batch machine  
2. Confirm `rate_loader_config.json` PDINT/PSEGT paths resolve under `QLA_Migration/Source/`  
3. Run **GENERATE RATE TABLES** (CSV emit) or full batch with rates included  
4. Confirm `Output/rates/QuikIssc.csv` = 8 rows and `QuikUint.csv` = 32 rows  

No `APP_VERSION` bump required for this fix.

---

## Gate checklist (G7)

| Item | Result |
|------|--------|
| Resolution one-liner published | **Yes** |
| Resolution summary + tracking updated | **Yes** |
| app.py version bump | **N/A** (not touched) |
| Validation + Regression PASS | **Yes** |
| Issue-scoped git commit | Per Closure |
| Push to remote | Per Closure / user |

**Status:** **Closed**
