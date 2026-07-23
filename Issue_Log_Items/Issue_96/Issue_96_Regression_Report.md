# Issue #96 — Regression Report

**Issue:** #96 — CSO val cannot use SAL MULTPL / L17 RV  
**Framework stage:** Regression Agent (G6)  
**Result:** **PASS**  
**Date:** 2026-07-22  
**Engine version:** v58.27 (rate package includes durable `#96` companion keys)

---

## Surfaces checked

| Surface | Result |
|---------|--------|
| `validate_issue96_cso_pvo.py` | **PASS** — 8 focus plans PVO + QuikPl* / QuikTvs |
| L17 RV inheritance validator | **PASS** — children match `1L17SP`; Track 2 held |
| Annuity A8e `PLANVALOPT=N` | **PASS** (`A60MIR`, `A96DAR`) |
| Issue #98 CV anchors | **PASS** (same rate release) |
| Rate audit package parity | **PASS** |

## Non-changes preserved

- QuikTvs factor values (Track 1 inheritance)
- Track 2 RV holds (L01/L05/L07/667 ART)
- Issue #95 QuikUint scope (separate)
