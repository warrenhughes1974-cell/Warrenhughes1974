# Issue #98 — Regression Report

**Issue:** #98 — CV Endpoint Off By One  
**Framework stage:** Regression Agent (G6)  
**Result:** **PASS**  
**Date:** 2026-07-22  
**Engine version:** v58.27

---

## Surfaces checked

| Surface | Result | Notes |
|---------|--------|-------|
| Issue #41 endpoint (`1960PO`) | **PASS** | Age-100 endpoint rule retained (`return lp_d`) |
| Issue #37 first-duration bands M 18–22 / M 24+ | Preserved | Only M 1–17 matrix cell changed |
| Issue #40 inherited CV presence (`17085M`) | Intact | Plan still emits QuikCvs keys |
| Issue #96 SAL MULTPL keys | **PASS** | Durable companion keys, not Output patch |
| Rate package parity | **PASS** | Full `Output/rates` vs pipeline expectation |
| Manifest hygiene | **PASS** | No stale zero-row Uint/Aint/Issc member entries |

---

## Non-candidate / out of scope

- `QuikAing` intentionally tracked separately (`Rate_Audit_20260723/QuikAing_Scope_Decision.md`)
- Post-load QLAdmin export parity remains a UAT gate after reload
