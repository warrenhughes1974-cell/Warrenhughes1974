# DG-R-012 — Validation

**Date:** 2026-07-19  
**Data region:** `Q:\CSO\CSO_Test_6_30_2026`

| Check | Run | Result |
|-------|-----|--------|
| DG-QUIKPLAN-028 | `validation_out/DG-20260719_104850_568528` | Overall **PASS**; 2/6 checks passed; **4 WARN** residual (A60MIR/A96DAR: missing Aexp + neither Aing nor Ainf) |
| DG-QUIKPLAN-027 | `validation_out/DG-20260719_104852_794048` | Overall **PASS**; unchanged advisory (~98 WARN) |
| Unit test Aing-or-Ainf | pytest | **Pass** |

QuikAinf-only false positives cleared. No DBF writes.
