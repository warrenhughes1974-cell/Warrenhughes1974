# Issue #78 — Scope Decisions

**Locked for Planning / Risk / Development:** 2026-07-17  
**Authority:** User approval of three-tier payee fallback (“Okay this is approved…”)

| ID | Decision |
|----|----------|
| **SD-78-1** | Recover `quikclmp` payment rows for policies that have a `quikclms` claim header but **zero** payment rows, when LifePRO PACTG contains **live, non-reversed** payout transactions (codes **90 / 92 / 94 / 567 / 1900**). |
| **SD-78-2** | **Tier 1 — single PE:** If the policy has exactly one distinct `RELATE_CODE=PE` name in `RelationshipNameAddress`, use that payee’s name + address on the recovered payment row(s). |
| **SD-78-3** | **Tier 2 — multiple PE:** If 2+ distinct PE names exist: when payout count matches payee count, pair one-to-one by amount/date order; otherwise assign the **primary PE** (first/lowest sequence) to all recovered rows and tag MEMO / audit lineage so Tier 2 is reviewable. |
| **SD-78-4** | **Tier 3 — no PE:** Prefer beneficiary of record (`B1`, then other beneficiary codes if present); if none, use **`ESTATE OF [insured KEY_NAME]`** with the insured’s last known address (`IN` / `INSD` relationship). |
| **SD-78-5** | Amounts, check/payment dates come from PACTG payout rows (not invented). Check number: use CONTROL_NUMBER when usable; otherwise follow existing `quikclmp` derivation convention / blank-safe default used by Phase 10A. |
| **SD-78-6** | Do **not** delete or rewrite existing `quikclmp` rows for policies that already have payments. Non-candidate policies unchanged. |
| **SD-78-7** | Do **not** invent new `quikclms` claim headers under this issue. Header-only lifecycle fixes (Pending→Settled, ORIGSTTUS, CAUSE) are **out of scope** unless a later decision folds them in. |
| **SD-78-8** | Emit an Issue #78 recovery audit CSV under `QLA_Migration/Reports/` (tier, policy, amount, payee source) — **not** in `Output/`. |
| **SD-78-9** | Preserve Issue **#25** MPOLICY padding and Issue **#26** MPREM mapping. No `quikmstr` / `quikridr` / rate changes. |
| **SD-78-10** | Development only after G1+G2+G3 and explicit “Approved for Development”; surgical change; bump `APP_VERSION` in both `app.py` copies. |
