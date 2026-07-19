# DG-R-012 — Business Decision

**Status:** DECIDED  
**Date:** 2026-07-19  
**Approved by:** User (chat)

## Decision

**Option R1**

1. **Revise DG-QUIKPLAN-028:** require QuikAint and QuikAexp; require QuikAing **or** QuikAinf (not both).
2. **Accept DG-QUIKPLAN-027** as intentional advisory audit (no rule change).
3. **No DBF writes.**

## Evidence

- `Data_Goverence.txt` already stated Aing/Ainf interchangeability.
- WPA QuikAinf has 0 rows; requiring both created permanent false advisories.
- 027 text explicitly requires audit-log warnings for incomplete traditional value setups; WPA has the same gaps.

## Residuals (accepted)

- CSO 027: ~98 traditional WARN (closed riders / incomplete CV suites).
- CSO 028: A60MIR / A96DAR still warn (missing Aexp and neither Aing nor Ainf) — overlaps DG-R-009 deferral.
