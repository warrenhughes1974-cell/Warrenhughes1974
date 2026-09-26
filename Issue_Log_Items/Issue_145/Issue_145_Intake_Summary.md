# Issue #145 — Intake Summary

**Issue:** #145 — Vanish Flag (VB)  
**Framework stage:** Intake Agent (G0)  
**Status recommendation:** Intake Complete → Planning → Dependency Gate → Risk  
**Generated:** 2026-08-19  
**Owner:** Conversion  
**Priority:** Go

---

## Client symptom (verbatim + normalized)

**Verbatim:** For the 636 policies that have **VB** in PPOLC Billing Reason, populate `quikspec.VANISH = TRUE`.

**Normalized:** On each policy’s QuikSpec User Defined tab, set Vanish when LifePRO billing reason is **VB**. Everyone else stays off. Do not treat “eligible to vanish” or all 659-family plans as on vanish.

## Example policies

| QLA policy | LifePRO BILLING_REASON | Proposed VANISH |
|------------|------------------------|-----------------|
| 9010815236C | VB | On (T) |
| 9011050114C | VB | On (T) |
| 9011069610C | VB | On (T) |
| 9010761639C | blank | Off (F) — Issue **#146**, not this emit |
| 9010760840C | blank | Off (F) — Issue **#146**, not this emit |

## Suspected domain

Policy User Defined — `quikspec.VANISH`. Same table as resident state (#132) and reserve category (#141).

## In scope (first pass)

- Map `PPOLC.BILLING_REASON = VB` → `quikspec.VANISH` true.
- Leave non-VB policies at false (current default).
- Leave `VANISHDT` blank.
- Validator + fail-closed smoke (required at Close): count matches the extract under conversion; gold traces on; negative traces off.

## Out of scope (first pass)

- `VANISHDT` / New Era / CSO licensee date path (**#22** stays research).
- All 659 / “eligible to vanish” / `BA_OR_VANISH_FLAG` (blank in extract).
- QuikIsrr / #34 unit rows.
- Non-VB leftover unit drops (**#146**).
- Changing `RESSTATE` or `RESRVCAT`.
- Recreating QUIKSPEC.DBF (append-only).

## Related issues

| ID | Relationship |
|----|----------------|
| **#22** | Vanish Option research (No-Go). Flag-driven QLA; eligible ≠ on vanish. Stays open. |
| **#34** | QuikIsrr anniversary units — do not change. |
| **#132** | RESSTATE on the same QuikSpec row — do not change. |
| **#141** | RESRVCAT on the same QuikSpec row — preserve Closed fill. |
| **#146** | Non-VB unit leftovers (9010761639 / 9010760840). |

## Immediate blockers at intake

None. Source PPOLC is in the package. Target field already exists (default F). Warren locked VB = vanish at Discovery (2026-08-18). VANISHDT stays blank (confirmed after Discovery).

## Artifact inventory

| Artifact | Status |
|----------|--------|
| Discovery notes | `Issue_145_Discovery_Notes.md` |
| PPOLC 20260630 | In `QLA_Migration/Source/` — 636 VB |
| PPOLC 20260731 | In `LifePRO_Extracts_20260731/` — 635 VB |
| Current `quikspec.csv` | 5,083 rows; VANISH all **F**; VANISHDT blank; RESRVCAT filled (#141) |

## Severity / owner

- **Severity:** Medium — vanish flag missing on policies that are already on vanish in LifePRO.
- **Owner:** Conversion (Warren). Sheet owner QLA.
