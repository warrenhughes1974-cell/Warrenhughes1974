# Issue #80 — Implementation Notes

**Completed:** 2026-07-17 (v58.01 validation-fix pass)  
**Version:** app.py / QLA_Migration/app.py **v58.01**  
**Authority:** `plan_analysis/source_data/rates/CSO_Valuation_Setup.csv` (51 non-PUA plans)

---

## Validation-fix pass (v58.01)

| Fix | Detail |
|-----|--------|
| QuikPlTv MORT blank rule | Removed QuikPlCv fallback in `field_value()` — blank authority stays blank |
| Overlay helper artifacts | Backup → `QLA_Migration/Archive/`; QA → `QLA_Migration/Reports/` |
| app.py QA path | `cso_valuation_setup_quikplan_qa.csv` → `QLA_Migration/Reports/` |
| Test_Validation | `--clean` publish; folder holds **only** quikplan + rates/QuikPlCv + rates/QuikPlTv + manifest |
| Validator | Schema order, package purity, absent keys for quikplan-only plans, PUA isolation, artifact guard, Test_Validation parity |

```powershell
python QLA_Migration/_validate_issue80_valuation_setup.py --publish-test-validation
```

**Result:** PASS (all G4 packaging checks included).

---

## Summary

CSO Valuation_Setup is now the authoritative source for plan/rate assumption fields on 51 in-scope QLA plans. Valuation_Setup **wins** over `CSO_Mortiality_Crosswalk.csv` for those plans. Blank workbook cells emit blank (assumption does not apply).

PUA plans and four missing-QLA PUA rows remain out of scope (#81 / #82).

---

## Code changes

| File | Change |
|------|--------|
| `qla_core/cso_valuation_setup.py` | **New** — loader, `ValuationSetupAssumptionProvider`, `CompositeAssumptionProvider`, quikplan overlay |
| `qla_core/rate_pipeline.py` | `load_assumptions()` accepts `cso_valuation_setup`; composite provider for QuikPlCv/Tv emit |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | Added `cso_valuation_setup` path |
| `app.py` / `QLA_Migration/app.py` | After CSO crosswalk, apply `apply_quikplan_valuation_setup()`; QA CSV `cso_valuation_setup_quikplan_qa.csv` |
| `QLA_Migration/_validate_issue80_valuation_setup.py` | **New** — compares Output to `cso_valuation_setup_coded_expected.csv` |
| `QLA_Migration/_apply_issue80_quikplan_overlay.py` | **New** — headless quikplan overlay helper (batch mirror) |

---

## Scope exceptions (locked)

| Plan(s) | Treatment |
|---------|-----------|
| `10L171`, `10L172`, `117JPO` | quikplan NFOINT/INTMETHCV only — **no** QuikPlCv/Tv keys (no factor grids) |
| PUA QLA plans (10) | Deferred to **#82** |
| PUA rows without QLA Plan (4) | Deferred to **#81** |
| `221END`, `222END` ETIMORT | **`N1`** (1941 CSO) per user lock |

---

## Validation

```powershell
python plan_governance/phase_r5_rate_loader_runner/rate_loader_gui_runner.py --emit-csv
python QLA_Migration/_apply_issue80_quikplan_overlay.py   # if quikplan not from full batch v58.00
python QLA_Migration/_validate_issue80_valuation_setup.py
```

**Result (2026-07-17):** PASS — 48 rate-key plans + 3 quikplan-only plans; QuikPlCv/Tv/quikplan match coded expected.

Rate emit: SUCCESS (partial emit; V-UINT-PDINT blocker ignored as before).

---

## Test_Validation publish

Partial UAT reload package:

- `Output/Test_Validation/quikplan.csv`
- `Output/Test_Validation/rates/QuikPlCv.csv`
- `Output/Test_Validation/rates/QuikPlTv.csv`

---

## Anchor spot checks (post-emit)

| Plan | QuikPlCv NFOINT | QuikPlTv RSVINT | ETIMORT |
|------|-----------------|-----------------|---------|
| `1960PO` | `6` | `6` | `Q1` |
| `221END` | `2` | `2` | `N1` |
| `1658C1` | `A` | `A` | `C1` |

---

## Regression notes

- Non–Valuation_Setup plans still use CSO mortality crosswalk fallback at rate emit and quikplan.
- No Citizens / CFIC folder changes.
- Next framework stage: **Validation** (Grok 4.5 read-only) on user request.
