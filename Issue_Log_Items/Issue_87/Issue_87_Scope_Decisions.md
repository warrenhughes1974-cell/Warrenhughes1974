# Issue #87 — Scope Decisions (Risk-locked)

**Issue:** #87 — QuikForge Balancing  
**Locked:** 2026-07-19 by Risk Agent (Planning §5 Q1–Q5)  
**Status:** Locked for Development unless user overrides before Dev  

| ID | Question | Locked default | Rationale |
|----|----------|----------------|-----------|
| **Q1** | Auto-run after Full Batch? | **Button-only v1** | Avoid lengthening Full Batch; operator opt-in. Optional post-batch flag is a follow-up, default **off**. |
| **Q2** | Control set size? | **Full ~17 controls** (BAL-C01–C08, BAL-D01–D07, BAL-I01–I02) | Still one CSV; methodology covers all. Reduced set rejected — undercuts audit value. |
| **Q3** | EXPLAINED seed? | **Converter-documented filters only** | UV/FV/SL + seq; CREDIT 110 (+prmh excluded codes); 516; QuikLoan zero-balance hold; non-product BENEFIT_SEQ 99/UV. Expand via `balancing_exclusions.csv`. |
| **Q4** | Source folder resolution? | **Mirror Governance Audit** | Same UI Source folder / prompt pattern; reuse `resolve_table_source`. |
| **Q5** | Open Balancing folder? | **After successful run** (messagebox / open path) | No second permanent Ops button in v1. |

## Hard scope (unchanged)

- Read-only reconciliation — **zero** conversion row deltas  
- **No** Sync_Rulebook edits  
- Reports only under `QLA_Migration/Balancing/`  
- Distinct from `claims_analysis/` family balancing  
- Preserve Issue #25 MPOLICY padding and Issue #26 MPREM mapping  
