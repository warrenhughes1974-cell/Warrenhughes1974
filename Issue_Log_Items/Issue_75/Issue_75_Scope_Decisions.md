# Issue #75 — Scope Decisions

**Locked for Planning / Risk:** 2026-07-15  
**Authority:** Intake evidence + QLAdmin Help + current Output analysis (client open questions noted)

| ID | Decision |
|----|----------|
| **SD-75-1** | Target field is `quikmstr.MBANKNO` (Bank Acct on Base Data). |
| **SD-75-2** | QLA expected shape (Help): **routing number** + `/` + **payor account**; optional trailing `/S` (savings) and/or `/A` (advance draft). System **validates routing**. |
| **SD-75-3** | Conversion contract remains `ABA/ACCOUNT` (Issues #21H / #45). Fix focuses on **emit quality**, not a new field. |
| **SD-75-4** | Primary defects in scope: (a) ABA not exactly **9 digits**, (b) **extra `/`** inside ABA or account producing `//` or multi-slash, (c) **non-digit punctuation** in account (hyphens/spaces) that QLA may reject or mis-parse. |
| **SD-75-5** | Preserve Issue #45 gate: emit `MBANKNO` only when both usable ABA and usable account resolve; else blank + exception. |
| **SD-75-6** | Preserve Issue #25 MPOLICY padding and Issue #26 MPREM. No `MBILLFRM` change. |
| **SD-75-7** | Out of scope unless client expands: inventing ABA; bank-name mapping; #21H Credit Card ID vs Bank Acct UI label. |
| **SD-75-8** | UAT: policy **010161748C** (and similar) must accept Bank Acct on policy change without routing validation error after reload. |
