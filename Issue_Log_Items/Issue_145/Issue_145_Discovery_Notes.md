# Issue #145 — Discovery Notes (Search & Discuss)

**Issue:** #145 — Vanish Flag (VB)  
**Date:** 2026-08-18  
**Framework stage:** Stage 0 Discovery (G-D)  
**Code:** None  

---

## Client ask (verbatim)

For the 636 policies that have **VB** in PPOLC Billing Reason, populate `quikspec.VANISH = TRUE`.

---

## Verdict

This is a **QuikSpec flag mapping**, not a new table. QuikSpec is already emitted (v58.92) with resident state. `VANISH` is currently defaulted to **False** for every policy. The locked source for “on vanish” is `PPOLC.BILLING_REASON = VB` (636 policies on the 2026-06-30 extract).

Do **not** treat this as “all 659 / all eligible to vanish.” That was the Issue 22 trap. VB is the on-vanish code; blank billing reason stays `VANISH=False`.

---

## Source findings

**File:** `QLA_Migration/Source/PPOLC_PolicyMaster_Extract_20260630.csv`  
**Field:** `BILLING_REASON`

| Billing Reason | Count | Meaning used here |
|---|---:|---|
| (blank) | 3,322 | Not on vanish |
| **VB** | **636** | On vanish — set `VANISH=TRUE` |
| PU | 344 | Paid Up |
| RU | 304 | Reduced Paid Up |
| ET | 291 | Extended Term |
| PC | 169 | Premium Ceased |
| WD | 17 | Withdrawal |

Meeting examples:

| Policy | BILLING_REASON | Action |
|---|---|---|
| 9010815236 | VB | `VANISH=TRUE` |
| 9011050114 | VB | `VANISH=TRUE` |
| 9011069610 | VB | `VANISH=TRUE` |
| 9010761639 | blank | Leave False |
| 9010760840 | blank | Leave False |

All five still have `BILLING_CODE=A` (active billing).

---

## Current conversion vs desired

| Area | Current | Desired |
|---|---|---|
| `quikspec` emit | Yes — MPOLICY + RESSTATE from PPOLC | Keep |
| `VANISH` | Default **F** (`Sync_Rulebook_quikspec.csv`) | **TRUE** when `BILLING_REASON=VB`; else False |
| `VANISHDT` | Blank | Stay blank unless Intake locks a date source |
| Non-VB policies | VANISH False | Unchanged |

---

## Related issues

| Issue | Relationship |
|---|---|
| **#22 Vanish Option** | Research issue (No-Go). Established QLA is flag-driven and “eligible to vanish” ≠ on vanish. #145 is the conversion action using VB as the on-vanish source. |
| **#34 QuikIsrr** | Many VB policies also have anniversary 0561 rows equal to billed premium (no check). That is context for units, **not** this emit. Do not change QuikIsrr in #145. |
| **#146 Non-VB Unit Reductions** | Leftover 0561 unit drops that are **not** VB. Opened 2026-08-18 from the same call. |

Overlap note (not in scope): 587 of 636 VB policies also have QuikIsrr history; 49 VB have no 0561; 50 0561 policies are not VB (including 9010761639 and 9010760840).

---

## Proposed work list (Planning will refine)

1. Map `PPOLC.BILLING_REASON=VB` → `quikspec.VANISH=TRUE` (636 rows).
2. Leave all other `VANISH` as False.
3. Do not invent `VANISHDT`.
4. Validator: count 636 TRUE; examples above; no FALSE→TRUE on non-VB.

---

## Open questions

1. Confirm with Eric that VB means vanish billing / on vanish (internal codebook still says “Variable Billing”).
2. Is `VANISHDT` required for CSO (Issue 22 / Sujitha-Greg licensee path), or flag-only?
3. Should #22 stay open as the New Era / VANISHDT research, with #145 as the VB flag only?

---

## Stop

Discovery complete 2026-08-18. Intake → Risk completed 2026-08-19. Awaiting **Approved for Development**.
