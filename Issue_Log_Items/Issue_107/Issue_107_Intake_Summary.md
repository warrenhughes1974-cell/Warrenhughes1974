# Issue #107 — Intake Summary

**Issue:** #107 — `1L1095` RV source vs L10 LP9595 (follow-up from #106)  
**Date:** 2026-07-24  
**Framework stage:** Intake complete (G0)  
**Status:** Open — blocked on source / SME confirmation  
**Parent:** #106 Defect #2  
**Owner:** Conversion (Warren) + Client (Eric) for extract / authority  
**Business status:** Open (split from Eric No-Go 7/24 on #106)

---

## Client / business symptom (verbatim from #106)

> Also included is L10 LP9595 RV factors; however, they look significantly different from what is in QLAdmin. If you can check where the QLAdmin RV rates for 1L1095 are pulling, I can try to research.

---

## Normalized finding

| Item | Finding |
|------|---------|
| QLAdmin plan | `1L1095` QuikTvs |
| Current source segment | **`L10 LP95`** (Rate_Table + inheritance parity) |
| Client compared to | **L10 LP9595** samples in `docs/RV Factor Samples.docx` |
| LP9595 in delivered Rate_Table | **0 rows** |
| Relation to #106 Dur fix | Dur identity (v58.31) aligns `1L1095` to **LP95** by duration; does **not** make LP9595 samples match |

---

## Suspected domain

Rate source / inheritance mapping for L10 fleet RV — not duration indexing.

Possible outcomes (Planning later):

1. Client confirms LP95 is correct → close as documentation / UAT reconcile  
2. Client requires LP9595 → need extract rows (or alternate authority) then remapped emit  
3. Hybrid / wrong plan code on QuikTvs → SME mapping decision

---

## Evidence already on file

| Artifact | Role |
|----------|------|
| `docs/RV Factor Samples.docx` | Client LP9595 samples |
| `Issue_Log_Items/Issue_106/*` | Parent Dur fix; lineage proof |
| Rate_Table extract | 0 × LP9595; LP95 present |
| Inheritance parity JSON | `1L1095` RV ← `L10 LP95` |

---

## Intake disposition

**Open as follow-up.** Do not merge back into #106 closure. Pre-Dev Planning/DG can run when Eric confirms intended source or supplies LP9595 rates.
