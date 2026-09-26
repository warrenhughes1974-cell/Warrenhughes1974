# Issue #137 — Intake Summary

**Issue:** #137 — Names-tab Modalized Annual Premium  
**Framework stage:** Intake Agent (G0)  
**Status recommendation:** Intake Complete → Planning → Dependency Gate → Risk  
**Generated:** 2026-08-05  
**Owner:** Conversion  
**Priority:** High (Names-tab Modal Premiums Annl wrong vs LifePRO; billed Mode Prem already correct)

---

## Client symptom (verbatim + normalized)

**Normalized:** LifePRO Policy Values “Annually” is the **modalized** annual premium (current mode premium ÷ that mode’s modal factor). QLAdmin Names → Modal Premiums **Annl** is higher. Current-mode billed premium matches. Policy fee is separate.

Gold evidence: `9010722550C` — LifePRO Annually **436**, Monthly **40.11**, fee **25**; QLAdmin Annl ≈ **506**.

## Example policies

| QLA policy | Plan | Mode | Mode Prem | LifePRO modalized Annl (ex fee) | QLA Names Annl (MPREM×MUNIT+fee) |
|------------|------|------|----------:|--------------------------------:|---------------------------------:|
| `9010722550C` | 1659C2 | Monthly Dir | 40.11 | ~436 | 506.32 |
| `9010732078C` | 1659C2 | Semi | 59.19 | ~112.74 | 143.38 |
| `9010367131C` | 17085M | Semi | 31.20 | 60.00 | ~60 (already OK; ANN path) |

## Suspected domain

Rider / premium — `quikridr.MPREM` blank-`ANN_PREM_PER_UNIT` fallback (Issue #88 annualization). Names-tab UI math uses `(MPREM × MUNIT × factor/100) + modal_fee` (#58).

## In scope (first pass)

- Change **blank/zero ANN** `MPREM` fallback annualization from crude payments-per-year (`×12/×4/×2`) to **mode premium ÷ current mode modal factor**, then ÷ units.
- Mode-aware divisor: monthly Direct→MTHD, monthly PAC→MTHB, quarterly→QTRL, semi→SEMI, annual→100%.
- Preserve #26 populated `ANN_PREM_PER_UNIT` → `MPREM`.
- Preserve `quikmstr.MMODEPREM`, factors (#21J/#36), fees (#21C/#58), MPOLICY (#2/#25).

## Out of scope (first pass)

- QuikVal modal premiums (#128 / #93).
- Recalculating `MMODEPREM` or modal factors/fees.
- Replacing populated ANN→MPREM rows.
- Global premium engine redesign.

## Related issues

| ID | Relationship |
|----|----------------|
| **#88** | Closed — introduced crude `ann_factor`; this issue refines that fallback |
| **#26** | Preserve populated ANN→MPREM |
| **#36 / #21J** | Factors = divisors; do not regress |
| **#58** | Documents Names formula; fees untouched |
| **#128** | QuikVal — separate |

## Immediate blockers at intake

None for framing. Risk must quantify QuikVal / Coverage Prem/Unit side-effect of changing `MPREM`.

## Artifact inventory

| Artifact | Status |
|----------|--------|
| Discovery notes | `Issue_137_Discovery_Notes.md` |
| Gold policy LifePRO vs Output math | Confirmed in Discovery |
| Modal factor mapping | `QLA_Migration/Mapping/Modal_Premium_Factors_By_Plan.csv` |
| #88 interceptor location | `app.py` / `QLA_Migration/app.py` ~8815–8844 |
| Client screenshot of Names 506 | Referenced in thread; not required to frame |

## Severity / owner

- **Severity:** High — CS Names-tab quotes wrong Annl (and derived modes) when blank-ANN crude path used.
- **Owner:** Conversion (surgical `app.py` fallback).
- **Not** a missing-factor defect.
