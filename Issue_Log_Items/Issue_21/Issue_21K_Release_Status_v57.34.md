# Issue #21K — Release Status (NOT in v57.34 closure)

| Field | Value |
|-------|-------|
| **Issue** | #21K PUA Amount Precision (MUNIT N(10,3) → N(10,5)) |
| **Engine release** | **NOT RELEASED** — excluded from v57.34 closure |
| **Reason** | Client UAT / production migration **HOLD** (2026-06-27) |
| **Companion tooling** | `qladmin_core/` shipped for client-side migration (optional deploy) |

---

## Framework status

| Stage | Status | Report |
|-------|--------|--------|
| Intake | Complete | `Issue_21K_Intake_Report.md` |
| Planning | Complete | `Issue_21K_Planning_Report.md` |
| Risk | CONDITIONAL GO | `Issue_21K_Risk_Review_Report.md` |
| Development | Complete (QLAdmin Core) | `Issue_21K_Development_Report.md` |
| Validation | CONDITIONAL PASS (repo/staging) | `Issue_21K_Validation_Report.md` |
| Client UAT | **HOLD** | `Issue_21K_Client_UAT_Report.md` |
| Closure | **NOT AUTHORIZED** | — |

---

## Why not in v57.34 release closure

Per release criteria: issues **Waiting on Client UAT** are excluded from "Released" status. Production migration on `C:\QLAdmin\Data` and six-table schema widen were not executed. QLAdmin UI UAT on policy **010448806C** is required before closure.

Conversion engine (`app.py`) is **unchanged** for 21K — `quikridr.csv` already carries full MUNIT precision.

---

## Client post-release action (when ready)

1. Backup all six QLAdmin unit tables.
2. Run `python qladmin_core/issue21k_units_migration.py --migrate-dir <QLAdmin Data>`.
3. Run `--reload-quikridr` with staging CSV.
4. Verify PUA face **$5,752.96** on **010448806C**.
5. Reindex / search regression check.

---

*v57.34 release integration — 21K remains OPEN.*
