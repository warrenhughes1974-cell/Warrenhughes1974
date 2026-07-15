# Issue #74 — Scope Decisions

**Locked for Planning / Risk:** 2026-07-15 (revised)  
**Authority:** Client clarification — only plans currently at Var DB Code `4` become `0`; non-`4` plans stay

| ID | Decision |
|----|----------|
| **SD-74-1** | Target field is `quikplan.VARDB` (Var DB Code). |
| **SD-74-2** | Change **only** plans where `VARDB` is currently **`4`** → **`0`**. |
| **SD-74-3** | **Do not change** plans that already have `VARDB` ∈ {`1`,`2`,`3`} (Option B structure codes). Leave those values as-is. |
| **SD-74-4** | Preferred fix: Sync Rulebook default `4` → `0`. **Keep** Option B structure overrides so classified plans continue to emit `1`/`2`/`3`. |
| **SD-74-5** | **Out of scope:** `VARGP`, `*VARYDB` flags, QuikDbs rebuild, forcing `0` on structure-coded plans. |
| **SD-74-6** | No change to MPOLICY (#25), MPREM (#26), or policy tables. |
| **SD-74-7** | UAT: count(`VARDB=4`) = **0**; count(`VARDB=0`) = prior count of `4` (~121); plans formerly `1`/`2`/`3` unchanged. |
