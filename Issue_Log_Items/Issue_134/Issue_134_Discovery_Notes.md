# Issue #134 — Discovery Notes (Search & Discuss)

**Issue:** #134 — Death Benefit Notes  
**Date:** 2026-08-01  
**Framework stage:** Stage 0 Discovery complete (G-D)  
**Status recommendation:** Discovery — await **Proceed to Intake** before Pre-Dev chain  
**Owner:** Conversion (Warren)  
**Raised by:** Eric  
**Priority:** No Go (client sheet)  
**Code:** None (Discovery only)

---

## Client ask (verbatim)

> Please place any note with a File_Type code of B on the PNOTE_PolicyNotes_Extract in Memo section in the Claims Tab.

---

## Normalized finding

LifePRO **PNOTE** rows with **`FILE_TYPE = B`** are death-benefit / claim-file notes. They must appear in QLAdmin on the **Claims Tab Memo**, which is **`quikclms.MEMOTEXT`** — not the Policy Display **Memo** tab (`quikmemo`).

Today the QUIKMEMO converter emits **all** PNOTE types (no `FILE_TYPE` filter), so B notes already land on the **wrong** tab. Claims `MEMOTEXT` is currently filled with Phase 10B derivation **lineage** audit strings (`mlineage`), not LifePRO note text. Payee table `quikclmp` has **no** memo field.

---

## Source findings

| Item | Detail |
|------|--------|
| Extract | `QLA_Migration/Source/PNOTE_PolicyNotes_Extract_20260630.csv` |
| Key column | `FILE_TYPE` (header; client “File_Type”) |
| Approx counts | **B ≈ 4,149**; P ≈ 3,746; R ≈ 75; M ≈ 4; H ≈ 2 (of ~7,976 rows) |
| B content | Death/claim language common (PB=, CLAIM, PROOF, etc.) |
| Other columns | `POLICY_NUMBER`, `BENEFIT_SEQ`, `DATE_OR_NAMEID`, `TIME_OR_UW_REQ_SEQ`, `RECORD_SEQ`, `LINE_1`–`LINE_4`, … |

---

## Current vs desired behavior

| Domain | UI | Table / field | Current | Desired (#134) |
|--------|-----|---------------|---------|----------------|
| Policy memos | Policy Display → Memo tab | `quikmemo` | All PNOTE + PENSE (#21M/#50) | Keep non-B PNOTE (+ PENSE); **exclude B** |
| Claim memos | Policy Display → Claims tab → Memo | `quikclms.MEMOTEXT` | Lineage audit text | **B note text** (formatted) |
| Payees | Claims payees | `quikclmp` | N/A | **Untouched** |

---

## Related issues (preserve)

| Issue | Relevance |
|-------|-----------|
| **#21M** | Greenfield QUIKMEMO from PNOTE + PENSE; planning noted claim memos as separate domain |
| **#50** | Fixed-width PNOTE parse + MEMOKEY left-pad — keep for non-B notes |
| **#21M-FU / merge** | One row per MEMOKEY for policy memos — do not regress |
| Claims lineage path | `Sync_Rulebook_quikclms.csv` maps `mlineage → MEMOTEXT` — collision with #134 |

---

## Proposed work list (for Planning — no code yet)

1. **Route `FILE_TYPE=B` → `quikclms.MEMOTEXT`** — join on policy key to claim header(s); format similar to existing PNOTE memo text (date/time/seq + LINE_1–4).
2. **Exclude B from `quikmemo`** — stop dual-tab display.
3. **MEMOTEXT collision default (locked at Discovery):** **Replace** UI lineage text with death-benefit note text; keep lineage in Reports/Validation artifacts only (Eric may override to append).
4. **Edge cases for Planning/Risk:** multiple claims per policy; B notes with no claim row; non-B types (P/R/M/H) stay on Policy Memo only (default yes); surrender/`quikisrr` synthetic memos unchanged unless shared claim row.
5. **Validation later:** B absent from `quikmemo`; present on matching `quikclms.MEMOTEXT`; `quikclmp` untouched; non-B policy notes unchanged.

**Likely Development touchpoints (after approval only):** `qla_core/quikmemo_converter.py`, claims emit / `QLA_Migration/Configs/Sync_Rulebook_quikclms.csv` / post-emit overlay in `app.py`, Issue 134 validator.

---

## Open questions

| # | Question | Discovery default |
|---|----------|-------------------|
| 1 | Replace vs append lineage in `quikclms.MEMOTEXT`? | **Replace** with B note text; lineage → Reports only |
| 2 | Multiple claims / one policy — which claim gets the note? | Planning: prefer death-claim family; document if ambiguous |
| 3 | B notes with no `quikclms` row? | Orphan log / skip emit; do not invent claims |
| 4 | Keep P/R/M/H on Policy Memo only? | **Yes** |

---

## QuikHcmm clarification (2026-08-01 discussion)

**QuikHcmm is not the target.** QLAdmin Help §7.107 defines it as **Health Claim Memos** (`MMEMO`, keyed with health claim fields). Life death Claims Tab memo remains **`quikclms.MEMOTEXT`**.

---

## Stop

**Discovery complete (G-D).** User proceeded to Intake 2026-08-01 — Pre-Dev chain continued.