# Issue #51 — Implementation Notes

**Issue:** Missing Interest Table (A60MIR / A96DAR) — Projected Values crash loop  
**Engine version:** v57.76  
**Development agent:** Composer 2.5  
**Date:** 2026-07-11  

## Summary

Emitted exactly **2** QuikAint stub rows for closed MIR/DAR riders (`A60MIR`, `A96DAR`) at `MEFFDATE=19000101`, `MINTRATE/MINTRATE1=0.0000` per PPBEN `FV_GUAR_RATE=.00` authority. Wired into rate emit path; no QuikUint, quikridr, #21D, #25, or #26 changes.

## Files changed

| File | Change |
|------|--------|
| `qla_core/rate_dbf_schema.py` | Added `QuikAint` fields + `quikaint_fields()` helper (Help §7.31) |
| `qla_core/rate_dbf_writer.py` | Added `write_quikaint_table()` / `write_quikaint_csv()` |
| `qla_core/quikaint_closed_riders.py` | **New** — stub builder + `emit_issue51_quikaint()` |
| `qla_core/rate_emit.py` | Hook QuikAint emit on CSV/DBF rate package write |
| `plan_analysis/phase_r5_rate_loader/rate_loader_emit.py` | Mirror QuikAint emit for CLI rate loader |
| `app.py` | `APP_VERSION` v57.75 → v57.76 |
| `QLA_Migration/app.py` | `APP_VERSION` v57.75 → v57.76 |
| `tools/validators/validate_issue51_quikaint.py` | **New** — issue validator |
| `QLA_Migration/_validate_issue51_quikaint.py` | **New** — thin wrapper |
| `QLA_Migration/Output/rates/QuikAint.csv` | **Produced** — 2 stub rows |
| `QLA_Migration/Output/rates/rate_csv_manifest.csv` | Added QuikAint entry |
| `QLA_Migration/Output/Test_Validation/rates/QuikAint.csv` | Partial UAT publish |

## Before / after

| Artifact | Before | After |
|----------|--------|-------|
| `Output/rates/QuikAint.csv` | Absent | 2 rows (A60MIR, A96DAR @ 0%) |
| `rate_csv_manifest.csv` | No QuikAint | QuikAint listed (2 rows) |
| QuikUint | No MIR/DAR (unchanged) | Still no MIR/DAR |
| quikridr MIR/DAR rows | 6 × MPHSTAT=56 | Unchanged |

### QuikAint.csv contents

```
MPLAN,MEFFDATE,MINTRATE,MINTRATE1
A60MIR,19000101,0.0000,0.0000
A96DAR,19000101,0.0000,0.0000
```

## How to validate

```powershell
python tools/validators/validate_issue51_quikaint.py
python tools/validators/validate_issue51_quikaint.py --publish-test-validation
# or
python QLA_Migration/_validate_issue51_quikaint.py
```

Re-emit via rate loader (stubs always appended when CSV emit runs):

```powershell
python -c "from qla_core.quikaint_closed_riders import emit_issue51_quikaint; emit_issue51_quikaint('QLA_Migration/Output/rates')"
```

Or full rate emit from app GUI / `qla_core.rate_emit.run_rate_emit()`.

## Validator output (2026-07-11)

```
========================================================================
ISSUE #51 QUIKAINT VALIDATION (script v1.0, engine v57.76)
========================================================================
OK: QuikAint.csv found (2 row(s))
OK: A60MIR stub @ 19000101 / 0.0000 / 0.0000
OK: A96DAR stub @ 19000101 / 0.0000 / 0.0000
OK: QuikUint has no A60MIR/A96DAR rows
OK: quikridr regression — 6 rows, all MPHSTAT=56
OK: rate_csv_manifest.csv lists QuikAint
OK: published QuikAint.csv to QLA_Migration/Output/Test_Validation/rates
------------------------------------------------------------------------
RESULT: PASS
```

## Regression risks

- **Low:** Static 2-row append; no policy-table or premium logic touched.
- **Rate package:** Manifest gains one file; UAT must load `QuikAint.csv` with other rate tables.
- **Follow-on:** If UAT still loops after QuikAint load, Risk authorized QuikAing/QuikAinf stubs at same 0% rate.

## Ready for Validation Agent

**Yes** — validator PASS; `QuikAint.csv` in `Output/rates/` and `Test_Validation/rates/`.
