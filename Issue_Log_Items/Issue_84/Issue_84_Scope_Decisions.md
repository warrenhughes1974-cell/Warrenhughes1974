# Issue #84 — Scope Decisions

**Locked for Planning / Dependency Gate:** 2026-07-17  
**Authority:** User-opened claims money-field decomposition after QLAdmin screenshot vs Policy-book comparison  
**Model:** Cursor Grok 4.5 (locked)  
**Code changes:** None  

**ID note:** #80 already Closed (CSO Valuation Setup). This issue is **#84**.

| ID | Decision |
|----|----------|
| **SD-84-1** | Target table is **`quikclms`** money / decomposition fields shown on QLAdmin Claims screens: Net Payment (`MPAID`), Amount Ins (`MFACE`), Dividends (`DIVIDENDS`), Loan (`LOAN`), Net Benefits (`NETDB`), Premium (`PREMIUM`), Suspense (`SUSPENSE`), IntRate (`MINTRATE`), Interest (`MINTAMT`), Adjustments (`ADJUST`). |
| **SD-84-2** | Primary target authority for population patterns and example formulas is **`docs/Policy/quikclms.dbf`**. Primary LifePRO component authority is **PACTG** (`docs/claims_conversion_reference/PACTG_Accounting_Extract20260427.csv` and/or current Source extract of same shape). |
| **SD-84-3** | Goal is Policy-book–like **component decomposition**, not merely nonzero fill rates. Family-specific formulas (death / surrender / disbursement / maturity) may differ; Risk/Development must not force one formula onto all families without evidence. |
| **SD-84-4** | Header ↔ payee reconciliation is in scope for analysis and (after Development approval) remediation of **header** money/dates when payees already exist — especially #78 append-only cases where `quikclmp` has amounts but `MPAID`/`PDDATE` stay blank/zero. |
| **SD-84-5** | Do **not** change `CLAIMSTAT` under this issue (preserve Issue **#79**). |
| **SD-84-6** | Do **not** invent or recover new `quikclmp` payee rows under this issue (preserve Issue **#78**). Existing payee rows remain; amounts on payees are not rewritten unless a later explicit decision expands scope. |
| **SD-84-7** | Do **not** touch `quikmstr`, `quikridr`, rate tables, or premium mode fields. |
| **SD-84-8** | Claims Item **18** (partial death NETDB/MPAID/MFACE) is a predecessor, not a complete solution; #84 supersedes Item 18 for full decomposition coverage once Development is approved. |
| **SD-84-9** | Emit money-field audit CSV(s) under `QLA_Migration/Reports/` (before/after, component sources, reconciliation flags) — **not** in `Output/`. |
| **SD-84-10** | Preserve Issue **#25** MPOLICY padding and Issue **#26** MPREM mapping. |
| **SD-84-11** | No production code until G1+G2+G3 and explicit “Approved for Development”; bump both `app.py` copies when Development proceeds. |
| **SD-84-12** | Open business questions (PACTG code map, #78 header backfill, family formula targets) may be resolved at Risk with planning defaults; gate does not require client answer if defaults are documented and reversible. |
