# Issue #55 — Implementation Notes

**Version:** v57.78  
**Date:** 2026-07-13  
**Stage:** Development (G4)

## Summary

Surgical post-map hook on `quikridr` emit:

1. **MUNIT floor:** if `0 < MUNIT < 0.001`, set to `0` (formatted `0.00000`).
2. **Leading-zero decimals:** all QUIKRIDR numeric decimal fields per Help layout emit with a leading digit (`0.53000`, not `.53000`). `MPREM` (#26) keeps its numeric string; only leading-dot prefix is fixed.

## Files changed

| File | Change |
|------|--------|
| `qla_core/quikridr_decimal_emit.py` | New — floor + format helpers |
| `app.py` | v57.78; call `apply_quikridr_decimal_emit` before quikridr row append (incl. PUA path) |
| `QLA_Migration/app.py` | Synced with root engine |
| `tools/validators/validate_issue55_munit_floor.py` | Fleet + trace validation |
| `QLA_Migration/_validate_issue55_munit_floor.py` | Thin wrapper |

## Hook placement

After all quikridr enrichments (`MPHDOB`, `MLASTANN`, PUA inheritance, MCV0) and **before** `output.append`.

## Before / after (trace policies)

| Policy | Phase | Before MUNIT | After MUNIT |
|--------|------:|-------------:|------------:|
| `018495BC` | 1 | `.00001` | `0.00000` |
| `018495BC` | 2 | `.53000` | `0.53000` |
| `018499CC` | 1 | `.00001` | `0.00000` |
| `018499CC` | 2 | `1.05000` | `1.05000` |
| `018510C` | 1 | `.00001` | `0.00000` |
| `018510C` | 2 | `.64700` | `0.64700` |
| `010434419C` | 2 | `.00009` | `0.00000` |

## Regression guards

- **#25 MPOLICY:** unchanged — `format_qladmin_mpolicy` still applied in rulebook loop.
- **#26 MPREM:** numeric value unchanged; `.00` → `0.00` only.
- **QLAdmin NFO/display:** not modified (out of scope).

## Validation

```bash
python QLA_Migration/_validate_issue55_munit_floor.py --simulate-only
python QLA_Migration/_validate_issue55_munit_floor.py --publish-test-validation
```

Re-run full batch via `run_converter.bat`, then run validator without `--simulate-only` for G5.

## Out of scope

- QLAdmin Edit Phase Units `3000` display (NFO×VPU / plan INITVAL).
- DBF Append Tool (user desktop v1.5 — separate fix).
