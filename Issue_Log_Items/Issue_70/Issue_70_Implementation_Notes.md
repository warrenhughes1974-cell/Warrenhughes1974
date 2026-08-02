# Issue #70 — Implementation Notes

## History — Interim emit (v57.89) — preserved

**Engine:** v57.89  
**Date:** 2026-07-14  
**Status then:** Interim emit complete — awaiting CSO Advance/Arrears confirmation  

| Item | Detail |
|------|--------|
| `qla_core/quikplan_converter.py` | Fleet-wide `_normalize_quikplan_loanintx`: invalid/missing → `A` on **all** plans (not only PLOAN-matched) |
| Rulebook | Unchanged — `LOANINTX` default `A`, `SKIP_TRANSLATION` (prevents `A→22` status mistranslation) |
| `app.py` / `QLA_Migration/app.py` | `APP_VERSION` → **v57.89** |

| File | LOANINTX |
|------|----------|
| `QLA_Migration/Output/quikplan.csv` | **141 / 141 = A** (interim) |

---

## Source-driven emit (v58.50) — Development 2026-08-02

**Engine:** v58.50  
**Status:** Development complete — ready for Validation Agent (re-batch Output required before Closure)  
**Authority:** CSO confirmed `PCOVR_Coverage_Extract_20260630.LOAN_ADV_ARREARS` is source of truth.

### Codebook

| `LOAN_ADV_ARREARS` | `LOANINTX` | Notes |
|--------------------|------------|-------|
| `0` | **A** | Advance |
| `N` | **A** | Advance family |
| `1` | **R** | Arrears |
| blank / unknown | **A** | Fail-safe + audit/trace (`blank_default` / `unknown_default`) |

### Changes

| Path | Change |
|------|--------|
| `qla_core/quikplan_converter.py` | `map_loan_adv_arrears_to_loanintx`; same-row map in `convert_quikplan_row`; rulebook path in `_map_field_value`; `_normalize_quikplan_loanintx` remains invalid→`A` safety net (**preserves `R`**) |
| `QLA_Migration/Configs/Sync_Rulebook_quikplan.csv` | `Source_Field=LOAN_ADV_ARREARS` for `LOANINTX`; **retain `SKIP_TRANSLATION`** |
| `app.py` + `QLA_Migration/app.py` | `APP_VERSION` → **v58.50**; batch log of A/R counts + fallback audit |
| `tools/validators/validate_issue70_loanintx.py` | Read-only Output validator (137 A / 4 R; SAL set) |
| `QLA_Migration/_validate_issue70_loanintx.py` | Thin wrapper |
| `Issue_Log_Items/Issue_70/test_issue70_loanintx_map.py` | Focused unit tests |

### Untouched (by design)

- QuikLoan `resolve_mloanintx` / #32 derivation (inherits plan values when applicable)
- Issue #104 settlement paths
- QuikPlan `LOANINT` PLOAN enrichment (rate only)
- QuikPlSt

### Expected Output after re-batch

| Metric | Count |
|--------|------:|
| `LOANINTX=A` | **137** |
| `LOANINTX=R` | **4** — `1SALOL`, `1SALML`, `1SALMI`, `9SLADB` |
| QuikLoan `MLOANINTX` flips today | **0** (no SAL PLOAN rows) |

### Before / after trace

| Plan | Before (interim) | After (source map) |
|------|------------------|--------------------|
| `1SALOL` | A | **R** |
| `1SALML` | A | **R** |
| `1SALMI` | A | **R** |
| `9SLADB` | A | **R** |
| `1960PO` | A | **A** |

### Validation commands

```text
python Issue_Log_Items/Issue_70/test_issue70_loanintx_map.py
python QLA_Migration/_validate_issue70_loanintx.py
```

Validator PASS on full Output requires re-batch with v58.50 (current Output still 141×A until re-emit).
