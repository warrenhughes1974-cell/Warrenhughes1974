# Issue #79 — Scope Decisions

**Locked for Planning / Risk / Development:** 2026-07-17  
**Authority:** User approval of Policy-book claim status convention (“Okay thats what we want…”)

| ID | Decision |
|----|----------|
| **SD-79-1** | Authority for CLAIMSTAT conventions is `docs/Policy/quikclms.dbf` (real QLAdmin claim book). |
| **SD-79-2** | Finished **death** claims → `CLAIMSTAT = 2` (Paid in Full), not 3. |
| **SD-79-3** | **Surrender / partial surrender / disbursement-withdrawal** claims → `CLAIMSTAT = 99`. |
| **SD-79-4** | **Maturity** claims → `CLAIMSTAT = 98` when family is maturity. |
| **SD-79-5** | `CLAIMSTAT = 1` (Pending) only when the claim is truly open/unpaid (no payment evidence and no settled/paid lifecycle). |
| **SD-79-6** | Apply to all emitted `quikclms` rows in Output (not a tiny sample). Non-candidate tables untouched. |
| **SD-79-7** | Do **not** change `quikclmp` amounts/payees under this issue (preserve #78). |
| **SD-79-8** | Prior Item 15 recommendation of death CLAIMSTAT=3 is **superseded** for consistency with Policy book (deaths → 2). |
| **SD-79-9** | Emit `Reports/issue79_claimstat_remap_audit.csv` (before/after, family, reason) — not in Output. |
| **SD-79-10** | Development only after G1+G2+G3 and explicit “Approved for Development”; bump both `app.py` copies. |
