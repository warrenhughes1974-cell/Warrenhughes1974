# DG-R-001 — Business Decision

**Status:** DECIDED  
**Date:** 2026-07-18  
**Approved by:** User (chat)

## Decision

1. **Option A — Remap** remaining company codes **G** and **V** → **C** on non-List tables (QuikChrt, and QuikAgts/QuikActg if inventory finds them). Do **not** create G or V in QuikComp.
2. **Delete** bad QuikList groups (user confirmed data is bad):
   - `GTEST01`
   - `TERMG`
   - `TEST1`
3. Target company for remaps: **C** (must exist exactly once in QuikComp before Implement).

## Tables in scope (Implement)

| Table | Action |
|-------|--------|
| QuikList | **Delete** rows where `MGROUP` in (`GTEST01`, `TERMG`, `TEST1`) |
| QuikChrt | Remap `MCOMP` G/V → C |
| QuikAgts | Remap `MCOMP` G/V → C if present |
| QuikActg | Remap `MCOMP` G/V → C if present |
| QuikComp | No insert of G/V |

## Out of scope

- Billing-default fixes on deleted groups (DG-R-002 becomes N/A for these three groups; may close/defer)
- Creating companies G/V
- Auto-delete logic in conversion (see future-code note below — recommend separately)

## Future code recommendation (not part of this Implement)

See control-tower note in chat / TRACKER: prefer **detect + hold**, not silent delete, if this scenario recurs during conversion/governance.

## Risk acceptance

- Deleting the three QuikList groups is intentional; confirm no live policies still bill under those `MGROUP` values during Implement inventory.
- Remap G/V → C assumes single-company book.
