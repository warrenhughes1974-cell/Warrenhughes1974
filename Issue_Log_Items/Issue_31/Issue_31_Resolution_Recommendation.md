# Issue #31 — Resolution Recommendation

**Date:** 2026-06-30  
**Research pass:** PSEGT / PDINT / PDINTTBL follow-up (20260629 extracts)

---

## Question

Can Issue #31 be marked **Resolved**?

## Answer

**No — not fully resolved.**  
**Yes — source dependency resolved.**

---

## Recommended status

| Status | Applies to |
|--------|------------|
| **Resolved — Source Dependency** | PSEGT, PDINT, PDINTTBL delivery and validation |
| **Open — Implementation** | QUIKUINT, QUIKCOI, QUIKGCOI, QUIKGPS, QUIKISSC, Expenses loaders |
| **Open — SME** | PDINT IDENT mapping, U6/U5 semantics, SR/SL decode, expense segment model |
| **Conditional ready** | QUIKCVS (8/8 segment + rate coverage; parity check pending) |

---

## What changed (20260629)

| Before | After |
|--------|-------|
| PSEGT missing — hierarchy blocked at PCOVRSGT | **696-row PSEGT extract** joins 185/191 ISWL slots |
| PDINT/PDINTTBL missing — QUIKUINT blocked | **10 + 37 rows**; CENII A1 **4.50%** confirmed |
| 6/7 QLA areas "blocked" on source | **0/7 fully blocked** on source; **1/7 fully resolved** (QUIKCVS) |

---

## What remains open

1. **QLAdmin table schemas** (QUIKUINT, QUIKCOI, QUIKGCOI, QUIKISSC) not in repo
2. **Expense codes** U1/U2/U3/G2/G3/GF — zero PSEGT rows
3. **PAAGERAT segment-ID indirection** — U6/U5/BP rates keyed to SD parent coverages
4. **PPRDF** extract still absent (top of hierarchy incomplete in repo)
5. **Implementation** — no loaders/converters changed (by design)

---

## Gate for full closure

Issue #31 may move to **Fully Resolved** when:

- [ ] SME signs PDINT IDENT → 8 MPLAN interest mapping  
- [ ] QUIKCVS PDAGE/Rate_Table parity PASS  
- [ ] At least one UL target (QUIKUINT or QUIKCOI) has approved QLAdmin schema + trace proof on 2+ flagship MPLANs  
- [ ] Expense model decision documented (UF-only vs nested premium segments)

Until then: **close source dependency only**; route to Implementation Planning + SME Review agents.

---

See: `Issue_31_PSEGT_PDINT_Followup_Report.md`
