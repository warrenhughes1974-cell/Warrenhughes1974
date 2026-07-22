# Issue #88 — Intake Summary

**Issue:** #88 — Blank `ANN_PREM_PER_UNIT` fallback loads full `MODE_PREMIUM` into `quikridr.MPREM` (Prem/Unit)  
**Framework stage:** Intake Agent (G0)  
**Status recommendation:** Intake Complete → Planning  
**Generated:** 2026-07-21  
**Owner:** Conversion  
**Priority:** High (valuation gross premium overstated; ISWL large-face policies extreme)

---

## Client symptom (normalized)

QLAdmin valuation / ValxLife compare shows gross / mode premium far above LifePRO for some policies (example: LifePRO ~$3,085 vs QLA valuation ~$1,465,400). Policy Display Mode Prem looks correct, but Coverage **Prem/Unit** equals the full modal premium. Valuation then multiplies Prem/Unit × units.

## Example policies

| QLA policy | LifePRO | Plan | Units | Mode Prem (header) | Prem/Unit (wrong) | Val/extract MPREM1 |
|------------|---------|------|------:|-------------------:|------------------:|-------------------:|
| `010779727C` | `9010779727` | `1658C1` / `658 CEN I` | 500 | 2,930.75 | 2,930.75 | 1,465,400 |
| Population | — | ISWL-heavy | >1 | — | — | ~512 Compare rows flagged prem×units |

Evidence: QLA Policy Display screenshot; ValxLife compare workbook; Reserve Detail QLR; Issue #26 blank-ANN inventory includes this policy.

## Suspected domain

Policy / rider premium mapping — `quikridr.MPREM` (Coverage Prem/Unit), Issue #26 fallback path only.

## In scope (first pass)

- Change blank/zero `ANN_PREM_PER_UNIT` fallback for `quikridr.MPREM` so it does **not** load full phase `MODE_PREMIUM` into Prem/Unit.
- Proposed direction (user-approved intent): derive per-unit from `MODE_PREMIUM ÷ units` (details in Planning).
- Preserve Issue #26 primary map: populated `ANN_PREM_PER_UNIT` → `MPREM`.
- Preserve `quikmstr.MMODEPREM` ← policy modal premium.
- Preserve Issue #25 MPOLICY padding.

## Out of scope (first pass)

- Plan setup Var GP / Units Max on `1658C1` (Issue A / product setup).
- Recalculating actuarial ValxLife extract fields.
- Changing modal factors, fees (#58), or `MMODPREM`.
- Committing / releasing without user Validation.

## Related issues

| ID | Relationship |
|----|----------------|
| **#26** | RELEASED — mapped `ANN_PREM_PER_UNIT`→`MPREM`; blank fallback retained full `MODE_PREMIUM` (known caveat). This issue tightens that fallback. |
| **#55** | Units floor / emit — do not regress |
| **#58** | Modal fees on quikridr — do not touch |
| **Issue A / A7** | VarGP=4 on ISWL — separate plan-setup track |

## Immediate blockers at intake

None for framing. Business fallback rule needs Planning/Risk confirmation for non-annual modes and zero-unit rows.

## Artifact inventory

| Artifact | Status |
|----------|--------|
| Policy Display screenshot (`010779727C`) | Provided |
| Plan Information `1658C1` screenshot | Provided |
| ValxLife compare + QLR June 2026 | In `docs/Valuation/QLReports/` |
| Issue #26 blank ANN CSV (includes this policy) | Present |
| Prem×units population CSVs | `docs/Valuation/analysis/iswl_premium_times_units_*.csv` |

## Severity / owner

- **Severity:** High — valuation / actuarial compare distorted; admin Mode Prem can still look fine.
- **Owner:** Conversion (engine fallback in `app.py`; rulebook comment update).
- **Not** a LifePRO source extract defect for this example (`ANN_PREM_PER_UNIT` blank is source fact; wrong semantic load is conversion).
