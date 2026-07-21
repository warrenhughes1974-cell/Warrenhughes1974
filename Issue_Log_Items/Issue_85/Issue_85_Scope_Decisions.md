# Issue #85 — Scope Decisions & Decisions Needed

**Locked framing:** 2026-07-17  
**Decisions locked:** 2026-07-17 — expert recommendation adopted per user instruction (“make your best guess as an insurance conversion expert”).  
**Client / conversion owner approval:** **2026-07-17** — user: “Approve and lets proceed.” D1–D5 approved as written in `Issue_85_Decisions_For_Review.md`.  
**Model:** Cursor Grok 4.5 (locked)  
**Code changes:** None  

---

## DECISIONS — LOCKED 2026-07-17

New evidence that drove the decisions: in the **real Policy book**, 20 policies have more than one claim, and every one of them puts **each claim on its own phase** (0, 2, 3, 4) with its **own claim number**. The book never stacks two claims on one phase. Our duplicate groups split into two kinds:

| Kind | Groups | Rows | Meaning |
|------|-------:|-----:|---------|
| Same claim number repeated on one phase | 150 | 327 | True duplicates — one claim emitted twice |
| Different claim numbers sharing one phase | 566 | 3,443 | Real separate events crowded onto one phase |

| # | Decision | Locked choice | Why (expert rationale) |
|---|----------|---------------|------------------------|
| **D1** | Unique claim rule | **Hybrid: identity = claim number.** Same claim number on same phase → **merge into one header** (150 groups). Different claim numbers sharing a phase → **renumber phases** so each claim gets its own phase, exactly like the real book (566 groups). | Matches the only precedent we have (real book multi-claim pattern). Preserves real claim history instead of destroying it by over-merging. |
| **D2** | Winner / merge rule | For same-claim-number merges: **one surviving header** — sum Net Payment (header = total paid, book convention), keep earliest death/reported dates, **latest** paid date, keep the populated Amount Ins (MFACE), keep #79-mapped status. | The book’s headers carry claim totals with final settlement dates; summing preserves dollars without invention. |
| **D3** | Losing rows | **Drop from the load file + keep a full before/after audit CSV** in `QLA_Migration/Reports/` (D3-A + D3-B). No memo rewriting. | Rollback-safe: audit preserves history; load stays clean for QLAdmin. |
| **D4** | Payee re-attach | **Payees follow their claim.** After phase renumbering, match payee checks to their claim event by payment date/amount (D4-C). If a check can’t be matched, attach it to the surviving header and flag it in the audit (D4-A fallback). | Keeps check-to-claim truth where provable; nothing orphaned; exceptions visible, not silent. |
| **D5** | Sequencing vs #84 | **#85 ships before #84 Track B.** #84 **Track A** (backfill Net Payment/Paid date where header is $0 but checks exist) may proceed independently now (D5-A + Track A carve-out). | Balancing money onto a broken header structure would have to be redone; Track A is safe either way. |

**Standing guards (unchanged):** no new payees invented (#78), no CLAIMSTAT rule changes (#79), no quikmstr/quikridr/rates, audit files in Reports/ not Output.

---

These were the **business decisions required** before Development. Original options preserved below for the record; Planning defaults shown; client may override any locked choice above before Development approval.

---

## Locked scope boundaries

| ID | Decision |
|----|----------|
| **SD-85-1** | Problem is **duplicate `quikclms` headers** sharing the same policy + phase (3,054 rows), unlike real Policy book (0 duplicates). |
| **SD-85-2** | Goal: each live claim header has a **unique QLAdmin claim identity** so payees can attach and Net Payment can balance (Policy-book pattern). |
| **SD-85-3** | Do **not** invent new payees (#78). Existing `quikclmp` rows must remain and re-attach under the chosen rule. |
| **SD-85-4** | Do **not** change CLAIMSTAT rules (#79). Status values may move with a kept header, but mapping rules stay #79’s. |
| **SD-85-5** | Money component fill (Dividends, Loan, etc.) stays in **#84**; this issue only fixes header structure / identity. |
| **SD-85-6** | No production code until G1+G2+G3 and explicit Development approval. |

---

## Decisions needed from you (client / conversion owner)

### Decision 1 — What makes a “unique claim” in QLAdmin?

**Question:** When LifePRO has several claim/settlement events on one policy, how should they appear in QLAdmin?

| Option | Plain English | Tradeoff |
|--------|---------------|----------|
| **D1-A (recommended default)** | Keep **one header per policy + phase**, like the real Policy book. Merge duplicate headers into that one row (combine or pick the “best” claim). | Matches real book; may lose separate claim-number history on screen |
| **D1-B** | Keep multiple headers, but give each a **different phase** (2, 3, …) so QLAdmin can tell them apart | Preserves multiple claim stories; changes phase meaning vs today’s emit |
| **D1-C** | Keep multiple headers under phase 1, but make **Claim Number** the true key and force QLAdmin uniqueness another way | Only valid if QLAdmin truly keys on claim number (needs proof) |

**Needed:** Choose D1-A, D1-B, or D1-C.

---

### Decision 2 — When we collapse duplicates, which header “wins”?

**Question:** If two+ headers share policy+phase, which one do we keep as the main claim row?

| Option | Plain English |
|--------|---------------|
| **D2-A (default)** | Keep the header that has the **most recent paid/settlement date** (or latest claim event) |
| **D2-B** | Keep the header with the **largest Net Payment / payee activity** |
| **D2-C** | Keep **death claims over surrenders** when both exist; otherwise newest |
| **D2-D** | Keep all money history by **summing** selected money fields onto the winner (only if safe) |

**Needed:** Choose winner rule (can combine, e.g. D2-C then D2-A).

---

### Decision 3 — What happens to the losing duplicate headers?

| Option | Plain English |
|--------|---------------|
| **D3-A (default)** | **Drop** losing headers from `quikclms` after moving/attaching payees to the winner |
| **D3-B** | Keep losers in an **audit / hold** file only (not loaded to QLAdmin) |
| **D3-C** | Convert losers to **memo / note** text on the winner (if client wants history visible) |

**Needed:** Choose D3-A / B / C.

---

### Decision 4 — How do payee (check) rows re-attach?

| Option | Plain English |
|--------|---------------|
| **D4-A (default)** | All existing payees for that policy+phase attach to the **winning** header’s phase |
| **D4-B** | Split payees by check date / amount matching each original claim event (harder; needs PACTG proof) |
| **D4-C** | If phases are renumbered (D1-B), move each payee with its claim to the new phase |

**Needed:** Choose D4-A / B / C (depends on Decision 1).

---

### Decision 5 — Sequencing vs Issue #84

| Option | Plain English |
|--------|---------------|
| **D5-A (recommended)** | Do **#85 structure first**, then #84 Track B money balancing |
| **D5-B** | Do #84 Track A only now (header Net Payment backfill where blank); park #84 Track B until #85 ships |
| **D5-C** | Attempt #84 Track B without #85 (Risk already flagged this as high risk) |

**Needed:** Confirm D5-A or D5-B (D5-C not recommended).

---

## Planning defaults (if you want to move fast)

Until you override:

1. **D1-A** — one header per policy + phase (Policy-book style)  
2. **D2-A + D2-C** — prefer death over surrender when both; else newest settlement  
3. **D3-A + D3-B** — drop from load file; keep full before/after audit  
4. **D4-A** — attach all phase payees to winner  
5. **D5-A / D5-B** — #85 before #84 Track B; #84 Track A may still proceed alone  

---

## What we do *not* need a decision on yet

- Exact PACTG dividend/premium codes (#84 OBQs)
- CLAIMSTAT values (#79 already decided)
- Whether to invent missing payees (#78 already done; no new invent here)
