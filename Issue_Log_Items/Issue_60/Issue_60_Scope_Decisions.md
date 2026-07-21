# Issue #60 — Scope Decisions (Chris / New Era authority)

**Locked:** 2026-07-14  
**Authority:** Chris (actuary) email to Robert 7/14/2026; user direction: implement Chris’s plan  
**Supersedes:** Issue #56 Development path (add `1960PA` plan + own QuikCvs/QuikTvs)

---

| ID | Decision | Source |
|----|----------|--------|
| **SD-60-1** | **Do not** add PA plans to the plan file for this fix. Keep synthetic `*PA` on `quikridr.MPLAN` only as today; omit from `quikplan` / PA rate keys. | Chris |
| **SD-60-2** | **Do not** add conversion/plan “factors.” Let QLAdmin calculate PUA values after correct phase + base interest. | Chris |
| **SD-60-3** | PUA phase **`MPHSTAT = 41`** (Paid Up). | Chris |
| **SD-60-4** | PUA **`MEFFDATE`** and **`MAGE`** = same-policy base (phase 1) values. | Chris |
| **SD-60-5** | PUA **`MLASTANN`** = same-policy base (phase 1) value (after MEFFDATE inheritance, or copy explicitly). | Chris |
| **SD-60-6** | PUA **`MPAYUP`** = **PUA `MEFFDATE`** (eff date). Eff+1 year is the alternate Chris allowed; default to **eff** unless UAT proves QLAdmin needs +1. | Chris + Planning default |
| **SD-60-7** | Continue inheriting PUA **`MEXPRY`** from base (unchanged). Keep `MPLAN = base[:4]+"PA"`. | Existing + Chris (no PA plan file) |
| **SD-60-8** | Base plan **`1960PO`** (pilot) must have **non-zero** Cash Value NFO interest and Reserve interest/methods — not 0.00 / blank. | Chris |
| **SD-60-9** | Issue **#56** “add `1960PA` + own CV/TV/basis” is **withdrawn** in favor of #60. Re-open only if Chris later documents a “really good reason” for a separate PA plan. | User + Chris |
| **SD-60-10** | Pilot / UAT policy: **`010310404C`**. Fleet apply Track A to all PUA product rows. | Chris sample + fleet analysis |
| **SD-60-11** | **PUA only:** `MEFFDATE` / `MAGE` / `MPAYUP` / `MLASTANN` / `MPHSTAT` overrides apply **only** inside `_apply_pua_rider_inheritance` (gated by `_is_paid_up_addition_product`). **Do not** change dates or ages on other riders (ADB, WP, term, etc.) or on phase-1 base. | User Risk constraint 2026-07-14 |
| **SD-60-12** | `MPHSTAT=41` only when base phase `MPHSTAT` &lt; 50; terminated-base PUA keep current status. | Risk G3 |

---

## Workstreams

| Track | Content | Dev readiness |
|-------|---------|---------------|
| **A — `quikridr` PUA phase** | SD-60-3…7, **11**, **12** | **Conditional Go** — await Development approval |
| **B — Base interest** | SD-60-8 (`QuikPlCv.NFOINT`, `QuikPlTv` RSVINT/RSVMETH/INTMETHTV…) | **Blocked** until Chris/CSO supplies codes/rates for `1960PO` (and optional peer CRVM plans) |
