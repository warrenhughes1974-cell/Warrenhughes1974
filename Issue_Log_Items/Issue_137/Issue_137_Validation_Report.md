# Issue #137 — Validation Report

**Issue:** #137 — Names-tab Modalized Annual Premium  
**Framework stage:** Validation  
**Engine:** v58.80  
**Date:** 2026-08-05  
**Result:** **PASS**

---

## Validators

| Check | Command | Result |
|-------|---------|--------|
| #137 | `python tools/validators/validate_issue137_modalized_mprem.py` | **PASS** |
| #88 (updated rule) | `python tools/validators/validate_issue88_mprem_unit_fallback.py` | **PASS** (#26 ANN soft warns only) |

Evidence: `evidence/issue137_validation_summary.json`, `evidence/issue137_apply_summary.json`

## Gold

| Policy | Field | Expected | Actual |
|--------|-------|----------|--------|
| `9010722550C` | MPREM×MUNIT | ~436 | **435.98** |
| `9010722550C` | MMODEPREM | 40.11 | 40.11 (unchanged) |
| `9010367131C` | MPREM (#26 ANN) | 9.12 | 9.12 |

Names-tab Annl with fee may show ~**460.98** (435.98+25) — premium base matches LifePRO modalized annual.

## Fleet

- Blank-ANN rows checked: **1,848** — 0 formula mismatches vs helper  
- Output MPREM cells updated by apply: **1,027**  
- Published: `QLA_Migration/Output/Test_Validation/quikridr.csv`

## Notes

- Full converter re-batch will emit the same rule from v58.80; surgical apply used for this Validation.  
- Pre-existing ANN≠MPREM zeros/drifts remain WARN-only on #88 (out of #137 scope).
