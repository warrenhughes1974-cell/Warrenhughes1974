# Issue #71 — Scope Decisions

**Locked for Planning / Risk:** 2026-07-14  
**Authority:** User — “everything on the plan code, policy level and keys are all zero”

| ID | Decision |
|----|----------|
| **SD-71-1** | Canonical band for this conversion is **`00`** (QLAdmin “NOT APPLICABLE”). |
| **SD-71-2** | **`quikridr.MBAND`** remains **`00`** (already fleet-wide; Chris 2026-07-14 — do not use `01`). |
| **SD-71-3** | All single-band rate factor/key tables currently on `01` remap to **`00`**. |
| **SD-71-4** | **`QuikPlBd`**: emit/remap `BDCODE=00`, description “NOT APPLICABLE”. |
| **SD-71-5** | Multi-band GP (`QuikGps` / `QuikPlGp` with `01`/`02`/`03`): collapse to `00` using Planning collision rule (keep one row per key — prefer former `01` content; drop/merge `02`/`03` duplicates). Flag for UAT on `5L01MA` peers. |
| **SD-71-6** | No change to NFOINT / mortality / UWCLASS / gender. |
| **SD-71-7** | Development only after G1+G2+G3; surgical rate-path + band-member emit; version bump if `app.py` touched. |
