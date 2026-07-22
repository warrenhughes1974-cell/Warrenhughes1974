# Issue #88 — Tracking Sheet

| Field | Value |
|-------|--------|
| **ID** | #88 |
| **Title** | Blank `ANN_PREM_PER_UNIT` fallback → Prem/Unit × units |
| **Status** | **CLOSED ✓** |
| **Resolution** | When `ANN_PREM_PER_UNIT` is blank, `quikridr.MPREM` now uses annualized `MODE_PREMIUM ÷ NUMBER_OF_UNITS` instead of full modal premium; `quikmstr` Mode Prem unchanged. |
| **Release** | v58.23 |
| **Opened** | 2026-07-21 |
| **Anchor** | `010779727C` / `9010779727` / `1658C1` |
| **Related** | #26 (released), valuation ISWL prem×units population |

## Stage progress

| Stage | Result | Date |
|-------|--------|------|
| Intake (G0) | PASS | 2026-07-21 |
| Planning (G1) | PASS | 2026-07-21 |
| Dependency Gate (G2) | **PASS** | 2026-07-21 |
| Risk (G3) | **CONDITIONAL GO** | 2026-07-21 |
| Development (G4) | **DONE v58.23** (Grok one-time override) | 2026-07-21; no commit |
| Validation (G5) | **PASS** | 2026-07-21; validator 0 mismatches / 6934; QLA val re-run confirms anchor |
| Regression (G6) | **PASS** | 2026-07-21; 1845 intentional MPREM fixes; 0 ANN drift; #25 PASS |
| Closure (G7) | **CLOSED ✓** | 2026-07-21; G7 Output gate PASS; commit pending user |

## Deliverables

- `Issue_88_Intake_Summary.md`
- `Issue_88_Planning_Report.md`
- `Issue_88_Dependency_Gate.md`
- `Issue_88_Risk_Review_Report.md`
- `Issue_88_Development_Notes.md`
- `Issue_88_Validation_Report.md` (MPREM unit fallback — G5 PASS)
- `Issue_88_Regression_Report.md` (MPREM unit fallback — G6 PASS)
- `Issue_88_Resolution_Summary.md`
- Validator: `tools/validators/validate_issue88_mprem_unit_fallback.py`
