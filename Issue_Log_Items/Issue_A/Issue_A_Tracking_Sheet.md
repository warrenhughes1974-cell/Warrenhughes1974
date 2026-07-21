# Issue A — Tracking Sheet (Internal)

| Field | Value |
|-------|-------|
| ID | **A** |
| Track | **Internal** — do not report to client |
| Title | QuikPlan / PVO / rate-key structural defects (Robert CSO review) |
| Opened | 2026-07-20 |
| Reporter | Robert |
| Owner | Conversion + Eric/CSO |
| Status | **A10 IMPLEMENTED v58.22** — QuikUwpo emit PASS |
| Next | Reload `Test_Validation/rates/QuikUwpo.csv` in QLAdmin; continue A2/A3 when ready |

## Sub-items

| ID | Topic | Status |
|----|-------|--------|
| A1 | Single prem PAYYRS=1 + S/Q/M=0.00 | **IMPLEMENTED v58.20** — verified v58.21 |
| A2 | Calc Dfcy / deficiency reserves | **Planning — Awaiting CSO** |
| A3 | Default PVO keys (even no rates) | **Decision (Warren): every plan** — await Dev approval |
| A4 | Empty QuikPl* PLAN rows | **IMPLEMENTED v58.21** |
| A5 | Missing basis info | OPEN — awaiting Eric |
| A6 | Category settings vs keys | **PARTIAL v58.21** |
| A7 | VarGP vs PVO rates | OPEN — awaiting Eric |
| A8 | Annuity PAR/VarDB/int/schg/PVO | **a/b/e IMPLEMENTED** · c/d OPEN |
| A9 | Supp `9*` type + PAR=0 | **b IMPLEMENTED** · a OPEN |
| A10 | QuikUwpo UW class master | **IMPLEMENTED v58.22** — verified PASS |

## Deliverables

| File | Role |
|------|------|
| `Issue_A_A10_Intake_Summary.md` | A10 G0 |
| `Issue_A_A10_Planning_Report.md` | A10 G1 |
| `Issue_A_A10_Dependency_Gate.md` | A10 G2 **PASS** |
| `Reports/A10_quikuwpo_inventory.csv` | Codes used on QuikPlUw vs QuikUwpo |
| `Issue_A_Email_Questions.md` | Eric/CSO questions (A10 not required) |
| `Issue_A_Conversion_Checklist.md` | Running conversion checks |
