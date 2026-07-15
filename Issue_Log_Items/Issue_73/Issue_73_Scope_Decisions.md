# Issue #73 — Scope Decisions

**Locked for Planning / Risk:** 2026-07-15  
**Authority:** Client rule — Issue Country must be `0000` for all policies

| ID | Decision |
|----|----------|
| **SD-73-1** | Target field is `quikmstr.MISSCNTRY` (Issue Country). Client “country date” = country code, not a calendar date. |
| **SD-73-2** | Emit **`0000`** for **all** converted policies (fleet-wide constant). |
| **SD-73-3** | Preferred fix: change Sync Rulebook default `USA` → `0000` on the blank-source `MISSCNTRY` row (no LifePRO source column). |
| **SD-73-4** | **Out of scope:** `quikclnt.MCOUNTRY` (mailing/address country), `MISSUEST`, `MRESSTATE`, rate-key emit (`ISSCNTRY` already `0000`). |
| **SD-73-5** | No change to MPOLICY padding (#25), MPREM (#26), or other `quikmstr` fields. |
| **SD-73-6** | UAT: after batch, `MISSCNTRY` count where value ≠ `0000` must be **0**; spot-check any 3 policies on Policy Display Issue Country. |
