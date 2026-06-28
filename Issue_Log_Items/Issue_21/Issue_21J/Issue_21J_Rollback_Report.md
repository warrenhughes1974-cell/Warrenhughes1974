# Issue #21J — Rollback Report

**Issue:** Modal Premium Factors — QUIKMEMO Enhancement Rollback  
**Date:** 2026-06-28  
**Rolled back from:** v57.37  
**Rollback version:** v57.38  
**Authority:** Planning Correction Report + Development Decision  
**Stage:** Development Rework / Rollback ✅

---

## 1. Executive Summary

Issue #21J v57.37 added a QUIKMEMO `[CONVERSION]` segment documenting QLAdmin standard plan-level modal factors on every converted policy. The **Planning Correction Agent** determined:

- LifePRO source extracts do **not** contain policy-level Premium Quote effective modal factors.
- All convertible premium data is already loaded (`MODE_PREMIUM` → `MMODEPREM`, PPBEN rates, quikplan factors).
- The memo duplicated quikplan information and provided no incremental business value.

**Rollback complete.** Converter quikmemo behavior restored to **v57.36 / Issue #21M-FU** baseline (PNOTE + PENSE merge only, 4,380 rows).

---

## 2. What Was Removed

| Removed item | Location |
|--------------|----------|
| `ISSUE21J_MODAL_FACTORS` constant | `qla_core/quikmemo_converter.py` |
| `format_conversion_modal_factor_memo()` | `qla_core/quikmemo_converter.py` |
| `_load_mplan_by_mpolicy()` | `qla_core/quikmemo_converter.py` |
| `_load_converted_memokeys()` | `qla_core/quikmemo_converter.py` |
| `_merge_conversion_segment()` | `qla_core/quikmemo_converter.py` |
| `append_issue21j_conversion_memos()` | `qla_core/quikmemo_converter.py` |
| quikmemo batch `#21J` append call + logging | `app.py`, `QLA_Migration/app.py` |
| RUN_GUIDE modal premium operational note | `QLA_Migration/RUN_GUIDE.md` |

See `Issue_21J_Files_Removed.md`.

---

## 3. What Was NOT Changed

- `PPOLC.MODE_PREMIUM` → `quikmstr.MMODEPREM` mapping
- `PPBEN.ANN_PREM_PER_UNIT` → `quikridr.MPREM` (#26)
- QUIKPLAN modal factors (ANNL/SEMI/QTRL/MTHD/MTHB rulebook defaults)
- Premium calculations, rating logic, rulebooks, crosswalks
- Issue #21M PNOTE/PENSE merge architecture

---

## 4. Regression Results

See `Issue_21J_Rollback_Regression_Results.md`.

| Metric | v57.37 (#21J) | v57.38 (rollback) | Expected |
|--------|---------------|-------------------|----------|
| quikmemo.csv rows | 5,083 | **4,380** | #21M baseline |
| `[CONVERSION]` segments | 5,083 | **0** | None |
| Unique MEMOKEY | 5,083 | **4,380** | = row count |
| quikmstr / quikridr / quikplan / quikclnt / quikprmh | unchanged | unchanged | PASS |
| 010713704C MMODEPREM | 43.91 | **43.91** | PASS |

---

## 5. Protected Issues

| Issue | Status at v57.38 |
|-------|------------------|
| #21M / #21M-FU | **PASS** — 4,380 rows; one per MEMOKEY; PNOTE/PENSE merge intact |
| #21K | **PASS** — no quikridr changes |
| #25 | **PASS** — MEMOKEY formatting unchanged |
| #26 | **PASS** — MPREM / MMODEPREM unchanged |
| #28 | **PASS** — no catalog/crosswalk changes |
| #21D | **PASS** — quikclnt/quikdvdp counts unchanged |

No #21M validator baseline update required (remains at 4,380).

---

## 6. Issue #21J Status

Issue #21J remains **AWAITING CLIENT** per tracking sheet. The original modal premium **display mismatch** (QLAdmin Coverage Detail vs LifePRO draft premium) is documented in `Issue_21J_Planning_Correction_Report.md` as **runtime/out-of-scope** for conversion — not resolved by memo or rollback.

---

## 7. Release Note

See `Issue_21J_Rollback_Release_Note.md`. v57.37 memo release note superseded.

---

**Rollback status:** ✅ COMPLETE — Validation not authorized until separately requested for v57.38 baseline.
